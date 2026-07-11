from typing import Any

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.assistant_service import AssistantService
from app.services.memory_service import MemoryService

router = APIRouter()
assistant_service = AssistantService()


async def _handle_chat(request: ChatRequest, db: Session, *, stream: bool = False) -> Any:
    if stream:
        return await assistant_service.generate_reply(request, history=[], db=db)
    return await assistant_service.generate_reply(request, history=[], db=db)


@router.post("", response_model=ChatResponse)
async def chat(request: ChatRequest, db: Session = Depends(get_db)) -> ChatResponse:
    return await _handle_chat(request, db, stream=False)


@router.post("/stream")
async def chat_stream(request: ChatRequest, db: Session = Depends(get_db)) -> StreamingResponse:
    return await _handle_chat(request, db, stream=True)


@router.get("/memory-inspector")
def memory_inspector(user_id: str = "muhammed", workspace: str | None = None, db: Session = Depends(get_db)) -> dict[str, Any]:
    return MemoryService(db).get_inspector_data(user_id, workspace=workspace)
