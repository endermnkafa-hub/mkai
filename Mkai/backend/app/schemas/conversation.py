from pydantic import BaseModel, ConfigDict


class ConversationCreate(BaseModel):
    title: str


class ConversationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    created_at: str
