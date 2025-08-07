import numpy as np
from sentence_transformers import SentenceTransformer
import json
from typing import List, Tuple
import logging
import sqlite3
import os

logger = logging.getLogger(__name__)

class EmbeddingService:
    def __init__(self, database_url: str, model_name: str = "all-MiniLM-L6-v2"):
        self.database_url = database_url
        self.model = SentenceTransformer(model_name)
        self.db_type = self._detect_db_type()
        self._init_database()
    
    def _detect_db_type(self) -> str:
        """Detect database type from URL"""
        if self.database_url.startswith('sqlite://'):
            return 'sqlite'
        elif self.database_url.startswith('postgresql://') or self.database_url.startswith('postgres://'):
            return 'postgresql'
        else:
            raise ValueError(f"Unsupported database URL: {self.database_url}")
    
    def _get_sqlite_path(self) -> str:
        """Extract SQLite file path from URL"""
        if self.database_url.startswith('sqlite:///'):
            return self.database_url[10:]  # Remove 'sqlite:///' prefix
        elif self.database_url.startswith('sqlite://'):
            return self.database_url[9:]   # Remove 'sqlite://' prefix
        else:
            return self.database_url
    
    def _init_database(self):
        """Initialize database with appropriate schema"""
        try:
            if self.db_type == 'sqlite':
                self._init_sqlite()
            elif self.db_type == 'postgresql':
                self._init_postgresql()
            logger.info(f"Database initialized successfully ({self.db_type})")
        except Exception as e:
            logger.error(f"Database initialization failed: {e}")
            raise
    
    def _init_sqlite(self):
        """Initialize SQLite database"""
        db_path = self._get_sqlite_path()
        # Ensure directory exists
        os.makedirs(os.path.dirname(db_path) if os.path.dirname(db_path) else '.', exist_ok=True)
        
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        try:
            # Create embeddings table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS embeddings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    document_id TEXT,
                    chunk_text TEXT,
                    embedding TEXT,  -- Store as JSON string
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            # Create index for faster searches
            cur.execute("CREATE INDEX IF NOT EXISTS idx_document_id ON embeddings(document_id)")
            conn.commit()
        finally:
            cur.close()
            conn.close()
    
    def _init_postgresql(self):
        """Initialize PostgreSQL database"""
        import psycopg2
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
    
    def store_embeddings(self, document_id: str, chunks: List[str]) -> int:
        """Store document chunks and their embeddings"""
        try:
            if self.db_type == 'sqlite':
                return self._store_embeddings_sqlite(document_id, chunks)
            elif self.db_type == 'postgresql':
                return self._store_embeddings_postgresql(document_id, chunks)
        except Exception as e:
            logger.error(f"Failed to store embeddings: {e}")
            raise
    
    def _store_embeddings_sqlite(self, document_id: str, chunks: List[str]) -> int:
        """Store embeddings in SQLite"""
        db_path = self._get_sqlite_path()
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        try:
            # Delete existing embeddings for this document
            cur.execute("DELETE FROM embeddings WHERE document_id = ?", (document_id,))
            # Generate and store new embeddings
            for chunk in chunks:
                embedding = self.model.encode(f"passage: {chunk}")
                # Store embedding as JSON string
                embedding_json = json.dumps(embedding.tolist())
                cur.execute("""
                    INSERT INTO embeddings (document_id, chunk_text, embedding)
                    VALUES (?, ?, ?)
                """, (document_id, chunk, embedding_json))
            conn.commit()
            logger.info(f"Stored {len(chunks)} embeddings for document {document_id}")
            return len(chunks)
        finally:
            cur.close()
            conn.close()
    
    def _store_embeddings_postgresql(self, document_id: str, chunks: List[str]) -> int:
        """Store embeddings in PostgreSQL"""
        import psycopg2
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
            raise
        finally:
            conn.close()
    
    def search_similar(self, query: str, top_k: int = 100) -> List[Tuple[str, float]]:
        """Search for similar chunks using cosine similarity"""
        logger.info(f"Searching for query: {query}")
        query_embedding = self.model.encode(f"query: {query}")
        
        try:
            if self.db_type == 'sqlite':
                return self._search_similar_sqlite(query_embedding, top_k)
            elif self.db_type == 'postgresql':
                return self._search_similar_postgresql(query_embedding, top_k)
        except Exception as e:
            logger.error(f"Search failed: {str(e)}")
            logger.exception("Full exception details:")
            raise
    
    def _search_similar_sqlite(self, query_embedding: np.ndarray, top_k: int) -> List[Tuple[str, float]]:
        """Search similar chunks in SQLite"""
        db_path = self._get_sqlite_path()
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        try:
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
            for text, emb_json in results:
                emb = np.array(json.loads(emb_json), dtype=np.float32)
                sim = float(np.dot(query_embedding, emb) / (np.linalg.norm(query_embedding) * np.linalg.norm(emb) + 1e-10))
                scored.append((text, sim))
            
            # Sort by similarity descending and return top_k
            scored.sort(key=lambda x: x[1], reverse=True)
            top_results = scored[:top_k]
            
            logger.info(f"Found {len(top_results)} relevant results")
            if top_results:
                logger.info(f"Top similarity score: {top_results[0][1]}")
            
            return top_results
        finally:
            cur.close()
            conn.close()
    
    def _search_similar_postgresql(self, query_embedding: np.ndarray, top_k: int) -> List[Tuple[str, float]]:
        """Search similar chunks in PostgreSQL"""
        import psycopg2
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
        finally:
            conn.close()