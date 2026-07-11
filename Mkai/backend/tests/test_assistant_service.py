import asyncio

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.database import Base
from app.schemas.chat import ChatRequest
from app.services.assistant_service import AssistantService
from app.services.memory_service import MemoryService


def test_generate_reply_returns_expected_response() -> None:
    service = AssistantService()
    response = asyncio.run(service.generate_reply(ChatRequest(message="Merhaba MKAI")))

    assert response.model
    assert response.reply
    assert "Merhaba" in response.reply or "hello" in response.reply.lower()


def test_generate_reply_uses_memory_from_db_in_prompt(monkeypatch) -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()

    try:
        MemoryService(session).extract_and_store(
            "Benim adım Muhammed. Ben Java öğreniyorum.",
            user_id="muhammed",
            workspace="Naruto Mod",
        )

        captured: dict[str, object] = {}

        async def fake_generate(messages, *, provider=None, model=None):
            captured["messages"] = messages
            return {"text": "ok", "model": "test-model"}

        monkeypatch.setattr("app.services.assistant_service.provider_router.generate", fake_generate)

        service = AssistantService()
        response = asyncio.run(
            service.generate_reply(
                ChatRequest(message="Beni hatırla", user_id="muhammed", workspace="Naruto Mod"),
                db=session,
            )
        )

        assert response.reply == "ok"
        messages = captured["messages"]
        assert isinstance(messages, list)
        assert any("muhammed" in item["content"].lower() for item in messages if item["role"] == "system")
        assert any("java" in item["content"].lower() for item in messages if item["role"] == "system")
    finally:
        session.close()


def test_generate_reply_defaults_missing_user_id_for_memory_storage(monkeypatch) -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()

    try:
        captured: dict[str, object] = {}

        async def fake_generate(messages, *, provider=None, model=None):
            captured["messages"] = messages
            return {"text": "ok", "model": "test-model"}

        monkeypatch.setattr("app.services.assistant_service.provider_router.generate", fake_generate)

        service = AssistantService()
        response = asyncio.run(
            service.generate_reply(
                ChatRequest(message="Merhaba", user_id=None, workspace="Naruto Mod"),
                db=session,
            )
        )

        assert response.reply == "ok"
        memories = MemoryService(session).list_memories("anonymous")
        assert memories
        assert any(item.category == "note" for item in memories)
    finally:
        session.close()


def test_direct_route_bypasses_llm_for_simple_math(monkeypatch) -> None:
    async def fail_generate(*args, **kwargs):
        raise AssertionError("LLM should not be called for direct answers")

    monkeypatch.setattr("app.services.assistant_service.provider_router.generate", fail_generate)
    service = AssistantService()

    response = asyncio.run(service.generate_reply(ChatRequest(message="2+2")))

    assert "4" in response.reply
    assert response.model == "direct"


def test_memory_guard_skips_unrelated_memories(monkeypatch) -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()

    try:
        MemoryService(session).extract_and_store(
            "Benim favori rengim siyah. Favori oyunum Minecraft.",
            user_id="user-1",
            workspace="default",
        )

        captured: dict[str, object] = {}

        async def fake_generate(messages, *, provider=None, model=None):
            captured["messages"] = messages
            return {"text": "ok", "model": "test-model"}

        monkeypatch.setattr("app.services.assistant_service.provider_router.generate", fake_generate)

        service = AssistantService()
        response = asyncio.run(
            service.generate_reply(
                ChatRequest(message="Big Bang nedir?", user_id="user-1", workspace="default"),
                db=session,
            )
        )

        assert response.reply == "ok"
        messages = captured["messages"]
        combined = "\n".join(item["content"] for item in messages if item["role"] != "system")
        assert "siyah" not in combined.lower()
        assert "minecraft" not in combined.lower()
    finally:
        session.close()
