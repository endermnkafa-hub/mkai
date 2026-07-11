from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.message import MessageCreate, MessageOut
from app.services.message_service import MessageService

router = APIRouter()


@router.post("", response_model=MessageOut)
def create_message(payload: MessageCreate, db: Session = Depends(get_db)) -> MessageOut:
    return MessageService(db).create_message(payload)


@router.get("", response_model=list[MessageOut])
def list_messages(db: Session = Depends(get_db)) -> list[MessageOut]:
    return MessageService(db).list_messages()
