import os
from typing import Any

from app.core.provider_registry import registry


class ProviderService:
    def __init__(self) -> None:
        self.registry = registry

    def get_provider_status(self) -> dict[str, dict[str, Any]]:
        return {
            name: {
                "enabled": config.enabled,
                "api_key_configured": bool(os.getenv(config.api_key_env)),
            }
            for name, config in self.registry.providers.items()
        }
