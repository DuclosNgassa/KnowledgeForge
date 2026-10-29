import json
import math
import time
from collections import defaultdict
from datetime import datetime

from sqlalchemy import select
from langchain_ollama import ChatOllama
from dotenv import load_dotenv
import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(PROJECT_ROOT / ".env")
print("DATABASE_URL configured:", bool(os.getenv("DATABASE_URL")))
print("OPENAI_API_KEY configured:", bool(os.getenv("OPENAI_API_KEY")))
from evaluation.dataset import DATASET, EvaluationSample
import asyncio

print("asyncio.run module:", asyncio.run.__module__)
print("asyncio.run function:", asyncio.run)
from evaluation.rag_quality_evaluator import RagQualityEvaluator

# Adjust these imports to your actual project paths.
from app.models.document_chunk import DocumentChunk

from app.core.db.database import AsyncSessionLocal

MODELS = [
    ("ollama", "qwen3:4b"),
    ("ollama", "llama3.2:3b"),
]

OUTPUT_DIR = Path("evaluation/comparison/results")


def create_model(provider: str, model_name: str):
    if provider == "ollama":
        return ChatOllama(model=model_name, temperature=0)

    raise ValueError(f"Unsupported provider: {provider}")


async def load_contexts(sample: EvaluationSample) -> list[str]:
    """Load the sample's relevant chunk text from PostgreSQL."""
    relevant_chunks = sample["relevant_chunks"]

    if not relevant_chunks:
        return []

    chunk_ids = [chunk["chunk_id"] for chunk in relevant_chunks]

    async with AsyncSessionLocal() as session:
        stmt = select(DocumentChunk).where(
            DocumentChunk.id.in_(chunk_ids)
        )
        db_chunks = (await session.scalars(stmt)).all()

    chunks_by_id = {str(chunk.id): chunk for chunk in db_chunks}
    contexts = []

    # Preserve the order defined by the evaluation dataset.
    for relevant in relevant_chunks:
        chunk = chunks_by_id.get(relevant["chunk_id"])

        if chunk is None:
            raise ValueError(
                f"Chunk {relevant['chunk_id']} not found "
                f"for sample {sample['id']}"
            )

        # Protect against accidentally mismatched document/chunk IDs.
        if str(chunk.document_id) != relevant["document_id"]:
            raise ValueError(
                f"Document ID mismatch for chunk {relevant['chunk_id']}. "
                f"chunk: {chunk}. "
                f"relevant: {relevant}"
            )

        contexts.append(
            f"[D{len(contexts) + 1}] "
            f"Document: {chunk.document_id}, "
            f"Page: {chunk.page_number}\n"
            f"{chunk.content}"
        )

    return contexts


def build_prompt(question: str, contexts: list[str]) -> str:
    return f"""You are a question-answering assistant.

Answer the question using only the supplied context.
Answer briefly in 1-2 sentences.
Cite sources using their citation IDs, such as [D1].
If the context does not contain the answer, clearly say so.
Do not invent facts or citations.

Context:
{"".join(context + chr(10) + chr(10) for context in contexts)}

Question:
{question}

Answer:
"""


async def compare_model(
        provider: str,
        model_name: str,
        sample: EvaluationSample,
        contexts: list[str],
        evaluator: RagQualityEvaluator,
) -> dict:
    result = {
        "sample_id": sample["id"],
        "provider": provider,
        "model_name": model_name,
        "question": sample["question"],
        "expected_answer": sample["expected_answer"],
        "question_type": sample["question_type"],
        "difficulty": sample["difficulty"],
        "answerable": sample["answerable"],
        "relevant_chunks": sample["relevant_chunks"],
        "context_count": len(contexts),
        "answer": None,
        "generation_latency_seconds": None,
        "evaluation_latency_seconds": None,
        "scores": {},
        "error": None,
        "evaluation_error": None,
    }

    model = create_model(provider, model_name)
    prompt = build_prompt(sample["question"], contexts)

    started = time.perf_counter()

    try:
        response = await model.ainvoke(prompt)
        content = response.content

        if isinstance(content, str):
            answer = content.strip()
        elif isinstance(content, list):
            answer = "\n".join(
                str(item.get("text", ""))
                for item in content
                if isinstance(item, dict)
            ).strip()
        else:
            answer = str(content).strip()

        result["answer"] = answer

    except Exception as exc:
        result["error"] = f"{type(exc).__name__}: {exc}"

    result["generation_latency_seconds"] = round(
        time.perf_counter() - started, 3
    )

    if result["error"] or not result["answer"]:
        if not result["error"]:
            result["error"] = "Empty answer returned by model"
        return result

    evaluation_started = time.perf_counter()

    try:
        if sample["answerable"]:
            scores = await evaluator.evaluate(
                question=sample["question"],
                answer=result["answer"],
                contexts=contexts,
                expected_answer=sample["expected_answer"],
            )
        else:
            scores = await evaluator.evaluate_unanswerable(
                question=sample["question"],
                answer=result["answer"],
                contexts=contexts,
            )

        result["scores"] = scores

    except Exception as exc:
        result["evaluation_error"] = (
            f"{type(exc).__name__}: {exc}"
        )

    result["evaluation_latency_seconds"] = round(
        time.perf_counter() - evaluation_started, 3
    )

    return result


def aggregate_results(results: list[dict]) -> dict:
    metric_values = defaultdict(list)
    latencies = []

    for result in results:
        latency = result["generation_latency_seconds"]
        if latency is not None:
            latencies.append(latency)

        for metric, value in result["scores"].items():
            if (
                    isinstance(value, (int, float))
                    and math.isfinite(value)
            ):
                metric_values[metric].append(float(value))

    return {
        "sample_count": len(results),
        "generation_error_count": sum(
            r["error"] is not None for r in results
        ),
        "evaluation_error_count": sum(
            r["evaluation_error"] is not None for r in results
        ),
        "average_generation_latency_seconds": (
            round(sum(latencies) / len(latencies), 3)
            if latencies else None
        ),
        "average_scores": {
            metric: round(sum(values) / len(values), 4)
            for metric, values in metric_values.items()
            if values
        },
    }


def group_results(results: list[dict], field: str) -> dict:
    groups = defaultdict(list)

    for result in results:
        groups[result[field]].append(result)

    return {
        key: aggregate_results(group)
        for key, group in sorted(groups.items())
    }


async def main():
    if not DATASET:
        raise ValueError("DATASET is empty")

    evaluator = RagQualityEvaluator(
        citation_grounding_service=None
    )

    # Load contexts once so every model gets exactly the same text.
    contexts_by_sample = {}

    for sample in DATASET:
        contexts = await load_contexts(sample)

        if not contexts and sample["answerable"]:
            raise ValueError(
                f"No context found for answerable sample {sample['id']}"
            )

        contexts_by_sample[sample["id"]] = contexts

    results_by_model = {}

    # Run models sequentially to limit RAM usage.
    for provider, model_name in MODELS:
        print(f"\nEvaluating {model_name}...")
        model_results = []

        for index, sample in enumerate(DATASET, start=1):
            result = await compare_model(
                provider=provider,
                model_name=model_name,
                sample=sample,
                contexts=contexts_by_sample[sample["id"]],
                evaluator=evaluator,
            )
            model_results.append(result)

            print(
                f"[{index}/{len(DATASET)}] {sample['id']}: "
                f"{result['scores'] or result['error'] or result['evaluation_error']}"
            )

        results_by_model[model_name] = model_results

    report = {
        "created_at": datetime.now().astimezone().isoformat(),
        "dataset_source": "evaluation.dataset.DATASET",
        "sample_count": len(DATASET),
        "models": results_by_model,
        "summary": {
            model_name: {
                "overall": aggregate_results(model_results),
                "by_question_type": group_results(
                    model_results, "question_type"
                ),
                "by_difficulty": group_results(
                    model_results, "difficulty"
                ),
            }
            for model_name, model_results in results_by_model.items()
        },
    }

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = OUTPUT_DIR / f"rag_quality_{timestamp}.json"

    output_file.write_text(
        json.dumps(report, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    print(f"\nResults saved to {output_file}")


if __name__ == "__main__":
    asyncio.run(main())
