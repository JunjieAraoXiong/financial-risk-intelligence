import os
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
import logging

logger = logging.getLogger(__name__)

DB_DIR = "rag/data/chroma_db"

class RAGRetriever:
    def __init__(self):
        self.embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
        if os.path.exists(DB_DIR):
            self.vector_store = Chroma(persist_directory=DB_DIR, embedding_function=self.embeddings)
        else:
            logger.warning(f"ChromaDB not found at {DB_DIR}. RAG will return empty results.")
            self.vector_store = None

    def get_relevant_context(self, query, k=3, filter_metadata=None):
        """
        Retrieve top-k relevant chunks for a query.
        
        Args:
            query (str): The search query.
            k (int): Number of documents to retrieve.
            filter_metadata (dict): Optional metadata filter (e.g., {'year': 2008}).
            
        Returns:
            list: List of document strings.
        """
        if not self.vector_store:
            return []

        try:
            # Perform similarity search
            # Note: Chroma filter syntax might vary, basic usage is filter=dict
            docs = self.vector_store.similarity_search(query, k=k, filter=filter_metadata)
            
            # Format results
            context_list = []
            for doc in docs:
                source = doc.metadata.get('source', 'Unknown')
                page = doc.metadata.get('page', 0)
                content = doc.page_content
                context_list.append(f"[Source: {os.path.basename(source)}, Page: {page}]\n{content}")
            
            return context_list

        except Exception as e:
            logger.error(f"Error during retrieval: {e}")
            return []

# Singleton instance for easy import
_retriever_instance = None

def get_relevant_context(query, k=3, filter_metadata=None):
    global _retriever_instance
    if _retriever_instance is None:
        _retriever_instance = RAGRetriever()
    return _retriever_instance.get_relevant_context(query, k, filter_metadata)
