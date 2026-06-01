import os
import re
import uuid

import aiosqlite
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import FileResponse

import config
from auth import verify_token
from database import get_db
from events import broadcaster

router = APIRouter()


def _sanitize(name: str) -> str:
    name = os.path.basename(name or "upload")
    name = re.sub(r"[^\w.\- ]", "_", name)
    return (name[:200].strip()) or "unnamed"


@router.get("/api/files")
async def get_files(
    _token: str = Depends(verify_token),
    db: aiosqlite.Connection = Depends(get_db),
):
    cur = await db.execute(
        "SELECT id, original_name, size_bytes, created_at FROM file_entries ORDER BY id DESC"
    )
    rows = await cur.fetchall()
    return [dict(r) for r in rows]


@router.post("/api/files/upload", status_code=201)
async def upload_file(
    file: UploadFile = File(...),
    _token: str = Depends(verify_token),
    db: aiosqlite.Connection = Depends(get_db),
):
    max_bytes = config.MAX_FILE_MB * 1024 * 1024
    content = await file.read()

    if len(content) > max_bytes:
        raise HTTPException(
            status_code=413,
            detail=f"File exceeds {config.MAX_FILE_MB} MB limit",
        )
    if len(content) == 0:
        raise HTTPException(status_code=400, detail="Empty file")

    original_name = _sanitize(file.filename)
    stored_name   = f"{uuid.uuid4().hex}_{original_name}"
    file_path     = os.path.join(config.UPLOAD_DIR, stored_name)

    with open(file_path, "wb") as fh:
        fh.write(content)

    cur = await db.execute(
        """INSERT INTO file_entries (original_name, stored_name, file_path, size_bytes)
           VALUES (?, ?, ?, ?)""",
        (original_name, stored_name, file_path, len(content)),
    )
    await db.commit()

    cur = await db.execute(
        "SELECT id, original_name, size_bytes, created_at FROM file_entries WHERE id = ?",
        (cur.lastrowid,),
    )
    entry = dict(await cur.fetchone())
    await broadcaster.broadcast("new_file", entry)
    return entry


@router.get("/api/files/{file_id}/download")
async def download_file(
    file_id: int,
    _token: str = Depends(verify_token),
    db: aiosqlite.Connection = Depends(get_db),
):
    cur = await db.execute(
        "SELECT original_name, file_path FROM file_entries WHERE id = ?",
        (file_id,),
    )
    row = await cur.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="File not found")
    if not os.path.exists(row["file_path"]):
        raise HTTPException(status_code=404, detail="File data missing on disk")

    return FileResponse(
        path=row["file_path"],
        filename=row["original_name"],
        media_type="application/octet-stream",
    )
