from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.database import Base
from app.services.core_brain_service import CoreBrainService
from app.services.memory_service import MemoryService


def test_core_brain_uses_profile_and_memory() -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()

    try:
        memory_service = MemoryService(session)
        memory_service.extract_and_store("Benim favori rengim siyah.", user_id="muhammed", workspace="Naruto Mod")
        memory_service.extract_and_store("Ben Java bilmiyorum.", user_id="muhammed", workspace="Naruto Mod")

        brain = CoreBrainService(session)
        context = brain.analyze("What is my favorite color?", user_id="muhammed", workspace="Naruto Mod")
        assert context.decision.needs_memory is True
        assert context.decision.needs_web_search is False
        assert context.profile.get("user_id") == "muhammed"
        assert context.memories

        prompt = brain.build_prompt(context, user_language="en")
        assert any("MKAI, your personal AI operating system and lifelong assistant" in item["content"] for item in prompt if item["role"] == "system")
    finally:
        session.close()
