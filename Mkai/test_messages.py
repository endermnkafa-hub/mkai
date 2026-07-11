import sys
sys.path.insert(0, 'backend')

import asyncio
from app.core.config import settings
from app.services.prompt_builder import PromptBuilder
from app.providers.ollama_provider import OllamaProvider

async def test():
    prompt_builder = PromptBuilder()
    messages = prompt_builder.build_messages('test', history=[], user_language='en')
    
    print(f"Message count: {len(messages)}")
    for i, msg in enumerate(messages):
        print(f"Message {i}: role={msg.get('role')}, content_length={len(msg.get('content', ''))}")
    
    provider = OllamaProvider()
    try:
        result = await provider.generate(messages)
        print(f"Provider result: {result.get('text', '')[:200]}")
    except Exception as e:
        print(f"Provider error: {e}")

asyncio.run(test())
