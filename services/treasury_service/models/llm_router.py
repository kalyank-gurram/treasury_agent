from __future__ import annotations
from typing import Literal
from ..config import settings
from langchain.chat_models import init_chat_model

Provider = Literal["openai", "anthropic", "hybrid"]

class LLMRouter:
    def __init__(self, provider: Provider | None = None):
        self.provider: Provider = provider or settings.model_provider  # type: ignore

    def cheap(self):
        if self.provider == "anthropic":
            return init_chat_model(settings.anthropic_cheap, model_provider="anthropic")
        return init_chat_model(settings.cheap_model, model_provider="openai")

    def primary(self):
        if self.provider == "anthropic":
            return init_chat_model(settings.anthropic_primary, model_provider="anthropic")
        return init_chat_model(settings.primary_model, model_provider="openai")