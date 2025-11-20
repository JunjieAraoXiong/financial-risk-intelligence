import os
import glob
import json
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

RAW_DATA_DIR = "rag/data/raw"
DB_DIR = "rag/data/chroma_db"
PROCESSED_FILES_LOG = "rag/data/processed_files.json"

def load_processed_files():
    """Load the list of already processed files."""
    if os.path.exists(PROCESSED_FILES_LOG):
        with open(PROCESSED_FILES_LOG, 'r') as f:
            return set(json.load(f))
    return set()

def save_processed_files(processed_files):
    """Save the list of processed files."""
    with open(PROCESSED_FILES_LOG, 'w') as f:
        json.dump(list(processed_files), f, indent=2)

def ingest_new_documents():
    """Ingest only NEW PDFs that haven't been processed yet."""
    # Get all PDF files
    pdf_files = glob.glob(os.path.join(RAW_DATA_DIR, "**/*.pdf"), recursive=True)
    if not pdf_files:
        logger.warning(f"No PDF files found in {RAW_DATA_DIR}")
        return

    # Load already processed files
    processed_files = load_processed_files()
    
    # Find new files
    new_files = [f for f in pdf_files if f not in processed_files]
    
    if not new_files:
        logger.info("No new files to process. All files already ingested.")
        return
    
    logger.info(f"Found {len(new_files)} new PDF files to process.")
    
    # Load new documents
    documents = []
    for pdf_path in new_files:
        try:
            loader = PyPDFLoader(pdf_path)
            docs = loader.load()
            for doc in docs:
                doc.metadata['filename'] = os.path.basename(pdf_path)
            documents.extend(docs)
            logger.info(f"Loaded {len(docs)} pages from {os.path.basename(pdf_path)}")
        except Exception as e:
            logger.error(f"Failed to load {pdf_path}: {e}")

    if not documents:
        logger.warning("No new documents loaded.")
        return

    # Split text
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50,
        separators=["\\n\\n", "\\n", " ", ""]
    )
    chunks = text_splitter.split_documents(documents)
    logger.info(f"Split into {len(chunks)} new chunks.")

    # Load existing database and add new chunks
    logger.info("Loading existing database...")
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    
    if os.path.exists(DB_DIR):
        # Add to existing database
        vector_store = Chroma(persist_directory=DB_DIR, embedding_function=embeddings)
        vector_store.add_documents(chunks)
        logger.info(f"Added {len(chunks)} chunks to existing database.")
    else:
        # Create new database
        vector_store = Chroma.from_documents(
            documents=chunks,
            embedding=embeddings,
            persist_directory=DB_DIR
        )
        logger.info(f"Created new database with {len(chunks)} chunks.")
    
    # Update processed files log
    processed_files.update(new_files)
    save_processed_files(processed_files)
    
    logger.info("Incremental ingestion complete.")

if __name__ == "__main__":
    os.makedirs(RAW_DATA_DIR, exist_ok=True)
    os.makedirs(DB_DIR, exist_ok=True)
    ingest_new_documents()
