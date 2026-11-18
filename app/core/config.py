from pathlib import Path
import os 
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(PROJECT_ROOT / ".env")

LLM_API_KEY = os.getenv("LLM_API_KEY")
DATABASE_URL = os.getenv("DATABASE_URL")
JWT_SECRET = os.getenv("JWT_SECRET")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM")

MAX_FILE_SIZE_MB = os.getenv("MAX_FILE_SIZE_MB")
TOTAL_FILE_SIZE_MB = os.getenv("TOTAL_FILE_SIZE_MB")
TOTAL_SUMMARY_LIMIT = os.getenv("TOTAL_SUMMARY_LIMIT")

CORS_ORIGINS = [
    origin.strip()
    for origin in os.getenv(
        "CORS_ORIGINS",
        "http://localhost:3000"
    ).split(",")
    if origin.strip()
]
