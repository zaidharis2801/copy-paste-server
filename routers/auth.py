import re

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, field_validator
from supabase import AsyncClient

from auth import create_token, get_current_user_id, hash_password, verify_password
from database import get_supabase

router = APIRouter()

_USERNAME_RE = re.compile(r"^[a-zA-Z0-9_]{3,32}$")


class AuthRequest(BaseModel):
    username: str
    password: str

    @field_validator("username")
    @classmethod
    def validate_username(cls, v: str) -> str:
        v = v.strip()
        if not _USERNAME_RE.match(v):
            raise ValueError(
                "Username must be 3–32 characters: letters, numbers, underscore only"
            )
        return v

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if len(v) < 6:
            raise ValueError("Password must be at least 6 characters")
        return v


@router.post("/api/auth/signup", status_code=201)
async def signup(body: AuthRequest, supabase: AsyncClient = Depends(get_supabase)):
    res = await supabase.table("users").select("id").ilike("username", body.username).execute()
    if res.data:
        raise HTTPException(status_code=409, detail="Username already taken")

    insert_res = await supabase.table("users").insert({
        "username": body.username,
        "password_hash": hash_password(body.password)
    }).execute()

    if not insert_res.data:
        raise HTTPException(status_code=500, detail="Failed to create user")

    user_id = insert_res.data[0]["id"]
    return {
        "token": create_token(user_id, body.username),
        "username": body.username,
    }


@router.post("/api/auth/login")
async def login(body: AuthRequest, supabase: AsyncClient = Depends(get_supabase)):
    res = await supabase.table("users").select("id, username, password_hash").ilike("username", body.username).execute()
    if not res.data:
        raise HTTPException(status_code=401, detail="Invalid username or password")

    row = res.data[0]
    if not verify_password(body.password, row["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid username or password")

    return {
        "token": create_token(row["id"], row["username"]),
        "username": row["username"],
    }


@router.get("/api/auth/me")
async def me(
    user_id: int = Depends(get_current_user_id),
    supabase: AsyncClient = Depends(get_supabase),
):
    res = await supabase.table("users").select("id, username, created_at").eq("id", user_id).execute()
    if not res.data:
        raise HTTPException(status_code=401, detail="User not found")
    return res.data[0]

