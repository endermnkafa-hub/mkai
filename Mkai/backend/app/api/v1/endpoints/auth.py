from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.services.auth_service import AuthService

router = APIRouter()


class AuthRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


@router.post("/token", response_model=TokenResponse)
def login(payload: AuthRequest) -> TokenResponse:
    if payload.username == "admin" and payload.password == "password":
        token = AuthService().create_token(payload.username)
        return TokenResponse(access_token=token)
    raise HTTPException(status_code=401, detail="Invalid credentials")
