from app.core.database import Base, engine
from app.schemas.conversation import ConversationCreate
from app.services.conversation_service import ConversationService
from sqlalchemy.orm import Session


def test_create_and_list_conversation() -> None:
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    with Session(engine) as db:
        service = ConversationService(db)
        conversation = service.create_conversation(ConversationCreate(title="Test chat"))
        items = service.list_conversations()

    assert conversation.title == "Test chat"
    assert len(items) == 1
