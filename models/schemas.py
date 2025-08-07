from pydantic import BaseModel, HttpUrl
from typing import List, Optional

class SearchRequest(BaseModel):
    query: str
    top_k: Optional[int] = 5

class SearchResponse(BaseModel):
    answer: str
    relevant_snippets: List[str]
    confidence_score: Optional[float] = None

class DocumentUploadResponse(BaseModel):
    message: str
    document_id: str
    chunks_created: int

class HealthResponse(BaseModel):
    status: str
    models_loaded: bool

class HackRXRequest(BaseModel):
    documents: HttpUrl
    questions: List[str]

class HackRXResponse(BaseModel):
    answers: List[str]