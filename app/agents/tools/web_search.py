from langchain_core.tools import tool
from langchain_tavily import TavilySearch

from app.core.settings import settings
from app.schemas.search_result import WebSearchResult
from app.observability.langfuse import langfuse


def create_web_search_tool():
    tavily = TavilySearch(
        max_result=5,
        topic="general",
        tavily_api_key=settings.tavily_api_key,
    )

    @tool
    async def web_search(query: str) -> list[WebSearchResult]:
        """Search the web for current or external information.

        Use this tool when the user´s question requires information
        that is not available in their stored documents

        Do not use this tool when the answer can be obtained from the
        user's stored documents.

        Use this tool for current information, external research,
        recent events, websites, public information, or topics that
        are not covered by user´s documents.
        """
        with langfuse.start_as_current_observation(
                as_type="retriever",
                name="web_search",
                input={
                    "query": query,
                },
        ) as observation:
            response = await tavily.ainvoke(
                {
                    "query": query,
                }
            )

            web_search_results = [
                WebSearchResult(
                    title=result["title"],
                    url=result["url"],
                    content=result["content"]
                )
                for result in response["results"]
            ]

            observation.update(
                output={
                    "result_count": len(web_search_results),
                }
            )
            return web_search_results

    return web_search
