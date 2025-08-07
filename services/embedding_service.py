import numpy as np
import psycopg2
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
                # Create embeddings table with FLOAT[] for embedding
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS embeddings (
                        id SERIAL PRIMARY KEY,
                        document_id VARCHAR(255),
                        chunk_text TEXT,
                        embedding FLOAT[],
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
            conn.commit()
            conn.close()
            logger.info("Database initialized successfully")
        except Exception as e:
            logger.error(f"Database initialization failed: {e}")
            raise
    
    def store_embeddings(self, document_id: str, chunks: List[str]) -> int:
        """Store document chunks and their embeddings"""
        conn = psycopg2.connect(self.database_url)
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
                    """, (document_id, chunk, list(map(float, embedding))))
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
        logger.info(f"Searching for query: {query}")
        query_embedding = self.model.encode(f"query: {query}")
        conn = psycopg2.connect(self.database_url)
        try:
            with conn.cursor() as cur:
                # First check if we have any embeddings at all
                cur.execute("SELECT COUNT(*) FROM embeddings")
                count = cur.fetchone()[0]
                logger.info(f"Total embeddings in database: {count}")
                
                if count == 0:
                    logger.warning("No embeddings found in database")
                    return []
                
                cur.execute("SELECT chunk_text, embedding FROM embeddings")
                results = cur.fetchall()
                logger.info(f"Retrieved {len(results)} chunks for comparison")
                
                scored = []
                for text, emb in results:
                    emb_np = np.array(emb, dtype=np.float32)
                    sim = float(np.dot(query_embedding, emb_np) / (np.linalg.norm(query_embedding) * np.linalg.norm(emb_np) + 1e-10))
                    scored.append((text, sim))
                
                # Sort by similarity descending and return top_k
                scored.sort(key=lambda x: x[1], reverse=True)
                top_results = scored[:top_k]
                
                logger.info(f"Found {len(top_results)} relevant results")
                if top_results:
                    logger.info(f"Top similarity score: {top_results[0][1]}")
                
                return top_results
                
        except Exception as e:
            logger.error(f"Search failed: {str(e)}")
            logger.exception("Full exception details:")
            raise
        finally:
            conn.close()