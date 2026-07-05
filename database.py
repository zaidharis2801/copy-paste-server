import config
from supabase import acreate_client, AsyncClient

_client: AsyncClient = None

async def init_db() -> None:
    global _client
    if _client is None:
        if not config.SUPABASE_URL or not config.SUPABASE_KEY:
            raise RuntimeError("SUPABASE_URL and SUPABASE_KEY must be set in environment variables.")
        _client = await acreate_client(config.SUPABASE_URL, config.SUPABASE_KEY)

async def get_supabase() -> AsyncClient:
    global _client
    if _client is None:
        await init_db()
    return _client
