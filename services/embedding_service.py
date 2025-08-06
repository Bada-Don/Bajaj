import numpy as np
import psycopg2
from pgvector.psycopg2 import register_vector
from sentence_transformers import SentenceTransformer
import json
from typing import List, Tuple
import logging

logger = logging.getLogger(__name__)

class EmbeddingService:
    def __init__(self, database_url: str, model_name: str = "all-MiniLM-L6-v2"):
        self.database_url = database_url
        self.model = SentenceTransformer(model_name)
        self._init_database()
    
    def _init_database(self):
        """Initialize database with vector extension"""
        try:
            conn = psycopg2.connect(self.database_url)
            with conn.cursor() as cur:
                # Enable pgvector extension
                cur.execute("CREATE EXTENSION IF NOT EXISTS vector")
                
                # Create embeddings table
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS embeddings (
                        id SERIAL PRIMARY KEY,
                        document_id VARCHAR(255),
                        chunk_text TEXT,
                        embedding vector(384),
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Create index for similarity search
                cur.execute("""
                    CREATE INDEX IF NOT EXISTS embeddings_vector_idx 
                    ON embeddings USING ivfflat (embedding vector_cosine_ops)
                """)
                
            conn.commit()
            conn.close()
            register_vector(conn)
            logger.info("Database initialized successfully")
            
        except Exception as e:
            logger.error(f"Database initialization failed: {e}")
            raise
    
    def store_embeddings(self, document_id: str, chunks: List[str]) -> int:
        """Store document chunks and their embeddings"""
        conn = psycopg2.connect(self.database_url)
        register_vector(conn)
        
        try:
            with conn.cursor() as cur:
                # Delete existing embeddings for this document
                cur.execute("DELETE FROM embeddings WHERE document_id = %s", (document_id,))
                
                # Generate and store new embeddings
                for chunk in chunks:
                    embedding = self.model.encode(f"passage: {chunk}")
                    cur.execute("""
                        INSERT INTO embeddings (document_id, chunk_text, embedding)
                        VALUES (%s, %s, %s)
                    """, (document_id, chunk, embedding.tolist()))
                
            conn.commit()
            logger.info(f"Stored {len(chunks)} embeddings for document {document_id}")
            return len(chunks)
            
        except Exception as e:
            conn.rollback()
            logger.error(f"Failed to store embeddings: {e}")
            raise
        finally:
            conn.close()
    
    def search_similar(self, query: str, top_k: int = 100) -> List[Tuple[str, float]]:
        """Search for similar chunks using cosine similarity"""
        query_embedding = self.model.encode(f"query: {query}")
        
        conn = psycopg2.connect(self.database_url)
        register_vector(conn)
        
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT chunk_text, 1 - (embedding <=> %s) as similarity
                    FROM embeddings
                    ORDER BY embedding <=> %s
                    LIMIT %s
                """, (query_embedding.tolist(), query_embedding.tolist(), top_k))
                
                results = cur.fetchall()
                return [(text, float(sim)) for text, sim in results]
                
        except Exception as e:
            logger.error(f"Search failed: {e}")
            raise
        finally:
            conn.close()