import json

from langchain_core.language_models import BaseChatModel
from langchain_core.prompts import ChatPromptTemplate

from app.schemas.document_comparison import (
    ComparisonCriterion,
    DocumentComparisonResponse,
)


class DocumentComparisonAgent:

    def __init__(self, model: BaseChatModel):
        self.model = model

        self.prompt = ChatPromptTemplate.from_messages([
            (
                "system",
                """
You are an expert document comparison assistant.

Your task is to compare multiple documents using ONLY the
summaries and structured extraction data provided to you.

SOURCE RESTRICTIONS:

1. Use exclusively the provided summaries and structured extractions.
2. Never assume information that is not explicitly present.
3. Never invent facts, technologies, entities, or topics.
4. Do not use external knowledge or external sources.
5. Do not reconstruct or summarize the original documents.
6. Do not interpret missing information as evidence that something
   is absent from a document.

COMPARISON RULES:

1. Focus exclusively on the requested comparison criteria.
2. Clearly distinguish similarities from differences.
3. Compare only information that is supported by the input data.
4. Do not claim that a topic, technology, or entity is unique to
   one document merely because it is missing from another document's
   extraction.
5. When information is insufficient, explicitly explain the limitation.
6. Keep all insights concise, factual, and meaningful.
7. Use document titles in human-readable findings.
8. Use document IDs exactly as provided in the input.
9. Distinguish between:
   - Explicitly stated information.
   - Information that can reasonably be inferred from the provided
     summaries and structured extractions.
   - Information that cannot be determined.

   Only use explicitly stated information for factual comparisons.
   Do not present reasonable inferences as established facts.

COMPARISON CRITERIA:

- key_topics:
  Compare the main subjects, themes, and topics covered by the documents.

- technologies:
  Compare programming languages, frameworks, platforms, tools,
  and other technologies explicitly identified in the documents.

- named_entities:
  Compare people, organizations, products, and other named entities
  identified in the documents.

OUTPUT REQUIREMENTS:

Return exactly one criterion result for every requested criterion.

For every criterion result:

- criterion:
  The requested criterion being analyzed.

- similarities:
  List meaningful similarities supported by the available data.
  If no similarities can be established, explain that.

- differences:
  List meaningful differences supported by the available data.
  Do not interpret missing extraction data as a confirmed difference.

- document_insights:
  Return exactly one entry for every input document.
  Each entry must contain the corresponding document_id,
  document_title, and criterion-specific insights.
  If there is insufficient information for a document,
  explicitly state that in its insights.

OVERVIEW:

Summarize the most important findings across all requested criteria.
Do not introduce findings that are not supported by the criterion results.

CONCLUSION:

Provide a concise overall assessment of the comparison.
Mention important similarities, differences, and limitations
where relevant.

Do not include information unrelated to the requested criteria.
"""
            ),
            (
                "human",
                """
Compare the following documents.

Requested comparison criteria:
{criteria}

Document summaries and structured extractions:
{documents}
"""
            ),
        ])

        self.structured_model = self.model.with_structured_output(
            DocumentComparisonResponse
        )

        self.chain = self.prompt | self.structured_model

    async def compare(
            self,
            documents: list[dict],
            criteria: list[ComparisonCriterion],
    ) -> DocumentComparisonResponse:

        self._validate_inputs(documents, criteria)

        document_data = [
            {
                "document_id": str(document["document_id"]),
                "document_title": document["document_title"],
                "summary": document["summary"],
                "extraction": document["extraction"],
            }
            for document in documents
        ]

        response = await self.chain.ainvoke({
            "criteria": ", ".join(
                criterion.value for criterion in criteria
            ),
            "documents": json.dumps(
                document_data,
                ensure_ascii=False,
                separators=(",", ":"),
            ),
        })

        return self._validate_response(
            response=response,
            documents=documents,
            criteria=criteria,
        )

    @staticmethod
    def _validate_inputs(
            documents: list[dict],
            criteria: list[ComparisonCriterion],
    ) -> None:

        if len(documents) < 2:
            raise ValueError(
                "At least two documents are required for comparison."
            )

        document_ids = [
            document["document_id"]
            for document in documents
        ]

        if len(document_ids) != len(set(document_ids)):
            raise ValueError(
                "Document IDs must be unique."
            )

        if not criteria:
            raise ValueError(
                "At least one comparison criterion is required."
            )

        if len(criteria) != len(set(criteria)):
            raise ValueError(
                "Comparison criteria must be unique."
            )

        for document in documents:
            if not document.get("summary"):
                raise ValueError(
                    f"Document {document['document_id']} "
                    "has no summary."
                )

            if document.get("extraction") is None:
                raise ValueError(
                    f"Document {document['document_id']} "
                    "has no structured extraction."
                )

            if not document.get("document_id"):
                raise ValueError("Every document must have an ID.")

            if not document.get("document_title"):
                document["document_title"] = "Untitled document"

            if not isinstance(document.get("summary"), str):
                raise ValueError(
                    f"Document {document['document_id']} has an invalid summary."
                )

    @staticmethod
    def _validate_response(
            response: DocumentComparisonResponse,
            documents: list[dict],
            criteria: list[ComparisonCriterion],
    ) -> DocumentComparisonResponse:

        if not response.overview.strip():
            raise ValueError("The comparison overview is empty.")

        if not response.conclusion.strip():
            raise ValueError("The comparison conclusion is empty.")

        for result in response.criterion_results:
            if not result.similarities:
                result.similarities = [
                    "No similarities could be established from the available data."
                ]

            if not result.differences:
                result.differences = [
                    "No differences could be established from the available data."
                ]

        returned_criteria = [
            result.criterion
            for result in response.criterion_results
        ]

        # Every requested criterion must appear exactly once.
        if len(returned_criteria) != len(set(returned_criteria)):
            raise ValueError(
                "The comparison response contains duplicate criteria."
            )

        expected_criteria = set(criteria)
        if set(returned_criteria) != expected_criteria:
            raise ValueError(
                "The comparison response does not contain exactly "
                "the requested criteria."
            )

        expected_documents = {
            document["document_id"]: document["document_title"]
            for document in documents
        }

        validated_results = []

        for criterion in criteria:
            result = next(
                item
                for item in response.criterion_results
                if item.criterion == criterion
            )

            returned_document_ids = [
                insight.document_id
                for insight in result.document_insights
            ]

            # Every document must have exactly one insight.
            if len(returned_document_ids) != len(set(returned_document_ids)):
                raise ValueError(
                    f"Criterion '{criterion.value}' contains duplicate "
                    "document insights."
                )

            if set(returned_document_ids) != set(expected_documents):
                raise ValueError(
                    f"Criterion '{criterion.value}' does not contain "
                    "exactly one insight for every input document."
                )

            # Restore the original document order and verify titles.
            insights_by_id = {
                insight.document_id: insight
                for insight in result.document_insights
            }

            ordered_insights = []

            for document_id, document_title in expected_documents.items():
                insight = insights_by_id[document_id]

                if insight.document_title != document_title:
                    raise ValueError(
                        f"Incorrect document title for document "
                        f"{document_id} in criterion '{criterion.value}'."
                    )

                ordered_insights.append(insight)

            validated_results.append(
                result.model_copy(
                    update={
                        "document_insights": ordered_insights,
                    }
                )
            )

        return response.model_copy(
            update={
                "criterion_results": validated_results,
            }
        )
