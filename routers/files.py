import re
import uuid

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from supabase import AsyncClient

import config
from auth import get_current_user_id
from database import get_supabase
from events import broadcaster

router = APIRouter()


class SignedUrlRequest(BaseModel):
    filename: str


class FileMetadataRequest(BaseModel):
    original_name: str
    stored_name: str
    size_bytes: int


def _sanitize(name: str) -> str:
    # Remove directory components and sanitize string
    import os
    name = os.path.basename(name or "upload")
    name = re.sub(r"[^\w.\- ]", "_", name)
    return (name[:200].strip()) or "unnamed"


@router.get("/api/files")
async def get_files(
    user_id: int = Depends(get_current_user_id),
    supabase: AsyncClient = Depends(get_supabase),
):
    res = await supabase.table("file_entries").select("id, original_name, size_bytes, created_at").eq("user_id", user_id).order("id", desc=True).execute()
    return res.data


@router.post("/api/files/signed-upload-url")
async def get_signed_upload_url(
    body: SignedUrlRequest,
    user_id: int = Depends(get_current_user_id),
    supabase: AsyncClient = Depends(get_supabase),
):
    original_name = _sanitize(body.filename)
    stored_name = f"{uuid.uuid4().hex}_{original_name}"
    path = f"{user_id}/{stored_name}"

    try:
        # Create signed upload URL in Supabase storage bucket
        # Returns a dict containing e.g. {"signedUrl": "..."} or similar
        res = await supabase.storage.from_(config.SUPABASE_BUCKET).create_signed_upload_url(path)
        if not res or "signedUrl" not in res:
            raise HTTPException(status_code=500, detail="Failed to generate upload URL from storage provider")
        
        return {
            "signed_url": res["signedUrl"],
            "stored_name": stored_name,
            "original_name": original_name
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Storage error: {str(e)}")


@router.post("/api/files/upload-metadata", status_code=201)
async def upload_metadata(
    body: FileMetadataRequest,
    user_id: int = Depends(get_current_user_id),
    supabase: AsyncClient = Depends(get_supabase),
):
    file_path = f"{user_id}/{body.stored_name}"

    insert_res = await supabase.table("file_entries").insert({
        "user_id": user_id,
        "original_name": body.original_name,
        "stored_name": body.stored_name,
        "file_path": file_path,
        "size_bytes": body.size_bytes
    }).execute()

    if not insert_res.data:
        raise HTTPException(status_code=500, detail="Failed to save file metadata")

    entry = insert_res.data[0]
    # Format metadata back into dict that matches what frontend expects (excluding foreign key and file_path if not needed, but index.html uses id, original_name, size_bytes, created_at)
    await broadcaster.broadcast(user_id, "new_file", entry)
    return entry


@router.get("/api/files/{file_id}/download")
async def download_file(
    file_id: int,
    user_id: int = Depends(get_current_user_id),
    supabase: AsyncClient = Depends(get_supabase),
):
    res = await supabase.table("file_entries").select("original_name, stored_name").eq("id", file_id).eq("user_id", user_id).execute()
    if not res.data:
        raise HTTPException(status_code=404, detail="File not found")

    row = res.data[0]
    path = f"{user_id}/{row['stored_name']}"

    try:
        # Create a signed download URL (valid for 60 seconds)
        download_res = await supabase.storage.from_(config.SUPABASE_BUCKET).create_signed_url(path, expires_in=60)
        if not download_res or "signedURL" not in download_res:
            # Note: in some versions of Supabase storage, key might be 'signedUrl' (lowercase l)
            signed_url = download_res.get("signedURL") or download_res.get("signedUrl")
            if not signed_url:
                raise HTTPException(status_code=500, detail="Failed to generate download link")
        else:
            signed_url = download_res["signedURL"]

        return RedirectResponse(url=signed_url)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Storage error: {str(e)}")
