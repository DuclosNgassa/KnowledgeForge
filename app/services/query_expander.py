from langchain_core.language_models import BaseChatModel
from langchain_core.messages import SystemMessage, HumanMessage
from pydantic import BaseModel, Field

from app.observability.logging import logger


class ExpandedQueries(BaseModel):
    queries: list[str] = Field(
        description=("Alternative search queries that preserve the original "
                     "question´s intent and constraints.")
    )


class QueryExpander:
    """Generate alternative retrieval queries for a user question."""

    def __init__(
            self,
            model: BaseChatModel,
            max_alternatives: int = 2,
    ) -> None:
        if max_alternatives < 0:
            raise ValueError("max_alternatives must be >= 0")
        self.model = model
        self.max_alternatives = max_alternatives

        self.structured_model = model.with_structured_output(ExpandedQueries)

    async def expand(self, query: str) -> list[str]:
        """Return original query plus unique alternatives."""
        query = query.strip()
        if not query or self.max_alternatives == 0:
            return [query] if query else []

        messages = [
            SystemMessage(
                content="You optimize queries for a document-based RAG system.\n"
                        f"Generate at most {self.max_alternatives} alternative "
                        "search queries for the user's question.\n"
                        "Use different wording, synonyms, or relevant domain "
                        "terminology to improve retrieval coverage.\n"
                        "Preserve the original intent, entities, and constraints.\n"
                        "Do not answer the question or introduce unsupported "
                        "assumptions.\n"
                        "Return alternatives only, not the original question."
            ),
            HumanMessage(content=query),
        ]

        try:
            response = await self.structured_model.ainvoke(messages)
        except Exception:
            logger.exception("Query expansion failed; using original query")
            return [query]

        queries = [query]
        seen = {query.casefold()}

        for candidate in response.queries:
            candidate = candidate.strip()
            if not candidate:
                continue

            normalized = candidate.casefold()

            if normalized in seen:
                continue

            seen.add(normalized)
            queries.append(candidate)

            if len(queries) > self.max_alternatives:
                break

        return queries
