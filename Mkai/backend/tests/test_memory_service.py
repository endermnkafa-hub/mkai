from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.database import Base
from app.services.memory_service import MemoryService


def test_memory_service_extracts_learning_and_temporary_memories() -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()

    try:
        service = MemoryService(session)

        service.extract_and_store(
            "Ben bugün Java öğrenmeye başladım.",
            user_id="muhammed",
            workspace="Naruto Mod",
        )
        service.extract_and_store(
            "Bugün canım sıkkın.",
            user_id="muhammed",
            workspace="Naruto Mod",
        )
        service.extract_and_store(
            "Benim adım Muhammed.",
            user_id="muhammed",
            workspace="Naruto Mod",
        )

        memories = service.list_memories("muhammed")
        assert any(item.category == "learning" and item.value == "Java" for item in memories)
        assert any(item.memory_type == "temporary" and item.category == "mood" for item in memories)
        assert any(item.category == "identity" and "Muhammed" in item.value for item in memories)

        inspector = service.get_inspector_data("muhammed", workspace="Naruto Mod")
        assert inspector["workspace"] == "Naruto Mod"
        assert inspector["profile"]["user_id"] == "muhammed"
        assert inspector["recent_memories"]
    finally:
        session.close()
