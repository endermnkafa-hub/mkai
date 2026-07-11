from __future__ import annotations

from typing import Any

import httpx

from app.core.config import settings
from app.providers.base import BaseProvider


class OllamaProvider(BaseProvider):
    name = "ollama"

    async def _list_models(self) -> list[str]:
        try:
            async with httpx.AsyncClient(timeout=20.0) as client:
                response = await client.get(f"{settings.ollama_base_url}/api/tags")
                response.raise_for_status()
                data = response.json()
            if isinstance(data, dict):
                models = data.get("models", [])
                return [m.get("name") for m in models if isinstance(m, dict) and m.get("name")]
            return []
        except Exception:
            return []

    async def generate(self, messages: list[dict[str, str]], *, model: str | None = None) -> dict[str, Any]:
        import sys
        print(f"[PROVIDER_DEBUG] settings.ollama_model={settings.ollama_model}", file=sys.stderr, flush=True)
        print(f"[PROVIDER_DEBUG] settings.default_model={settings.default_model}", file=sys.stderr, flush=True)
        print(f"[PROVIDER_DEBUG] model param={model}", file=sys.stderr, flush=True)

        endpoint = settings.ollama_base_url
        preferred_models = [model, settings.ollama_model, settings.default_model, "qwen2.5:3b", "llama3.2:3b"]
        selected_model = next((m for m in preferred_models if m), None)
        print(f"[PROVIDER_DEBUG] selected_model={selected_model}", file=sys.stderr, flush=True)

        available_models = await self._list_models()
        print(f"[PROVIDER_DEBUG] available_models={available_models}", file=sys.stderr, flush=True)
        if available_models:
            fallback_models = [m for m in preferred_models if m and m in available_models]
            if fallback_models:
                selected_model = fallback_models[0]
            elif selected_model not in available_models:
                selected_model = available_models[0]

        payload = {
            "model": selected_model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": 0.2,
                "top_p": 0.9,
                "repeat_penalty": 1.1,
                "num_ctx": 4096
            }
        }
        url = f"{endpoint}/api/chat"
        print(f"[PROVIDER] POST to {url}", file=sys.stderr, flush=True)
        print(f"[PROVIDER] Model: {selected_model}", file=sys.stderr, flush=True)
        print(f"[PROVIDER] Messages count: {len(messages)}", file=sys.stderr, flush=True)

        try:
            async with httpx.AsyncClient(timeout=600.0) as client:
                print(f"[PROVIDER] Client created, sending request...", file=sys.stderr, flush=True)
                response = await client.post(url, json=payload)
                print(f"[PROVIDER] Response status: {response.status_code}", file=sys.stderr, flush=True)
                response.raise_for_status()
                data = response.json()

            if isinstance(data, dict):
                text = data.get("message", {}).get("content", "") or data.get("response", "")
            else:
                text = str(data)
            return {"text": text, "model": selected_model}
        except Exception as exc:
            print(f"[PROVIDER] Exception: {type(exc).__name__}: {exc}", file=sys.stderr, flush=True)
            raise RuntimeError(f"Ollama provider error: {exc}") from exc
