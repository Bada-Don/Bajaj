# services/embedding_service.py

import numpy as np
from sentence_transformers import SentenceTransformer
import faiss  # Import FAISS
from typing import List, Tuple
import logging
import sqlite3
import os

logger = logging.getLogger(__name__)

class EmbeddingService:
    def __init__(self, database_url: str, model_name: str = "all-MiniLM-L6-v2"):
        self.database_url = database_url
        self.model = SentenceTransformer(model_name)
        self.db_path = self._get_sqlite_path()
        self._init_sqlite()
        
        # In-memory storage for FAISS index and chunk texts
        self.index = None
        self.chunk_id_map = []

    def _get_sqlite_path(self) -> str:
        """Extract SQLite file path from URL"""
        return self.database_url.replace('sqlite:///', '')

    def _init_sqlite(self):
        """Initialize SQLite database for storing chunk text"""
        os.makedirs(os.path.dirname(self.db_path) or '.', exist_ok=True)
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute("""
                CREATE TABLE IF NOT EXISTS chunks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    document_id TEXT,
                    chunk_text TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            cur.execute("CREATE INDEX IF NOT EXISTS idx_chunk_doc_id ON chunks(document_id)")
    
    def load_document_into_memory(self, document_id: str):
        """Load a document's chunks and build a FAISS index in memory."""
        logger.info(f"Loading document {document_id} into memory and building FAISS index.")
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute("SELECT id, chunk_text FROM chunks WHERE document_id = ?", (document_id,))
            results = cur.fetchall()
        
        if not results:
            raise ValueError(f"No chunks found for document_id: {document_id}. Ensure embeddings were stored first.")

        # Separate IDs and texts
        self.chunk_id_map = [row[0] for row in results]
        chunk_texts = [row[1] for row in results]

        # Batch encode all chunks for efficiency
        logger.info(f"Generating embeddings for {len(chunk_texts)} chunks...")
        embeddings = self.model.encode([f"passage: {chunk}" for chunk in chunk_texts], convert_to_tensor=False, show_progress_bar=False)
        embeddings = np.array(embeddings, dtype=np.float32)
        
        # Build the FAISS index
        embedding_dim = embeddings.shape[1]
        self.index = faiss.IndexFlatIP(embedding_dim)  # Using Inner Product (related to cosine similarity)
        faiss.normalize_L2(embeddings) # Normalize for cosine similarity search
        self.index.add(embeddings)
        logger.info(f"FAISS index built successfully with {self.index.ntotal} vectors.")

    def store_chunks(self, document_id: str, chunks: List[str]) -> int:
        """Store document chunks in the database (without embeddings)."""
        logger.info(f"Storing {len(chunks)} text chunks for document {document_id}")
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            # Clear old chunks for this document to prevent stale data
            cur.execute("DELETE FROM chunks WHERE document_id = ?", (document_id,))
            # Insert new chunks
            cur.executemany(
                "INSERT INTO chunks (document_id, chunk_text) VALUES (?, ?)",
                [(document_id, chunk) for chunk in chunks]
            )
            conn.commit()
            return cur.rowcount

    def search_similar(self, query: str, top_k: int = 100) -> List[Tuple[str, float]]:
        """Search for similar chunks using the in-memory FAISS index."""
        if self.index is None or not self.chunk_id_map:
            raise RuntimeError("FAISS index is not built. Call load_document_into_memory() first.")
            
        logger.info(f"Searching for query: {query}")
        query_embedding = self.model.encode(f"query: {query}")
        query_embedding = np.array([query_embedding], dtype=np.float32)
        faiss.normalize_L2(query_embedding) # Normalize query vector

        # Perform the search
        distances, indices = self.index.search(query_embedding, top_k)
        
        # Retrieve the actual chunk texts using the indices
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            top_results = []
            for i, idx in enumerate(indices[0]):
                if idx != -1:
                    # The index `idx` corresponds to the position in our original `chunk_texts` list
                    chunk_id = self.chunk_id_map[idx]
                    cur.execute("SELECT chunk_text FROM chunks WHERE id = ?", (chunk_id,))
                    text_result = cur.fetchone()
                    if text_result:
                        top_results.append((text_result[0], float(distances[0][i])))
        
        logger.info(f"FAISS search found {len(top_results)} results.")
        return top_results