from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.conversation import Conversation
from app.schemas.conversation import ConversationCreate, ConversationOut


class ConversationService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create_conversation(self, payload: ConversationCreate) -> ConversationOut:
        conversation = Conversation(title=payload.title, created_at=datetime.now(timezone.utc).isoformat())
        self.db.add(conversation)
        self.db.commit()
        self.db.refresh(conversation)
        return ConversationOut.model_validate(conversation)

    def list_conversations(self) -> list[ConversationOut]:
        conversations = self.db.query(Conversation).order_by(Conversation.id.desc()).all()
        return [ConversationOut.model_validate(item) for item in conversations]
