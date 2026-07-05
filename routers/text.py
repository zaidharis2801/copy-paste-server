from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from supabase import AsyncClient

from auth import get_current_user_id
from database import get_supabase
from events import broadcaster

router = APIRouter()


class TextCreate(BaseModel):
    content: str


@router.get("/api/text")
async def get_texts(
    limit: int = 50,
    user_id: int = Depends(get_current_user_id),
    supabase: AsyncClient = Depends(get_supabase),
):
    res = await supabase.table("text_entries").select("id, content, created_at").eq("user_id", user_id).order("id", desc=True).limit(limit).execute()
    return res.data


@router.post("/api/text", status_code=201)
async def create_text(
    body: TextCreate,
    user_id: int = Depends(get_current_user_id),
    supabase: AsyncClient = Depends(get_supabase),
):
    if not body.content.strip():
        raise HTTPException(status_code=400, detail="Content cannot be empty")

    insert_res = await supabase.table("text_entries").insert({
        "user_id": user_id,
        "content": body.content
    }).execute()

    if not insert_res.data:
        raise HTTPException(status_code=500, detail="Failed to save text entry")

    entry = insert_res.data[0]
    await broadcaster.broadcast(user_id, "new_text", entry)
    return entry

