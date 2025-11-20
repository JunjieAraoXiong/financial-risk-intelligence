import os
import glob
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Paths
RAW_DATA_DIR = "rag/data/raw"
DB_DIR = "rag/data/chroma_db"

def ingest_documents():
    """
    Ingest PDFs from rag/data/raw into ChromaDB.
    """
    # 1. Load Documents
    # Recursive search for all PDFs in subdirectories
    pdf_files = glob.glob(os.path.join(RAW_DATA_DIR, "**/*.pdf"), recursive=True)
    if not pdf_files:
        logger.warning(f"No PDF files found in {RAW_DATA_DIR}")
        return

    logger.info(f"Found {len(pdf_files)} PDF files.")
    
    documents = []
    for pdf_path in pdf_files:
        try:
            loader = PyPDFLoader(pdf_path)
            docs = loader.load()
            # Add filename as metadata if not present (PyPDFLoader usually adds 'source')
            for doc in docs:
                doc.metadata['filename'] = os.path.basename(pdf_path)
            documents.extend(docs)
            logger.info(f"Loaded {len(docs)} pages from {os.path.basename(pdf_path)}")
        except Exception as e:
            logger.error(f"Failed to load {pdf_path}: {e}")

    if not documents:
        logger.warning("No documents loaded.")
        return

    # 2. Split Text
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50,
        separators=["\n\n", "\n", " ", ""]
    )
    chunks = text_splitter.split_documents(documents)
    logger.info(f"Split into {len(chunks)} chunks.")

    # 3. Embed and Store
    logger.info("Initializing Embeddings (all-MiniLM-L6-v2)...")
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

    logger.info(f"Creating/Updating ChromaDB at {DB_DIR}...")
    vector_store = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=DB_DIR
    )
    # vector_store.persist() # Chroma 0.4+ persists automatically

    logger.info("Ingestion Complete.")

if __name__ == "__main__":
    # Ensure directories exist
    os.makedirs(RAW_DATA_DIR, exist_ok=True)
    os.makedirs(DB_DIR, exist_ok=True)
    
    ingest_documents()
