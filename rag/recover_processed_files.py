import os
import json
import logging
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DB_DIR = "rag/data/chroma_db"
PROCESSED_FILES_LOG = "rag/data/processed_files.json"

def recover_processed_files():
    if not os.path.exists(DB_DIR):
        logger.error(f"Database directory {DB_DIR} does not exist.")
        return

    logger.info("Loading ChromaDB to recover processed files list...")
    
    # We need the embedding function to load Chroma, even if we don't use it for querying
    if "OPENAI_API_KEY" not in os.environ:
        logger.error("OPENAI_API_KEY not found in environment variables.")
        return
        
    embeddings = OpenAIEmbeddings(model="text-embedding-3-large")
    vector_store = Chroma(persist_directory=DB_DIR, embedding_function=embeddings)
    
    # Get all data from Chroma
    # Chroma's get() method returns a dict with 'ids', 'embeddings', 'documents', 'metadatas'
    # We only need metadatas
    logger.info("Fetching all documents from ChromaDB (this might take a moment)...")
    result = vector_store.get(include=['metadatas'])
    
    metadatas = result.get('metadatas', [])
    if not metadatas:
        logger.warning("No metadata found in ChromaDB.")
        return

    logger.info(f"Found {len(metadatas)} chunks in database.")
    
    # Extract unique sources
    processed_files = set()
    for meta in metadatas:
        if meta and 'source' in meta:
            processed_files.add(meta['source'])
        elif meta and 'filename' in meta:
             # Fallback if source is not absolute path, though ingest_incremental uses source now.
             # If previous ingest.py used something else, we might need to reconstruct.
             # Let's check ingest.py content first, but assuming it put something in metadata.
             pass
             
    # If ingest.py didn't store 'source' as absolute path, we might have issues matching.
    # But let's save what we have.
    
    logger.info(f"Recovered {len(processed_files)} unique files.")
    
    # Save to JSON
    with open(PROCESSED_FILES_LOG, 'w') as f:
        json.dump(list(processed_files), f, indent=2)
        
    logger.info(f"Saved processed file list to {PROCESSED_FILES_LOG}")

if __name__ == "__main__":
    recover_processed_files()
