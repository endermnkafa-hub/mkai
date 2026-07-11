from collections.abc import Generator

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import settings


class Base(DeclarativeBase):
    pass


engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False} if settings.database_url.startswith("sqlite") else {},
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db() -> None:
    from app.models.conversation import Conversation  # noqa: F401
    from app.models.message import Message  # noqa: F401
    from app.services.memory_service import MemoryRecord  # noqa: F401

    Base.metadata.create_all(bind=engine)
    _ensure_message_conversation_id_column()


def _ensure_message_conversation_id_column() -> None:
    inspector = inspect(engine)
    if "messages" not in inspector.get_table_names():
        return

    columns = {column["name"] for column in inspector.get_columns("messages")}
    if "conversation_id" not in columns:
        with engine.begin() as connection:
            connection.execute(text("ALTER TABLE messages ADD COLUMN conversation_id INTEGER"))


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
