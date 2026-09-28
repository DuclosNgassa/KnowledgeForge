from langfuse import Langfuse

from app.core.settings import settings
from langfuse.langchain import CallbackHandler

langfuse = Langfuse(
    public_key=settings.langfuse_public_key,
    secret_key=settings.langfuse_secret_key,
    base_url=settings.langfuse_base_url,
)

langfuse_handler = CallbackHandler()
