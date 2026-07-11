import os
from datetime import datetime, timedelta, timezone
from typing import Any

import jwt

from app.core.config import settings


class AuthService:
    def __init__(self) -> None:
        self.secret_key = settings.secret_key

    def create_token(self, subject: str) -> str:
        now = datetime.now(timezone.utc)
        payload = {"sub": subject, "iat": now, "exp": now + timedelta(hours=24)}
        return jwt.encode(payload, self.secret_key, algorithm="HS256")

    def verify_token(self, token: str) -> dict[str, Any]:
        return jwt.decode(token, self.secret_key, algorithms=["HS256"])
