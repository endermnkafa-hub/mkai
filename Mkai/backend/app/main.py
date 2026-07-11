from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.database import init_db
from app.core.exceptions import AppError, app_exception_handler, validation_exception_handler
from app.core.middleware import LoggingMiddleware

app = FastAPI(title="MKAI", version="1.0.0", description="Production-grade AI assistant platform")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(LoggingMiddleware)

app.include_router(api_router, prefix="/api/v1")
app.add_exception_handler(AppError, app_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)


@app.on_event("startup")
def startup_event() -> None:
    init_db()


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok", "service": "backend"}
