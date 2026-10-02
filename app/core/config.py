from pathlib import Path
import os 
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(PROJECT_ROOT / ".env")

LLM_API_KEY = os.getenv("LLM_API_KEY")
DATABASE_URL = os.getenv("DATABASE_URL")

MAX_FILE_SIZE_MB = os.getenv("MAX_FILE_SIZE_MB")
TOTAL_FILE_SIZE_MB = os.getenv("TOTAL_FILE_SIZE_MB")
DAILY_SUMMARY_LIMIT = os.getenv("DAILY_SUMMARY_LIMIT")
MAX_TRANSCRIPT_CHARS = os.getenv("MAX_TRANSCRIPT_CHARS")
RATE_LIMIT_PER_MINUTE = os.getenv("RATE_LIMIT_PER_MINUTE")

CORS_ORIGINS = [
    origin.strip()
    for origin in os.getenv(
        "CORS_ORIGINS",
        "http://localhost:3000"
    ).split(",")
    if origin.strip()
]
