# config.py

import os
from chromadb.config import Settings
from dotenv import load_dotenv

# Load from .env
load_dotenv()

class Config:
    # Flask Config
    SECRET_KEY = os.environ.get("SECRET_KEY", "supersecretkey")
    DEBUG = True  

    # ChromaDB Config
    CHROMA_DB_DIR = os.environ.get("CHROMA_DB_DIR", "./chroma_storage")
    CHROMA_SETTINGS = Settings(
        chroma_db_impl="duckdb+parquet",
        persist_directory=CHROMA_DB_DIR
    )

    # Gemini API Config
    GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
    GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")


#  Aliases for convenience (optional)
CHROMA_PERSIST_DIR = Config.CHROMA_DB_DIR
GEMINI_API_KEY = Config.GEMINI_API_KEY
