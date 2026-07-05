from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import Depends, HTTPException, Query
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
import bcrypt

import config

_ALGORITHM = "HS256"
_TOKEN_TTL = timedelta(hours=24)

_http_bearer = HTTPBearer(auto_error=False)


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode(), hashed.encode())


def create_token(user_id: int, username: str) -> str:
    expire = datetime.now(timezone.utc) + _TOKEN_TTL
    return jwt.encode(
        {"exp": expire, "sub": str(user_id), "username": username},
        config.SECRET_KEY,
        algorithm=_ALGORITHM,
    )


def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, config.SECRET_KEY, algorithms=[_ALGORITHM])
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")


async def get_current_user_id(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(_http_bearer),
    token: Optional[str] = Query(None),
) -> int:
    """Accepts Bearer header OR ?token= query param; returns authenticated user id."""
    raw = credentials.credentials if credentials else token
    if not raw:
        raise HTTPException(status_code=401, detail="Authentication required")
    payload = decode_token(raw)
    try:
        return int(payload["sub"])
    except (KeyError, TypeError, ValueError):
        raise HTTPException(status_code=401, detail="Invalid token payload")


async def get_current_username(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(_http_bearer),
    token: Optional[str] = Query(None),
) -> str:
    raw = credentials.credentials if credentials else token
    if not raw:
        raise HTTPException(status_code=401, detail="Authentication required")
    payload = decode_token(raw)
    username = payload.get("username")
    if not username:
        raise HTTPException(status_code=401, detail="Invalid token payload")
    return username
