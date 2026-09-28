from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str
    jwt_secret_key: str
    jwt_algorithm: str
    refresh_token_expiration: int
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0
    redis_password: str = ""
    openai_api_key: str
    openai_embedding_model: str = "text-embedding-3-small"
    openai_chat_model: str = "gpt-4o-mini"
    google_embedding_model: str = "gemini-embedding-001"
    google_api_key: str
    google_chat_model: str = "gemini-3.6-flash"
    user_agent: str = "KnowledgeForge/1.0"
    tavily_api_key: str
    cohere_api_key: str
    cohere_rerank_model: str = "rerank-v3.5"
    langfuse_public_key: str
    langfuse_secret_key: str
    langfuse_base_url: str = "https://cloud.langfuse.com"
    langfuse_tracing_environment: str = "development"

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
        env_file_encoding="utf-8",
    )


settings = Settings()
