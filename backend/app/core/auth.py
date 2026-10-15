"""Admin HTTP Basic authentication dependency."""
from __future__ import annotations

import secrets
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials

from app.core.config import get_settings

security = HTTPBasic()
settings = get_settings()


def require_admin(credentials: Annotated[HTTPBasicCredentials, Depends(security)]) -> str:
    valid_user = secrets.compare_digest(credentials.username.encode(), settings.ADMIN_USERNAME.encode())
    valid_pass = secrets.compare_digest(credentials.password.encode(), settings.ADMIN_PASSWORD.encode())
    if not (valid_user and valid_pass):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid admin credentials.",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username
