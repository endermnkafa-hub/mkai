import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.providers.ollama_provider import OllamaProvider


@pytest.mark.asyncio
async def test_provider_falls_back_to_available_model_when_requested_model_is_missing():
    provider = OllamaProvider()
    result = await provider.generate([
        {"role": "user", "content": "Reply with one short word: ok"}
    ], model="qwen2.5:14b")

    assert isinstance(result, dict)
    assert result["text"].strip()
    assert result["model"] in {"qwen2.5:14b", "qwen2.5:3b", "llama3.2:3b"}
