from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

import aiosqlite

from auth import verify_token
from database import get_db
from events import broadcaster

router = APIRouter()


class TextCreate(BaseModel):
    content: str


@router.get("/api/text")
async def get_texts(
    limit: int = 50,
    _token: str = Depends(verify_token),
    db: aiosqlite.Connection = Depends(get_db),
):
    cur = await db.execute(
        "SELECT id, content, created_at FROM text_entries ORDER BY id DESC LIMIT ?",
        (limit,),
    )
    rows = await cur.fetchall()
    return [dict(r) for r in rows]


@router.post("/api/text", status_code=201)
async def create_text(
    body: TextCreate,
    _token: str = Depends(verify_token),
    db: aiosqlite.Connection = Depends(get_db),
):
    if not body.content.strip():
        raise HTTPException(status_code=400, detail="Content cannot be empty")

    cur = await db.execute(
        "INSERT INTO text_entries (content) VALUES (?)",
        (body.content,),
    )
    await db.commit()

    cur = await db.execute(
        "SELECT id, content, created_at FROM text_entries WHERE id = ?",
        (cur.lastrowid,),
    )
    entry = dict(await cur.fetchone())
    await broadcaster.broadcast("new_text", entry)
    return entry
