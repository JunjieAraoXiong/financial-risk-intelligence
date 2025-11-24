import logging
import torch
from sentence_transformers import CrossEncoder

logger = logging.getLogger(__name__)

class Reranker:
    def __init__(self, model_name="BAAI/bge-reranker-v2-m3"):
        """
        Initialize the Reranker with a Cross-Encoder model.
        """
        self.model_name = model_name

        # Auto-detect device: CUDA > MPS > CPU
        if torch.cuda.is_available():
            device = 'cuda'
        elif torch.backends.mps.is_available():
            device = 'mps'
        else:
            device = 'cpu'

        logger.info(f"Loading Reranker model: {model_name} on {device}")
        try:
            self.model = CrossEncoder(model_name, device=device)
            logger.info("Reranker model loaded successfully.")
        except Exception as e:
            logger.error(f"Failed to load Reranker model: {e}")
            self.model = None

    def rerank(self, query, documents, top_k=5):
        """
        Rerank a list of documents based on the query.

        Args:
            query (str): The search query.
            documents (list): List of document strings or objects. 
                              If objects, they must have a 'page_content' attribute.
            top_k (int): Number of top results to return.

        Returns:
            list: Top-k reranked documents.
        """
        if not self.model or not documents:
            return documents[:top_k]

        # Prepare pairs for Cross-Encoder
        # Handle both string documents and Document objects (from LangChain)
        doc_contents = []
        for doc in documents:
            if isinstance(doc, str):
                doc_contents.append(doc)
            elif hasattr(doc, 'page_content'):
                doc_contents.append(doc.page_content)
            else:
                # Fallback for unknown types
                doc_contents.append(str(doc))

        pairs = [[query, doc_text] for doc_text in doc_contents]

        try:
            scores = self.model.predict(pairs)

            # Log score distribution for debugging
            if len(scores) > 0:
                logger.debug(f"Reranker scores - min: {min(scores):.3f}, max: {max(scores):.3f}, mean: {sum(scores)/len(scores):.3f}")

            # Combine docs with scores
            doc_score_pairs = list(zip(documents, scores))

            # Sort by score descending
            doc_score_pairs.sort(key=lambda x: x[1], reverse=True)

            # Log top scores for analysis
            if len(doc_score_pairs) >= 3:
                logger.debug(f"Top 3 reranker scores: {[f'{s:.3f}' for _, s in doc_score_pairs[:3]]}")

            # Return top_k documents
            reranked_docs = [doc for doc, score in doc_score_pairs[:top_k]]
            return reranked_docs

        except Exception as e:
            logger.error(f"Error during reranking: {e}")
            return documents[:top_k]
