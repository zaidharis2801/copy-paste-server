import aiosqlite
import config

_CREATE_TEXT_TABLE = """
CREATE TABLE IF NOT EXISTS text_entries (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    content    TEXT    NOT NULL,
    created_at TEXT    NOT NULL
                       DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now'))
)
"""

_CREATE_FILE_TABLE = """
CREATE TABLE IF NOT EXISTS file_entries (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    original_name TEXT    NOT NULL,
    stored_name   TEXT    NOT NULL,
    file_path     TEXT    NOT NULL,
    size_bytes    INTEGER NOT NULL,
    created_at    TEXT    NOT NULL
                          DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now'))
)
"""


async def init_db() -> None:
    async with aiosqlite.connect(config.DB_PATH) as db:
        await db.execute(_CREATE_TEXT_TABLE)
        await db.execute(_CREATE_FILE_TABLE)
        await db.commit()


async def get_db():
    db = await aiosqlite.connect(config.DB_PATH)
    db.row_factory = aiosqlite.Row
    try:
        yield db
    finally:
        await db.close()
