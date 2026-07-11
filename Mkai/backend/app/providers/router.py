from __future__ import annotations

from typing import Any

from app.core.config import settings
from app.providers.ollama_provider import OllamaProvider
from app.providers.openai_provider import OpenAIProvider


class ProviderRouter:
    def __init__(self) -> None:
        self._providers = {
            "ollama": OllamaProvider(),
            "openai": OpenAIProvider(),
        }

    async def generate(
        self,
        messages: list[dict[str, str]],
        *,
        provider: str | None = None,
        model: str | None = None,
    ) -> dict[str, Any]:
        selected_provider = (provider or settings.default_provider or "ollama").lower()
        if selected_provider not in self._providers:
            raise ValueError(f"Unsupported provider: {selected_provider}")
        return await self._providers[selected_provider].generate(messages, model=model)


router = ProviderRouter()
