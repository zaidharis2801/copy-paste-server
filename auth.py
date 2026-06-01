from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import Depends, HTTPException, Query
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt

import config

_ALGORITHM = "HS256"
_TOKEN_TTL = timedelta(hours=24)

_bearer = HTTPBearer(auto_error=False)


def create_token() -> str:
    expire = datetime.now(timezone.utc) + _TOKEN_TTL
    return jwt.encode({"exp": expire, "sub": "user"}, config.SECRET_KEY, algorithm=_ALGORITHM)


def _decode(token: str) -> None:
    try:
        jwt.decode(token, config.SECRET_KEY, algorithms=[_ALGORITHM])
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")


async def verify_token(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(_bearer),
    token: Optional[str] = Query(None),
) -> str:
    """FastAPI dependency: accepts Bearer header OR ?token= query param."""
    raw = credentials.credentials if credentials else token
    if not raw:
        raise HTTPException(status_code=401, detail="Authentication required")
    _decode(raw)
    return raw
