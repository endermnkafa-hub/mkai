from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class BaseProvider(ABC):
    name: str

    @abstractmethod
    async def generate(self, messages: list[dict[str, str]], *, model: str | None = None) -> dict[str, Any]:
        raise NotImplementedError
