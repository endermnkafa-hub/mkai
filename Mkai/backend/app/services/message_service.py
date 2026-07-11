from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.message import Message
from app.schemas.message import MessageCreate, MessageOut


class MessageService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create_message(self, payload: MessageCreate) -> MessageOut:
        message = Message(
            content=payload.content,
            role=payload.role,
            conversation_id=payload.conversation_id,
            created_at=datetime.now(timezone.utc).isoformat(),
        )
        self.db.add(message)
        self.db.commit()
        self.db.refresh(message)
        return MessageOut.model_validate(message)

    def list_messages(self) -> list[MessageOut]:
        messages = self.db.query(Message).order_by(Message.id.asc()).all()
        return [MessageOut.model_validate(message) for message in messages]

    def list_messages_for_conversation(self, conversation_id: int) -> list[MessageOut]:
        messages = self.db.query(Message).filter(Message.conversation_id == conversation_id).order_by(Message.id.asc()).all()
        return [MessageOut.model_validate(message) for message in messages]
