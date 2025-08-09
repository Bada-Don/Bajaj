# services/embedding_service.py

import numpy as np
from sentence_transformers import SentenceTransformer
import faiss
from typing import List, Tuple, Dict
import logging
import sqlite3
import os
import torch
import re  # <-- Import Regular Expressions
from rank_bm25 import BM25Okapi
from config import Config

logger = logging.getLogger(__name__)

class EmbeddingService:
    def __init__(self, database_url: str, model_name: str = "BAAI/bge-base-en-v1.5"):
        self.database_url = database_url
        self.model = SentenceTransformer(model_name, device=Config.DEVICE)
        self.db_path = self._get_sqlite_path()
        self._init_sqlite()
        
        # In-memory storage for both search indexes
        self.faiss_index = None
        self.bm25_index = None
        self.chunk_id_map = []
        self.chunk_texts = []

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
        """Load a document's chunks and build both FAISS and BM25 indexes."""
        logger.info(f"Loading document {document_id} and building hybrid search indexes.")
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute("SELECT id, chunk_text FROM chunks WHERE document_id = ?", (document_id,))
            results = cur.fetchall()

        if not results:
            raise ValueError(f"No chunks found for document_id: {document_id}.")

        self.chunk_id_map = [row[0] for row in results]
        self.chunk_texts = [row[1] for row in results]

        # --- 1. Build Sparse Index (BM25) ---
        logger.info("Building BM25 (sparse) index...")
        tokenized_corpus = [doc.split(" ") for doc in self.chunk_texts]
        self.bm25_index = BM25Okapi(tokenized_corpus)
        logger.info("BM25 index built successfully.")

        # --- 2. Build Dense Index (FAISS) ---
        logger.info("Building FAISS (dense) index...")
        embeddings = self.model.encode(
            self.chunk_texts,
            batch_size=8,
            convert_to_tensor=False,
            show_progress_bar=True
        )
        embeddings = np.array(embeddings, dtype=np.float32)
        
        embedding_dim = embeddings.shape[1]
        self.faiss_index = faiss.IndexFlatIP(embedding_dim)
        faiss.normalize_L2(embeddings)
        self.faiss_index.add(embeddings)
        
        torch.cuda.empty_cache()
        logger.info("FAISS index built successfully.")

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

    # --- START: NEW HELPER FUNCTION ---
    def _transform_article_query(self, query: str) -> str:
        """
        Detects if the query asks for a specific article and transforms it
        to improve keyword matching with the document's format (e.g., "21.").
        """
        # Regex to find "Article" followed by a number, like Article 21 or article 19(2)
        match = re.search(r'[Aa]rticle\s*(\d+(\(\d+\))?)', query)
        if match:
            article_identifier = match.group(1)
            transformed_query = f"{query} {article_identifier}."
            logger.info(f"Original query '{query}' transformed for BM25 to '{transformed_query}'")
            return transformed_query
        return query
    # --- END: NEW HELPER FUNCTION ---

    def search_similar(self, query: str, top_k: int = 30) -> List[Tuple[str, float]]:
        """Performs Hybrid Search using FAISS and BM25 with a query transformation step."""
        if not self.faiss_index or not self.bm25_index:
            raise RuntimeError("Indexes are not built. Call load_document_into_memory() first.")

        # --- 1. Dense Search (FAISS) ---
        instructed_query = f"Represent this sentence for searching relevant passages: {query}"
        query_embedding = self.model.encode(instructed_query)
        query_embedding = np.array([query_embedding], dtype=np.float32)
        faiss.normalize_L2(query_embedding)
        distances, faiss_indices = self.faiss_index.search(query_embedding, top_k)

        # --- 2. Sparse Search (BM25) with transformed query ---
        bm25_query_text = self._transform_article_query(query)
        tokenized_query = bm25_query_text.split(" ")
        bm25_scores = self.bm25_index.get_scores(tokenized_query)
        bm25_indices = np.argsort(bm25_scores)[::-1][:top_k]

        # --- 3. Reciprocal Rank Fusion (RRF) ---
        fused_scores: Dict[int, float] = {}
        k = 60.0

        for rank, idx in enumerate(faiss_indices[0]):
            if idx != -1:
                fused_scores[idx] = fused_scores.get(idx, 0) + 1.0 / (k + rank + 1)

        for rank, idx in enumerate(bm25_indices):
            fused_scores[idx] = fused_scores.get(idx, 0) + 1.0 / (k + rank + 1)

        reranked_results = sorted(fused_scores.items(), key=lambda x: x[1], reverse=True)

        top_results = []
        for doc_idx, score in reranked_results[:top_k]:
            top_results.append((self.chunk_texts[doc_idx], score))
            
        logger.info(f"Hybrid search found {len(top_results)} results.")
        return top_results
