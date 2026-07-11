from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.conversation import ConversationCreate, ConversationOut
from app.services.conversation_service import ConversationService

router = APIRouter()


@router.post("", response_model=ConversationOut)
def create_conversation(payload: ConversationCreate, db: Session = Depends(get_db)) -> ConversationOut:
    return ConversationService(db).create_conversation(payload)


@router.get("", response_model=list[ConversationOut])
def list_conversations(db: Session = Depends(get_db)) -> list[ConversationOut]:
    return ConversationService(db).list_conversations()
