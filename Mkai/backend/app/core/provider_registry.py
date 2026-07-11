from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class ProviderConfig:
    name: str
    api_key_env: str
    enabled: bool = True


class ProviderRegistry:
    def __init__(self) -> None:
        self.providers: dict[str, ProviderConfig] = {
            "openai": ProviderConfig(name="openai", api_key_env="OPENAI_API_KEY"),
            "claude": ProviderConfig(name="claude", api_key_env="CLAUDE_API_KEY"),
            "gemini": ProviderConfig(name="gemini", api_key_env="GEMINI_API_KEY"),
            "deepseek": ProviderConfig(name="deepseek", api_key_env="DEEPSEEK_API_KEY"),
            "ollama": ProviderConfig(name="ollama", api_key_env="OLLAMA_API_KEY", enabled=False),
            "openrouter": ProviderConfig(name="openrouter", api_key_env="OPENROUTER_API_KEY"),
            "huggingface": ProviderConfig(name="huggingface", api_key_env="HUGGINGFACE_API_KEY"),
        }

    def list_enabled(self) -> list[str]:
        return [name for name, config in self.providers.items() if config.enabled]

    def get(self, name: str) -> ProviderConfig:
        return self.providers[name]


registry = ProviderRegistry()
