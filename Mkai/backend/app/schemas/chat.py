from typing import Any

from pydantic import BaseModel


class ChatRequest(BaseModel):
    message: str
    provider: str | None = None
    model: str | None = None
    history: list[dict[str, Any]] | None = None
    conversation_id: int | None = None
    user_id: str | None = None
    workspace: str | None = None
    debug: bool = False


class ChatResponse(BaseModel):
    reply: str
    model: str = "mkai-local"
