import re
from dataclasses import dataclass
from uuid import UUID

from app.schemas.agent_response import SourceReference, WebSource
from app.schemas.retrieved_document import RetrievedDocument
from app.schemas.search_result import WebSearchResult


@dataclass(frozen=True)
class CitationSource:
    """A source that can be referenced in a generated answer."""
    citation_id: str
    source_type: str
    content: str
    document_id: UUID | None = None
    chunk_id: UUID | None = None
    filename: str | None = None
    page_number: int | None = None
    title: str | None = None
    url: str | None = None


@dataclass
class CitationRegistry:
    sources: dict[str, CitationSource]

    def get(self, citation_id: str) -> CitationSource | None:
        return self.sources.get(citation_id)

    def document_sources(self) -> list[SourceReference]:
        """Return the retrieved document sources for the API response."""
        result = []
        for source in self.sources.values():
            if source.source_type != "document":
                continue

            if source.document_id is None or source.filename is None:
                continue

            result.append(
                SourceReference(
                    citation_id=source.citation_id,
                    chunk_id=source.chunk_id,
                    document_id=source.document_id,
                    filename=source.filename,
                    page_number=source.page_number,
                    content=source.content,
                )
            )

        return result

    def web_sources(self) -> list[WebSource]:
        """Return the retrieved web sources for the API response."""
        result = []
        for source in self.sources.values():
            if source.source_type != "web":
                continue

            if source.title is None or source.url is None:
                continue

            result.append(
                WebSource(
                    citation_id=source.citation_id,
                    url=source.url,
                    title=source.title,
                )
            )

        return result


class CitationService:
    """Build and validate citation references for generated answers."""

    CITATION_PATTERN = re.compile(r"\[((?:D|W)\d+(?:\s*,\s*(?:D|W)\d+)*)\]")

    def build_registry(self,
                       documents: list[RetrievedDocument],
                       web_results: list[WebSearchResult]) -> CitationRegistry:

        sources: dict[str, CitationSource] = {}

        for index, document in enumerate(documents, start=1):
            citation_id = f"D{index}"
            sources[citation_id] = CitationSource(
                citation_id=citation_id,
                source_type="document",
                content=document.content,
                document_id=UUID(document.document_id),
                chunk_id=UUID(document.chunk_id),
                filename=document.filename,
                page_number=document.page_number,
            )

        for index, web_result in enumerate(web_results, start=1):
            citation_id = f"W{index}"
            sources[citation_id] = CitationSource(
                citation_id=citation_id,
                source_type="web",
                title=web_result.title,
                url=web_result.url,
                content=web_result.content,
            )

        return CitationRegistry(sources)

    def extract_citations(self, answer: str) -> list[str]:
        """Return unique citation labels in order of appearance."""
        citations: list[str] = []

        for match in self.CITATION_PATTERN.finditer(answer):
            citations.extend(
                citation.strip()
                for citation in match.group(1).split(",")
            )

        return citations

    def validate_citations(self, answer: str, registry: CitationRegistry) -> list[str]:
        """Return citation labels that do not exist in the registry."""
        return [
            citation_id
            for citation_id in self.extract_citations(answer)
            if registry.get(citation_id) is None
        ]

    def build_contexts(
            self,
            registry: CitationRegistry,
    ) -> tuple[str, str]:
        """Build document and web contexts with stable citation labels."""

        document_blocks: list[str] = []
        web_blocks: list[str] = []

        for source in registry.sources.values():
            if source.source_type == "document":
                document_blocks.append(
                    f"[{source.citation_id}]\n"
                    f"Source: {source.filename}\n"
                    f"Document ID: {source.document_id}\n"
                    f"Chunk ID: {source.chunk_id}\n"
                    f"Page: {source.page_number}\n"
                    f"Content:\n{source.content}"
                )

            elif source.source_type == "web":
                web_blocks.append(
                    f"[{source.citation_id}]\n"
                    f"Title: {source.title}\n"
                    f"URL: {source.url}\n"
                    f"Content:\n{source.content}"
                )

        document_context = "\n\n---\n\n".join(document_blocks)
        web_context = "\n\n---\n\n".join(web_blocks)

        return document_context, web_context
