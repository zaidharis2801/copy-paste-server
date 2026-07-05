import asyncio
import os
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse

import config
from auth import get_current_user_id
from database import init_db
from events import broadcaster
from routers import auth as auth_router
from routers import files as files_router
from routers import text as text_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(title="ClipSync", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router.router)
app.include_router(text_router.router)
app.include_router(files_router.router)


@app.get("/api/events")
async def sse_events(user_id: int = Depends(get_current_user_id)):
    """SSE stream scoped to the signed-in user."""
    queue = await broadcaster.subscribe(user_id)

    async def generate():
        try:
            yield 'data: {"type":"connected"}\n\n'
            while True:
                try:
                    msg = await asyncio.wait_for(queue.get(), timeout=25)
                    yield msg
                except asyncio.TimeoutError:
                    yield ": keepalive\n\n"
        except (GeneratorExit, asyncio.CancelledError):
            pass
        finally:
            broadcaster.unsubscribe(user_id, queue)

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )


@app.get("/")
async def serve_frontend():
    return FileResponse("static/index.html")
