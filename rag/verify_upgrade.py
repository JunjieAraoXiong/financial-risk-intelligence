import os
import logging
from rag.retriever import get_relevant_context

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def verify_rag_upgrade():
    print("--- Verifying RAG Upgrade ---")
    
    # Test Query
    query = "What are the key market risks and outlook for October 2008?"
    print(f"Query: {query}")
    
    # Retrieve
    chunks = get_relevant_context(query, k=5)
    
    print(f"\nRetrieved {len(chunks)} chunks:")
    for i, chunk in enumerate(chunks):
        print(f"\n[Chunk {i+1}]")
        print(chunk[:300] + "...") # Print first 300 chars
        
        # Check for Source and Date in the formatted string
        # The retriever formats it as: [Source: ..., Date: ..., Page: ...]
        if "Date:" in chunk and "Source:" in chunk:
            print("✅ Metadata (Date/Source) present.")
        else:
            print("❌ Metadata MISSING.")

if __name__ == "__main__":
    verify_rag_upgrade()
