# preload_documents.py

import os
import hashlib
import logging
from config import Config
from services.document_processor import DocumentProcessor
from services.embedding_service import EmbeddingService

# Configure basic logging to see progress
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- IMPORTANT: PASTE YOUR 5 DOCUMENT URLS HERE ---
DOCUMENT_URLS = [
    "https://hackrx.blob.core.windows.net/assets/policy.pdf?sv=2023-01-03&st=2025-07-04T09%3A11%3A24Z&se=2027-07-05T09%3A11%3A00Z&sr=b&sp=r&sig=N4a9OU0w0QXO6AOIBiu4bpl7AXvEZogeT%2FjUHNO7HzQ%3D",
    "https://hackrx.blob.core.windows.net/assets/hackrx_6/policies/CHOTGDP23004V012223.pdf?sv=2023-01-03&st=2025-07-30T06%3A46%3A49Z&se=2025-09-01T06%3A46%3A00Z&sr=c&sp=rl&sig=9szykRKdGYj0BVm1skP%2BX8N9%2FRENEn2k7MQPUp33jyQ%3D",  # <-- Replace with your real URL
    "https://hackrx.blob.core.windows.net/assets/hackrx_6/policies/EDLHLGA23009V012223.pdf?sv=2023-01-03&st=2025-07-30T06%3A46%3A49Z&se=2025-09-01T06%3A46%3A00Z&sr=c&sp=rl&sig=9szykRKdGYj0BVm1skP%2BX8N9%2FRENEn2k7MQPUp33jyQ%3D",   # <-- Replace with your real URL
    "https://hackrx.blob.core.windows.net/assets/hackrx_6/policies/HDFHLIP23024V072223.pdf?sv=2023-01-03&st=2025-07-30T06%3A46%3A49Z&se=2025-09-01T06%3A46%3A00Z&sr=c&sp=rl&sig=9szykRKdGYj0BVm1skP%2BX8N9%2FRENEn2k7MQPUp33jyQ%3D",  # <-- Replace with your real URL
    "https://hackrx.blob.core.windows.net/assets/hackrx_6/policies/ICIHLIP22012V012223.pdf?sv=2023-01-03&st=2025-07-30T06%3A46%3A49Z&se=2025-09-01T06%3A46%3A00Z&sr=c&sp=rl&sig=9szykRKdGYj0BVm1skP%2BX8N9%2FRENEn2k7MQPUp33jyQ%3D",    # <-- Replace with your real URL
]

def main():
    """
    Processes a list of document URLs and stores their text chunks in the database.
    """
    logging.info("--- Starting Document Pre-loading Script ---")
    
    # Initialize the services we need
    doc_processor = DocumentProcessor(
        chunk_length=Config.CHUNK_LENGTH,
        chunk_overlap=Config.CHUNK_OVERLAP
    )
    
    embedding_service = EmbeddingService(
        database_url=Config.DATABASE_URL,
        model_name=Config.EMBEDDING_MODEL
    )

    for url in DOCUMENT_URLS:
        logging.info(f"Processing document: {url[:50]}...")
        temp_file_path = None
        try:
            # Generate the same document_id as the main app would
            document_id = hashlib.md5(str(url).encode()).hexdigest()[:8]

            # 1. Extract text from the document URL
            text, temp_file_path = doc_processor.extract_text_from_url(url)
            if not text.strip():
                logging.warning(f"No text could be extracted from {url}. Skipping.")
                continue

            # 2. Split the text into chunks
            chunks = doc_processor.chunk_text(text)
            logging.info(f"Document chunked into {len(chunks)} pieces.")

            # 3. Store the chunks in the database
            chunks_stored = embedding_service.store_chunks(document_id, chunks)
            logging.info(f"Successfully stored {chunks_stored} chunks for document_id '{document_id}'.")

        except Exception as e:
            logging.error(f"Failed to process document {url}. Error: {e}")
        finally:
            # Clean up the temporary file downloaded by requests
            if temp_file_path and os.path.exists(temp_file_path):
                os.remove(temp_file_path)
                logging.info(f"Cleaned up temp file: {temp_file_path}")

    logging.info("--- Document Pre-loading Complete ---")

if __name__ == "__main__":
    main()