from dataclasses import dataclass, field

from app.schemas.search_result import WebSearchResult


@dataclass
class WebSearchCollector:
    results: dict[str, WebSearchResult] = field(default_factory=dict)

    def add(self, results: list[WebSearchResult]) -> None:
        for result in results:
            # Deduplicate repeated URLs across multiple searches.
            self.results[result.url] = result

    def get_results(self) -> list[WebSearchResult]:
        return list(self.results.values())
