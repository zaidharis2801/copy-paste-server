import os
from dotenv import load_dotenv

load_dotenv()

SECRET_KEY: str = os.getenv("SECRET_KEY", "change-this-to-a-long-random-secret")
MAX_FILE_MB: int = int(os.getenv("MAX_FILE_MB", "50"))

SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY: str = os.getenv("SUPABASE_KEY", "")
SUPABASE_BUCKET: str = os.getenv("SUPABASE_BUCKET", "clipboard")
