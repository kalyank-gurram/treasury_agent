from pydantic_settings import BaseSettings
from pydantic import Field
import os

class Settings(BaseSettings):
    openai_api_key: str | None = Field(default=None, alias="OPENAI_API_KEY")
    anthropic_api_key: str | None = Field(default=None, alias="ANTHROPIC_API_KEY")
    model_provider: str = Field(default="openai", alias="MODEL_PROVIDER")
    primary_model: str = Field(default="gpt-4.1-mini", alias="PRIMARY_MODEL")
    cheap_model: str = Field(default="gpt-4o-mini", alias="CHEAP_MODEL")
    anthropic_primary: str = Field(default="claude-3-5-sonnet-latest", alias="ANTHROPIC_PRIMARY")
    anthropic_cheap: str = Field(default="claude-3-5-haiku-latest", alias="ANTHROPIC_CHEAP")

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()
if settings.openai_api_key and "OPENAI_API_KEY" not in os.environ:
    os.environ["OPENAI_API_KEY"] = settings.openai_api_key
if settings.anthropic_api_key and "ANTHROPIC_API_KEY" not in os.environ:
    os.environ["ANTHROPIC_API_KEY"] = settings.anthropic_api_key