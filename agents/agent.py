from uuid import UUID

from deepagents import create_deep_agent
from langchain.agents.structured_output import ToolStrategy

from agents.tools.document_content import create_get_document_content_tool
from agents.tools.document_search import create_search_documents_tool
from agents.tools.document import create_get_document_metadata_tool
from agents.tools.web_search import create_web_search_tool
from core.settings import settings
from schemas.agent_response import AgentResponse


def create_agent(
        search_service,
        document_service,
        user_id
):
    search_documents = create_search_documents_tool(
        search_service,
        user_id
    )

    get_document_metadata = create_get_document_metadata_tool(
        document_service=document_service,
        user_id=user_id,
    )

    get_document_content = create_get_document_content_tool(
        document_service=document_service,
        user_id=user_id,
    )

    web_search = create_web_search_tool()

    return create_deep_agent(
        model="google_genai:" + settings.google_chat_model,
        tools=[
            search_documents,
            get_document_metadata,
            get_document_content,
            web_search,
        ],
        response_format=ToolStrategy(AgentResponse),
        system_prompt="""
You are the KnowledgeForge research assistant.

You have access to the user's stored documents and web.

TOOL SELECTION:

1. Use search_documents when the user´s question may be answered 
using their stored documents.

2. Use get_document_metadata when you need metadata about a specific document.

3. Use get_document_content when you need to read the content 
of a specific document.

4. Use web_search when:
    - the information is not available in the user´s documents
    - the user explicitly ask for web research
    - current or recently changed information is required
    - external sources are needed
    
When answering a question about the user's documents:

1. ALWAYS call search_documents first.
2. Use only information returned by that tool.
3. The search tool returns documents containing:
   - document_id
   - chunk_id
   - filename
   - page_number
   - content

4. After using search_documents, ALWAYS populate the
   `sources` field of AgentResponse.

5. For every source used in your answer, copy:
   document_id
   chunk_id
   filename
   content
   page_number

   exactly from the search result.

6. NEVER invent document IDs, chunk IDs, filenames or
   page numbers.

7. If search_documents returns no results, return:
   sources=[]

8. Your final response must conform to AgentResponse.

Do not invent information.

When using web_search, base your answer on the returned
search results.
""",
    )
