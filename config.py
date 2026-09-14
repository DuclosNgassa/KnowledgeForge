from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    DATABASE_URL:str
    JWT_SECRET_KEY:str
    JWT_ALGORITHM:str
    REFRESH_TOKEN_EXPIRATION: int
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: str = ""

    model_config=SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )

Config=Settings()
