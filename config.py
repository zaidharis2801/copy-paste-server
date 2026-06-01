import os
from dotenv import load_dotenv

load_dotenv()

APP_PASSWORD: str = os.getenv("APP_PASSWORD", "changeme")
SECRET_KEY: str   = os.getenv("SECRET_KEY", "change-this-to-a-long-random-secret")
MAX_FILE_MB: int  = int(os.getenv("MAX_FILE_MB", "50"))
UPLOAD_DIR: str   = os.getenv("UPLOAD_DIR", "uploads")
DB_PATH: str      = os.getenv("DB_PATH", "clipboard.db")
