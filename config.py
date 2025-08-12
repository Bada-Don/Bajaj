# config.py

import os
from dotenv import load_dotenv
import torch

load_dotenv()

class Config:
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./test.db")
    REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
    
    # Model settings
    EMBEDDING_MODEL = "BAAI/bge-base-en-v1.5" # <-- CHANGED
    RERANKER_MODEL = "mixedbread-ai/mxbai-rerank-base-v1" # <-- CHANGED
    LLM_MODEL_NAME = "granite3.1-moe:3b"

    # Document processing
    CHUNK_LENGTH = 400
    CHUNK_OVERLAP = 100
    
    # Search settings
    TOP_K_INITIAL = 100  # <-- CHANGED FROM 100 to 25
    TOP_K_RERANKED = 15
    
    # API settings
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

    DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
