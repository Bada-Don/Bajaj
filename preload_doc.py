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
    "https://hackrx.blob.core.windows.net/assets/hackrx_6/policies/ICIHLIP22012V012223.pdf?sv=2023-01-03&st=2025-07-30T06%3A46%3A49Z&se=2025-09-01T06%3A46%3A00Z&sr=c&sp=rl&sig=9szykRKdGYj0BVm1skP%2BX8N9%2FRENEn2k7MQPUp33jyQ%3D",
    "https://hackrx.blob.core.windows.net/assets/Arogya%20Sanjeevani%20Policy%20-%20CIN%20-%20U10200WB1906GOI001713%201.pdf?sv=2023-01-03&st=2025-07-21T08%3A29%3A02Z&se=2025-09-22T08%3A29%3A00Z&sr=b&sp=r&sig=nzrz1K9Iurt%2BBXom%2FB%2BMPTFMFP3PRnIvEsipAX10Ig4%3D",
    "https://hackrx.blob.core.windows.net/assets/Super_Splendor_(Feb_2023).pdf?sv=2023-01-03&st=2025-07-21T08%3A10%3A00Z&se=2025-09-22T08%3A10%3A00Z&sr=b&sp=r&sig=vhHrl63YtrEOCsAy%2BpVKr20b3ZUo5HMz1lF9%2BJh6LQ0%3D",
    "https://hackrx.blob.core.windows.net/assets/Family%20Medicare%20Policy%20(UIN-%20UIIHLIP22070V042122)%201.pdf?sv=2023-01-03&st=2025-07-22T10%3A17%3A39Z&se=2025-08-23T10%3A17%3A00Z&sr=b&sp=r&sig=dA7BEMIZg3WcePcckBOb4QjfxK%2B4rIfxBs2%2F%2BNwoPjQ%3D",
    "https://hackrx.blob.core.windows.net/assets/indian_constitution.pdf?sv=2023-01-03&st=2025-07-28T06%3A42%3A00Z&se=2026-11-29T06%3A42%3A00Z&sr=b&sp=r&sig=5Gs%2FOXqP3zY00lgciu4BZjDV5QjTDIx7fgnfdz6Pu24%3D",
    "https://hackrx.blob.core.windows.net/assets/principia_newton.pdf?sv=2023-01-03&st=2025-07-28T07%3A20%3A32Z&se=2026-07-29T07%3A20%3A00Z&sr=b&sp=r&sig=V5I1QYyigoxeUMbnUKsdEaST99F5%2FDfo7wpKg9XXF5w%3D",
    "https://hackrx.blob.core.windows.net/assets/Happy%20Family%20Floater%20-%202024%20OICHLIP25046V062425%201.pdf?sv=2023-01-03&spr=https&st=2025-07-31T17%3A24%3A30Z&se=2026-08-01T17%3A24%3A00Z&sr=b&sp=r&sig=VNMTTQUjdXGYb2F4Di4P0zNvmM2rTBoEHr%2BnkUXIqpQ%3D",
    "https://hackrx.blob.core.windows.net/assets/UNI%20GROUP%20HEALTH%20INSURANCE%20POLICY%20-%20UIIHLGP26043V022526%201.pdf?sv=2023-01-03&spr=https&st=2025-07-31T17%3A06%3A03Z&se=2026-08-01T17%3A06%3A00Z&sr=b&sp=r&sig=wLlooaThgRx91i2z4WaeggT0qnuUUEzIUKj42GsvMfg%3D",
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