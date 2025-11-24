import os
import glob
import json
import time
import re
import logging
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

RAW_DATA_DIR = "rag/data/raw"
DB_DIR = "rag/data/chroma_db"
PROCESSED_FILES_LOG = "rag/data/processed_files.json"

def clean_html(raw_html):
    """Remove HTML tags from a string."""
    if not raw_html:
        return ""
    cleanr = re.compile('<.*?>')
    cleantext = re.sub(cleanr, '', raw_html)
    return cleantext

def extract_metadata_from_filename(filename):
    """Extract date and source from filename."""
    # JPM: JPM_..._YYYY-MM-DD_...pdf
    jpm_match = re.search(r'(\d{4}-\d{2}-\d{2})', filename)
    if "JPM" in filename and jpm_match:
        return {"date": jpm_match.group(1), "source": "JPM", "year": int(jpm_match.group(1)[:4])}
    
    # BIS: r_qtYYMM.pdf
    bis_match = re.search(r'r_qt(\d{2})(\d{2})', filename)
    if bis_match:
        yy = bis_match.group(1)
        mm = bis_match.group(2)
        # Pivot year: 90-99 -> 1990-1999, 00-89 -> 2000-2089
        year = 1900 + int(yy) if int(yy) >= 90 else 2000 + int(yy)
        return {"date": f"{year}-{mm}-01", "source": "BIS", "year": year}

    # FT: ..._YYYY-MM-DD.json
    ft_match = re.search(r'(\d{4}-\d{2}-\d{2})', filename)
    if filename.endswith('.json') and ft_match:
        return {"date": ft_match.group(1), "source": "FT", "year": int(ft_match.group(1)[:4])}

    # FCIC
    if "Financial Crisis Enquiry Report" in filename:
        return {"date": "2011-01-01", "source": "FCIC", "year": 2011}

    return {"date": "1900-01-01", "source": "Unknown", "year": 1900}

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

def add_documents_with_retry(vector_store, batch, max_retries=5):
    """Add documents to vector store with retry logic for rate limits."""
    for attempt in range(max_retries):
        try:
            vector_store.add_documents(batch)
            return True
        except Exception as e:
            if "RateLimitError" in str(e) or "429" in str(e):
                wait_time = (2 ** attempt) * 1
                logger.warning(f"Rate limit hit. Retrying in {wait_time} seconds... (Attempt {attempt + 1}/{max_retries})")
                time.sleep(wait_time)
            else:
                logger.error(f"Error adding documents: {e}")
                raise e
    return False

def process_and_ingest():
    """Ingest files in a streaming fashion: Load -> Chunk -> Batch -> Ingest."""
    
    # 1. Setup
    abs_raw_dir = os.path.abspath(RAW_DATA_DIR)
    pdf_files = glob.glob(os.path.join(abs_raw_dir, "**/*.pdf"), recursive=True)
    json_files = glob.glob(os.path.join(abs_raw_dir, "**/*.json"), recursive=True)
    all_files = pdf_files + json_files
    
    if not all_files:
        logger.warning(f"No files found in {abs_raw_dir}")
        return

    processed_files = load_processed_files()
    new_files = [f for f in all_files if f not in processed_files]
    
    if not new_files:
        logger.info("No new files to process.")
        return
    
    logger.info(f"Found {len(new_files)} new files. Starting streaming ingestion...")

    # 2. Initialize Vector Store with local BGE embeddings
    logger.info("Loading BGE embeddings model (this may take a moment on first run)...")
    embeddings = HuggingFaceEmbeddings(
        model_name="BAAI/bge-large-en-v1.5",
        model_kwargs={'device': 'mps'},  # M2 Pro GPU acceleration
        encode_kwargs={'normalize_embeddings': True}
    )
    vector_store = Chroma(persist_directory=DB_DIR, embedding_function=embeddings)
    
    # 3. Processing Loop
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50,
        separators=["\\n\\n", "\\n", " ", ""]
    )
    
    batch_docs = []
    batch_files = []
    BATCH_SIZE = 100
    
    total_files = len(new_files)

    from langchain_core.documents import Document

    for i, file_path in enumerate(new_files):
        try:
            # Load single file
            file_docs = []
            if file_path.endswith('.pdf'):
                loader = PyPDFLoader(file_path)
                file_docs = loader.load()
                for doc in file_docs:
                    filename = os.path.basename(file_path)
                    meta = extract_metadata_from_filename(filename)
                    doc.metadata['filename'] = filename
                    doc.metadata['source'] = file_path
                    doc.metadata.update(meta)
                    logger.info(f"Extracted meta for {filename}: {meta}") # Debug
            
            elif file_path.endswith('.json'):
                with open(file_path, 'r') as f:
                    data = json.load(f)
                    title = data.get('title', '')
                    body = clean_html(data.get('bodyXML', ''))
                    standfirst = data.get('standfirst', '')
                    content = f"{title}\n\n{standfirst}\n\n{body}"
                    
                    doc = Document(
                        page_content=content,
                        metadata={
                            'filename': os.path.basename(file_path),
                            'source': file_path,
                            'title': title,
                            'type': 'json_article'
                        }
                    )
                    filename = os.path.basename(file_path)
                    meta = extract_metadata_from_filename(filename)
                    doc.metadata.update(meta)
                    file_docs = [doc]

            # Chunk single file
            if file_docs:
                chunks = text_splitter.split_documents(file_docs)
                batch_docs.extend(chunks)
                batch_files.append(file_path)
                
                # If batch is full, ingest
                if len(batch_docs) >= BATCH_SIZE:
                    logger.info(f"Ingesting batch of {len(batch_docs)} chunks (Processed {i+1}/{total_files} files)...")
                    if add_documents_with_retry(vector_store, batch_docs):
                        # Mark files as processed only after successful ingestion
                        processed_files.update(batch_files)
                        save_processed_files(processed_files)
                        batch_docs = []
                        batch_files = []
                        time.sleep(0.5) # Rate limit niceness
                    else:
                        logger.error("Failed to ingest batch. Skipping update of processed files.")

        except Exception as e:
            logger.error(f"Failed to process {file_path}: {e}")

    # 4. Final Flush
    if batch_docs:
        logger.info(f"Ingesting final batch of {len(batch_docs)} chunks...")
        if add_documents_with_retry(vector_store, batch_docs):
            processed_files.update(batch_files)
            save_processed_files(processed_files)
    
    logger.info("Ingestion complete.")

if __name__ == "__main__":
    os.makedirs(RAW_DATA_DIR, exist_ok=True)
    os.makedirs(DB_DIR, exist_ok=True)
    process_and_ingest()
