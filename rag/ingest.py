import os
import glob
import json
import re
import time
from pathlib import Path
import requests
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document
import logging

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Use absolute paths based on script location
BASE_DIR = Path(__file__).parent
RAW_DATA_DIR = BASE_DIR / "data" / "raw"
DB_DIR = BASE_DIR / "data" / "chroma_db"
PROCESSED_FILES_LOG = BASE_DIR / "data" / "processed_files.json"


def load_processed_files():
    """Load list of already processed files."""
    if PROCESSED_FILES_LOG.exists():
        with open(PROCESSED_FILES_LOG, 'r') as f:
            return set(json.load(f))
    return set()


def save_processed_files(processed: set):
    """Save list of processed files for checkpointing."""
    with open(PROCESSED_FILES_LOG, 'w') as f:
        json.dump(list(processed), f, indent=2)


def clean_html_tags(text: str) -> str:
    """Remove HTML tags from text."""
    clean = re.sub(r'<[^>]+>', '', text)
    return clean.strip()


def load_json_article(filepath: str) -> list[Document]:
    """Load a Financial Times JSON article and return as Document."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Extract text content
        title = data.get('title', '')
        standfirst = data.get('standfirst', '')
        body = clean_html_tags(data.get('bodyXML', ''))
        byline = data.get('byline', '')
        date = data.get('firstPublishedDate', '')

        # Combine into document
        content = f"{title}\n\n{standfirst}\n\n{body}"
        if byline:
            content = f"By {byline}\n\n{content}"

        metadata = {
            'source': filepath,
            'filename': os.path.basename(filepath),
            'title': title,
            'date': date,
            'type': 'json_article'
        }

        return [Document(page_content=content, metadata=metadata)]
    except Exception as e:
        logger.error(f"Failed to load JSON {filepath}: {e}")
        return []


def ingest_documents():
    """
    Ingest PDFs and JSONs from rag/data/raw into ChromaDB.
    Supports checkpointing and deduplication.
    """
    # Find all files
    pdf_files = glob.glob(str(RAW_DATA_DIR / "**" / "*.pdf"), recursive=True)
    json_files = glob.glob(str(RAW_DATA_DIR / "**" / "*.json"), recursive=True)
    all_files = pdf_files + json_files

    if not all_files:
        logger.warning(f"No PDF or JSON files found in {RAW_DATA_DIR}")
        return

    logger.info(f"Found {len(pdf_files)} PDF files and {len(json_files)} JSON files.")
    logger.info(f"Total: {len(all_files)} files to process.")

    # Load processed files for deduplication
    processed_files = load_processed_files()
    files_to_process = [f for f in all_files if f not in processed_files]

    if not files_to_process:
        logger.info("All files already processed. Nothing to do.")
        return

    logger.info(f"Skipping {len(processed_files)} already processed files.")
    logger.info(f"Processing {len(files_to_process)} new files.")

    # Initialize embeddings - BGE with MPS (M2 GPU)
    logger.info("Initializing BGE embeddings with MPS (M2 GPU)...")
    from langchain_community.embeddings import HuggingFaceEmbeddings
    embeddings = HuggingFaceEmbeddings(
        model_name="BAAI/bge-large-en-v1.5",
        model_kwargs={'device': 'mps'},  # M2 Pro GPU acceleration
        encode_kwargs={'normalize_embeddings': True}
    )

    # Initialize or load ChromaDB
    logger.info(f"Initializing ChromaDB at {DB_DIR}...")
    DB_DIR.mkdir(parents=True, exist_ok=True)
    vector_store = Chroma(persist_directory=str(DB_DIR), embedding_function=embeddings)

    # Text splitter
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50,
        separators=["\n\n", "\n", " ", ""]
    )

    # Process files in batches with checkpointing
    # Reduced batch size for lower RAM usage (was 5000)
    batch_size = 1500
    chunks_buffer = []
    total_chunks = 0

    for i, filepath in enumerate(files_to_process):
        try:
            # Load document based on type
            if filepath.endswith('.pdf'):
                loader = PyPDFLoader(filepath)
                docs = loader.load()
                for doc in docs:
                    doc.metadata['filename'] = os.path.basename(filepath)
                    doc.metadata['type'] = 'pdf'
            else:  # JSON
                docs = load_json_article(filepath)

            if not docs:
                continue

            # Split into chunks
            chunks = text_splitter.split_documents(docs)
            chunks_buffer.extend(chunks)

            # Mark as processed
            processed_files.add(filepath)

            # Log progress
            if (i + 1) % 50 == 0:
                logger.info(f"Loaded {i + 1}/{len(files_to_process)} files ({len(chunks_buffer)} chunks buffered)")

            # Add to DB when buffer is full
            if len(chunks_buffer) >= batch_size:
                # Split into sub-batches to respect ChromaDB max (5461)
                chroma_max = 5000  # Stay under 5461 limit
                for j in range(0, len(chunks_buffer), chroma_max):
                    sub_batch = chunks_buffer[j:j + chroma_max]

                    # Retry logic for network errors
                    max_retries = 5
                    for attempt in range(max_retries):
                        try:
                            vector_store.add_documents(sub_batch)
                            total_chunks += len(sub_batch)
                            logger.info(f"Added sub-batch of {len(sub_batch)} chunks to ChromaDB (total: {total_chunks})")
                            break
                        except (requests.exceptions.ConnectionError,
                                requests.exceptions.Timeout,
                                Exception) as e:
                            if attempt < max_retries - 1:
                                wait_time = 2 ** attempt * 5  # 5, 10, 20, 40, 80 seconds
                                logger.warning(f"Network error, retrying in {wait_time}s (attempt {attempt+1}/{max_retries}): {e}")
                                time.sleep(wait_time)
                            else:
                                logger.error(f"Failed after {max_retries} retries: {e}")
                                raise

                    # Rate limit prevention - wait between batches
                    time.sleep(2)

                chunks_buffer = []

                # Checkpoint: save processed files
                save_processed_files(processed_files)
                logger.info(f"Checkpoint saved: {len(processed_files)} files processed")

        except Exception as e:
            logger.error(f"Failed to process {filepath}: {e}")
            continue

    # Add remaining chunks (split into sub-batches)
    if chunks_buffer:
        chroma_max = 5000
        for j in range(0, len(chunks_buffer), chroma_max):
            sub_batch = chunks_buffer[j:j + chroma_max]

            # Retry logic for network errors
            max_retries = 5
            for attempt in range(max_retries):
                try:
                    vector_store.add_documents(sub_batch)
                    total_chunks += len(sub_batch)
                    logger.info(f"Added final sub-batch of {len(sub_batch)} chunks (total: {total_chunks})")
                    break
                except (requests.exceptions.ConnectionError,
                        requests.exceptions.Timeout,
                        Exception) as e:
                    if attempt < max_retries - 1:
                        wait_time = 2 ** attempt * 5
                        logger.warning(f"Network error, retrying in {wait_time}s (attempt {attempt+1}/{max_retries}): {e}")
                        time.sleep(wait_time)
                    else:
                        logger.error(f"Failed after {max_retries} retries: {e}")
                        raise

            time.sleep(2)  # Rate limit prevention

    # Final checkpoint
    save_processed_files(processed_files)

    logger.info("=" * 50)
    logger.info("INGESTION COMPLETE")
    logger.info(f"Total files processed: {len(processed_files)}")
    logger.info(f"Total chunks in database: {total_chunks}")
    logger.info("=" * 50)


if __name__ == "__main__":
    # Ensure directories exist
    RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
    DB_DIR.mkdir(parents=True, exist_ok=True)

    ingest_documents()
