from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Message(Base):
    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    content: Mapped[str] = mapped_column(String(4000), nullable=False)
    role: Mapped[str] = mapped_column(String(20), nullable=False)
    conversation_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    created_at: Mapped[str] = mapped_column(String(100), nullable=False)
