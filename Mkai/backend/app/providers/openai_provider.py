from __future__ import annotations

import os
from typing import Any

import httpx

from app.core.config import settings
from app.providers.base import BaseProvider


class OpenAIProvider(BaseProvider):
    name = "openai"

    async def generate(self, messages: list[dict[str, str]], *, model: str | None = None) -> dict[str, Any]:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY is not configured")
        payload = {
            "model": model or settings.openai_model or "gpt-4o-mini",
            "messages": messages,
        }
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        async with httpx.AsyncClient(timeout=180.0) as client:
            response = await client.post("https://api.openai.com/v1/chat/completions", json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()
        text = data["choices"][0]["message"]["content"]
        return {"text": text, "model": payload["model"]}
