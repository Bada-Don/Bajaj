import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
    DATABASE_URL = os.getenv("DATABASE_URL")
    REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
    
    # Model settings
    EMBEDDING_MODEL = "all-MiniLM-L6-v2"
    RERANKER_MODEL = "cross-encoder/ms-marco-MiniLM-L6-v2"
    
    # Document processing
    CHUNK_LENGTH = 600
    CHUNK_OVERLAP = 200
    
    # Search settings
    TOP_K_INITIAL = 100
    TOP_K_RERANKED = 5
    
    # API settings
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB