from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

import config
from auth import create_token

router = APIRouter()


class LoginRequest(BaseModel):
    password: str


@router.post("/api/auth/login")
async def login(body: LoginRequest):
    if body.password != config.APP_PASSWORD:
        raise HTTPException(status_code=401, detail="Incorrect password")
    return {"token": create_token()}
