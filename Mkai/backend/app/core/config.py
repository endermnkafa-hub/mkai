from functools import lru_cache

from pydantic import ConfigDict, Field, field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    model_config = ConfigDict(env_file=".env", case_sensitive=False, extra="ignore")

    app_env: str = Field(default="development", alias="APP_ENV")
    api_host: str = Field(default="127.0.0.1", alias="API_HOST")
    api_port: int = Field(default=8000, alias="API_PORT")
    cors_origins: str = Field(default="http://localhost:3000,http://localhost:3001,http://127.0.0.1:3000,http://127.0.0.1:3001", alias="CORS_ORIGINS")
    database_url: str = Field(default="sqlite:///./mkai.db", alias="DATABASE_URL")
    secret_key: str = Field(default="change-me-in-production", alias="SECRET_KEY")
    rate_limit_per_minute: int = Field(default=120, alias="RATE_LIMIT_PER_MINUTE")
    max_upload_size_mb: int = Field(default=20, alias="MAX_UPLOAD_SIZE_MB")
    default_provider: str = Field(default="ollama", alias="DEFAULT_PROVIDER")
    default_model: str = Field(default="qwen2.5:3b", alias="DEFAULT_MODEL")
    ollama_base_url: str = Field(default="http://127.0.0.1:11434", alias="OLLAMA_BASE_URL")
    ollama_model: str = Field(default="qwen2.5:3b", alias="OLLAMA_MODEL")
    openai_model: str = Field(default="gpt-4o-mini", alias="OPENAI_MODEL")

    @field_validator("cors_origins", mode="before")
    @classmethod
    def validate_cors_origins(cls, value: object) -> object:
        if isinstance(value, list | tuple):
            return ",".join(str(item).strip() for item in value if str(item).strip())
        return value

    @property
    def cors_origin_list(self) -> list[str]:
        if isinstance(self.cors_origins, str):
            return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]
        return [origin.strip() for origin in self.cors_origins if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
