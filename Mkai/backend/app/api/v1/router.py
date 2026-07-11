from fastapi import APIRouter

from app.api.v1.endpoints.auth import router as auth_router
from app.api.v1.endpoints.chat import router as chat_router
from app.api.v1.endpoints.conversations import router as conversations_router
from app.api.v1.endpoints.health import router as health_router
from app.api.v1.endpoints.memories import router as memories_router
from app.api.v1.endpoints.messages import router as messages_router
from app.api.v1.endpoints.providers import router as providers_router
from app.api.v1.endpoints.upload import router as upload_router

api_router = APIRouter()
api_router.include_router(health_router, prefix="/health", tags=["health"])
api_router.include_router(auth_router, prefix="/auth", tags=["auth"])
api_router.include_router(chat_router, prefix="/chat", tags=["chat"])
api_router.include_router(conversations_router, prefix="/conversations", tags=["conversations"])
api_router.include_router(messages_router, prefix="/messages", tags=["messages"])
api_router.include_router(memories_router, prefix="/memories", tags=["memories"])
api_router.include_router(providers_router, prefix="/providers", tags=["providers"])
api_router.include_router(upload_router, prefix="/upload", tags=["upload"])
