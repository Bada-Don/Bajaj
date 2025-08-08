from fastapi import FastAPI, HTTPException, UploadFile, File, Depends
from fastapi.middleware.cors import CORSMiddleware
import hashlib
import logging
from contextlib import asynccontextmanager
from io import BytesIO
import os

import asyncio
from functools import partial
import sqlite3 # Import sqlite3 to check for existing chunks

from config import Config
from models.schemas import (
    SearchRequest, SearchResponse, DocumentUploadResponse, 
    HealthResponse, HackRXRequest, HackRXResponse
)
from services.document_processor import DocumentProcessor
from services.embedding_service import EmbeddingService
from services.search_service import SearchService

import asyncio
from functools import partial


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global service instances
doc_processor = None
embedding_service = None
search_service = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    global doc_processor, embedding_service, search_service
    
    logger.info("Initializing services...")
    
    doc_processor = DocumentProcessor(
        chunk_length=Config.CHUNK_LENGTH,
        chunk_overlap=Config.CHUNK_OVERLAP
    )
    
    embedding_service = EmbeddingService(
        database_url=Config.DATABASE_URL,
        model_name=Config.EMBEDDING_MODEL
    )
    
    search_service = SearchService(
        google_api_key=Config.GOOGLE_API_KEY,
        reranker_model=Config.RERANKER_MODEL
    )
    
    logger.info("Services initialized successfully")
    
    yield
    
    # Shutdown
    logger.info("Shutting down services...")

app = FastAPI(
    title="Document Search API",
    description="RAG-based document search and Q&A system",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_services():
    """Dependency to ensure services are initialized"""
    if not all([doc_processor, embedding_service, search_service]):
        raise HTTPException(status_code=503, detail="Services not initialized")
    return doc_processor, embedding_service, search_service

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    services_loaded = all([doc_processor, embedding_service, search_service])
    return HealthResponse(
        status="healthy" if services_loaded else "initializing",
        models_loaded=services_loaded
    )

@app.post("/upload-url", response_model=DocumentUploadResponse)
async def upload_document_from_url(
    url: str,
    document_id: str = None,
    services = Depends(get_services)
):
    """Process document from URL"""
    doc_proc, embed_service, _ = services
    
    try:
        # Generate document ID if not provided
        if not document_id:
            document_id = hashlib.md5(url.encode()).hexdigest()[:8]
        # Extract text from URL
        text, temp_file_path = doc_proc.extract_text_from_url(url)
        try:
            if not text.strip():
                raise HTTPException(status_code=400, detail="No text could be extracted from the document")
            # Chunk the text
            chunks = doc_proc.chunk_text(text)
            # Store embeddings
            chunks_created = embed_service.store_embeddings(document_id, chunks)
            return DocumentUploadResponse(
                message="Document processed successfully",
                document_id=document_id,
                chunks_created=chunks_created
            )
        finally:
            if temp_file_path and os.path.exists(temp_file_path):
                os.remove(temp_file_path)
        
    except Exception as e:
        logger.error(f"Document processing failed: {e}")
        raise HTTPException(status_code=500, detail=f"Document processing failed: {str(e)}")

@app.post("/upload-file", response_model=DocumentUploadResponse)
async def upload_document_file(
    file: UploadFile = File(...),
    document_id: str = None,
    services = Depends(get_services)
):
    """Process uploaded document file"""
    doc_proc, embed_service, _ = services
    
    # Check file size
    if file.size and file.size > Config.MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail="File too large")
    
    try:
        # Generate document ID if not provided
        if not document_id:
            document_id = hashlib.md5(file.filename.encode()).hexdigest()[:8]
        
        try:
            # Read file content into memory
            content = await file.read()
            file_buffer = BytesIO(content)
            
            # Extract text directly from the buffer
            text = doc_proc.extract_text_from_buffer(file_buffer, file.filename)
            
            if not text.strip():
                raise HTTPException(status_code=400, detail="No text could be extracted from the document")
            
            # Chunk the text
            chunks = doc_proc.chunk_text(text)
            
            # Store embeddings
            chunks_created = embed_service.store_embeddings(document_id, chunks)
            
            return DocumentUploadResponse(
                message="Document processed successfully",
                document_id=document_id,
                chunks_created=chunks_created
            )
                
        finally:
            # Ensure the buffer is closed
            file_buffer.close()
                
    except Exception as e:
        logger.error(f"Document processing failed: {e}")
        raise HTTPException(status_code=500, detail=f"Document processing failed: {str(e)}")

@app.post("/search", response_model=SearchResponse)
async def search_documents(
    request: SearchRequest,
    services = Depends(get_services)
):
    """Search documents and generate answer"""
    _, embed_service, search_service = services
    
    try:
        # Initial similarity search
        similar_results = embed_service.search_similar(
            request.query, 
            top_k=Config.TOP_K_INITIAL
        )
        
        if not similar_results:
            return SearchResponse(
                answer="I couldn't find any relevant information to answer your question.",
                relevant_snippets=[],
                confidence_score=0.0
            )
        
        # Rerank results
        top_snippets = search_service.rerank_results(
            request.query,
            similar_results,
            top_k=request.top_k or Config.TOP_K_RERANKED
        )
        
        # Generate answer
        answer = search_service.generate_answer(request.query, top_snippets)
        
        # Calculate average confidence score
        avg_confidence = sum(score for _, score in similar_results[:len(top_snippets)]) / len(top_snippets)
        
        return SearchResponse(
            answer=answer,
            relevant_snippets=top_snippets,
            confidence_score=avg_confidence
        )
        
    except Exception as e:
        logger.error(f"Search failed: {e}")
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")

def document_exists(db_path: str, document_id: str) -> bool:
    """Check if a document's chunks are already in the database."""
    with sqlite3.connect(db_path) as conn:
        cur = conn.cursor()
        cur.execute("SELECT 1 FROM chunks WHERE document_id = ? LIMIT 1", (document_id,))
        return cur.fetchone() is not None

@app.post("/hackrx/run", response_model=HackRXResponse)
async def process_hackrx_request(
    request: HackRXRequest,
    services = Depends(get_services)
):
    """Process multiple questions for a given document URL in parallel with caching."""
    doc_proc, embed_service, search_serv = services
    
    document_id = hashlib.md5(str(request.documents).encode()).hexdigest()[:8]
    db_path = embed_service.db_path # Get db_path from the service

    try:
        # STEP 1: Process document ONLY if it's not cached
        if not document_exists(db_path, document_id):
            logger.info(f"Document {document_id} not found in cache. Processing from URL.")
            text, temp_file_path = doc_proc.extract_text_from_url(str(request.documents))
            try:
                if not text.strip():
                    raise HTTPException(status_code=400, detail="No text could be extracted from the document")
                chunks = doc_proc.chunk_text(text)
                embed_service.store_chunks(document_id, chunks)
                logger.info(f"Document {document_id} processed and cached.")
            finally:
                if 'temp_file_path' in locals() and temp_file_path and os.path.exists(temp_file_path):
                    os.remove(temp_file_path)
        else:
            logger.info(f"Document {document_id} found in cache. Skipping processing.")

        # STEP 2: Load document chunks and build FAISS index
        embed_service.load_document_into_memory(document_id)

        # STEP 3: Define the processing pipeline for a single question
        async def process_single_question(question: str):
            # a) Similarity search (fast, synchronous)
            similar_results = embed_service.search_similar(question, top_k=Config.TOP_K_INITIAL)
            if not similar_results:
                return "No relevant information found for this question."

            # b) Reranking (CPU-bound, run in a thread to not block asyncio)
            rerank_func = partial(
                search_serv.rerank_results,
                query=question,
                results=similar_results,
                top_k=Config.TOP_K_RERANKED
            )
            top_snippets = await asyncio.to_thread(rerank_func)

            # c) Generate Answer (I/O-bound, run asynchronously)
            answer = await search_serv.generate_answer_async(question, top_snippets)
            return answer

        # STEP 4: Run the pipeline for all questions concurrently
        tasks = [process_single_question(q) for q in request.questions]
        answers = await asyncio.gather(*tasks)
        
        return HackRXResponse(answers=answers)
    
    except Exception as e:
        logger.error(f"HackRX processing failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")
        
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)