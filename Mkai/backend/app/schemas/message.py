from pydantic import BaseModel, ConfigDict


class MessageCreate(BaseModel):
    content: str
    role: str = "user"
    conversation_id: int | None = None


class MessageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    content: str
    role: str
    conversation_id: int | None = None
    created_at: str
