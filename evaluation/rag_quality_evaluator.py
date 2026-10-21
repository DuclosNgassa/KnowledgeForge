import nest_asyncio
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

_original_apply = nest_asyncio.apply

try:
    # RAGAS 0.3.1 calls nest_asyncio.apply() while importing
    # ragas.executor. Prevent that import-time side effect.
    nest_asyncio.apply = lambda *args, **kwargs: None

    from ragas import SingleTurnSample
    from ragas.embeddings import embedding_factory
    from ragas.llms import llm_factory
    from ragas.metrics import AnswerRelevancy, Faithfulness

finally:
    # Restore nest_asyncio for any other code that uses it.
    nest_asyncio.apply = _original_apply

from app.core.settings import settings


class RagQualityEvaluator:
    def __init__(self):
        evaluator_llm = llm_factory(
            model=settings.openai_chat_model,
        )

        evaluator_embeddings = embedding_factory(
            model=settings.openai_embedding_model,
        )

        self.faithfulness = Faithfulness(llm=evaluator_llm)
        self.answer_relevancy = AnswerRelevancy(
            llm=evaluator_llm,
            embeddings=evaluator_embeddings,
        )

        self.abstention_judge = ChatOpenAI(
            model=settings.openai_chat_model,
            api_key=settings.openai_api_key,
            temperature=0,
        ).with_structured_output(AbstentionEvaluation)

    async def evaluate(
            self,
            question: str,
            answer: str,
            contexts: list[str]
    ) -> dict[str, float]:
        sample = SingleTurnSample(
            user_input=question,
            response=answer,
            retrieved_contexts=contexts,
        )

        faithfulness_result = await self.faithfulness.single_turn_ascore(
            sample
        )

        relevancy_result = await self.answer_relevancy.single_turn_ascore(
            sample
        )

        return {
            "faithfulness": float(faithfulness_result),
            "answer_relevancy": float(relevancy_result),
        }

    async def evaluate_unanswerable(
            self,
            question: str,
            answer: str,
            contexts: list[str],
    ) -> dict[str, float]:
        prompt = f"""
    You are evaluating a RAG system's handling of an unanswerable question.

    The question is known to be unanswerable from the available knowledge base.

    Question:
    {question}

    Retrieved contexts:
    {contexts}

    Generated answer:
    {answer}

    Score the answer using this rubric:
    - 1.0: Clearly acknowledges insufficient information and does not
      present unsupported claims as facts.
    - 0.5: Ambiguous refusal or partially answers with some unsupported claims.
    - 0.0: Gives a confident answer unsupported by the available contexts.

    A concise statement that the information could not be found is acceptable.
    Do not penalize a correct refusal for not answering the question directly.
    """

        result = await self.abstention_judge.ainvoke(prompt)

        return {
            "abstention_correctness": float(result.score),
        }


class AbstentionEvaluation(BaseModel):
    score: float = Field(
        ge=0.0,
        le=1.0,
        description=(
            "1.0 if the answer correctly abstains without unsupported claims; "
            "0.5 if the response is ambiguous or partially answers without "
            "adequate support; 0.0 if it confidently gives an unsupported answer."
        ),
    )
    reason: str = Field(description="Brief explanation for the score")
