import os
import re
from datetime import datetime, date, timedelta
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_openai import OpenAIEmbeddings
from rag.reranker import Reranker
from rag.query_generator import QueryGenerator
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)

# Setup file logging for retrieval
log_dir = "rag/logs"
os.makedirs(log_dir, exist_ok=True)
file_handler = logging.FileHandler(os.path.join(log_dir, "retrieval.log"))
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
logger.addHandler(file_handler)

DB_DIR = "rag/data/chroma_db"

# Embedding configuration - must match ingestion
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "bge")  # "openai" or "bge"
OPENAI_EMBEDDING_MODEL = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-large")

class RAGRetriever:
    def __init__(self):
        # Initialize embeddings based on configuration
        # IMPORTANT: Must match the model used during ingestion
        if EMBEDDING_MODEL == "openai":
            logger.info(f"Loading OpenAI embeddings model: {OPENAI_EMBEDDING_MODEL}")
            self.embeddings = OpenAIEmbeddings(
                model=OPENAI_EMBEDDING_MODEL,
                # Dimensions: text-embedding-3-large = 3072
            )
        else:
            # Auto-detect device: CUDA > MPS > CPU
            import torch
            if torch.cuda.is_available():
                device = 'cuda'
            elif torch.backends.mps.is_available():
                device = 'mps'
            else:
                device = 'cpu'

            logger.info(f"Loading BGE embeddings model (local) on {device}...")
            self.embeddings = HuggingFaceEmbeddings(
                model_name="BAAI/bge-large-en-v1.5",
                model_kwargs={'device': device},
                encode_kwargs={'normalize_embeddings': True}
            )

        if os.path.exists(DB_DIR):
            self.vector_store = Chroma(persist_directory=DB_DIR, embedding_function=self.embeddings)
        else:
            logger.warning(f"ChromaDB not found at {DB_DIR}. RAG will return empty results.")
            self.vector_store = None

        # Initialize Reranker
        self.reranker = Reranker()

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
            # 1. MMR Search (Diversity at vector level)
            # Fetch more candidates for reranking and diversity filtering
            initial_k = k * 4
            docs = self.vector_store.max_marginal_relevance_search(
                query, k=initial_k, fetch_k=initial_k*2, filter=filter_metadata
            )
            
            # 2. Rerank results
            # Rerank all candidates to get quality scores
            reranked_docs = self.reranker.rerank(query, docs, top_k=initial_k)
            
            # 3. Source Diversity Filtering (Round Robin)
            # Group by source type
            source_buckets = {'JPM': [], 'BIS': [], 'FT': [], 'FCIC': [], 'Other': []}
            for doc in reranked_docs:
                src_path = doc.metadata.get('source', 'Other')
                if 'JPM' in src_path: key = 'JPM'
                elif 'BIS' in src_path: key = 'BIS'
                elif 'FT' in src_path: key = 'FT'
                elif 'Financial Crisis' in src_path: key = 'FCIC'
                else: key = 'Other'
                source_buckets[key].append(doc)
            
            # Interleave results
            final_docs = []
            keys = list(source_buckets.keys())
            
            # Continue until we have k docs or run out of candidates
            while len(final_docs) < k:
                added_this_round = False
                for key in keys:
                    if source_buckets[key] and len(final_docs) < k:
                        # Check if doc is already added (unlikely but safe)
                        doc = source_buckets[key].pop(0)
                        if doc not in final_docs:
                            final_docs.append(doc)
                            added_this_round = True
                
                if not added_this_round:
                    break
            
            # Format results
            context_list = []
            for doc in final_docs:
                source = doc.metadata.get('source', 'Unknown')
                page = doc.metadata.get('page', 0)
                date = doc.metadata.get('date', 'Unknown Date')
                content = doc.page_content
                context_list.append(f"[Source: {os.path.basename(source)}, Date: {date}, Page: {page}]\n{content}")
            
            # Log retrieval for verification
            logger.info(f"Query: {query}")
            logger.info(f"Retrieved {len(context_list)} chunks (Diversity Applied).")
            for i, ctx in enumerate(context_list):
                logger.info(f"Chunk {i+1}: {ctx[:100]}...")

            return context_list

        except Exception as e:
            logger.error(f"Error during retrieval: {e}")
            return []

    def get_context_multi_query(
        self,
        date: str,
        volatility: float,
        liquidity_factor: float,
        k: int = 5,
        use_hyde: bool = True
    ) -> List[str]:
        """
        SOTA retrieval using multi-query + HyDE approach.

        Args:
            date: Current simulation date
            volatility: Market volatility (0-1)
            liquidity_factor: Liquidity multiplier
            k: Final number of documents to return
            use_hyde: Whether to use HyDE for one of the queries

        Returns:
            List of diverse, relevant document strings
        """
        if not self.vector_store:
            return []

        try:
            # Parse current simulation date
            try:
                # Handle "Month Year" format (e.g., "September 2008")
                sim_date = datetime.strptime(date, "%B %Y").date()
                # Set to end of month to include all docs from that month
                # Actually, to be safe and avoid "future within month", let's treat "September 2008" 
                # as the *start* of the month for filtering if we want to be very strict, 
                # OR if the simulation step happens at the end of the week, we might want to include that week.
                # Given the granularity is "Month Year", let's assume we are IN that month.
                # To be safe: include docs up to the end of that month? 
                # Or better: The simulation steps are weekly. "September 2008" is the label for steps 36-39.
                # If we are in Week 1 of Sept, we shouldn't see Sept 30 news.
                # BUT, the input `date` is just "September 2008". 
                # Let's default to allowing everything up to the end of that month for now, 
                # as the resolution of the date string is low.
                # Ideally, we'd pass the specific date (YYYY-MM-DD).
                # For now, let's assume end of month to allow retrieving docs from that month.
                if sim_date.month == 12:
                    sim_date = sim_date.replace(day=31)
                else:
                    # Get last day of current month by going to 1st of next month and subtracting 1 day
                    next_month = sim_date.replace(month=sim_date.month+1, day=1)
                    sim_date = next_month - timedelta(days=1)
            except ValueError:
                # Fallback for other formats or if parsing fails
                logger.warning(f"Could not parse date '{date}', defaulting to 2008-12-31")
                sim_date = date(2008, 12, 31)

            # 1. Generate multiple queries based on market state
            queries = QueryGenerator.generate_market_queries(
                date, volatility, liquidity_factor, num_queries=3
            )

            # 2. Optionally add HyDE query
            if use_hyde:
                hyde_doc = QueryGenerator.generate_hyde_document(
                    date, volatility, liquidity_factor
                )
                queries.append(hyde_doc)

            # 3. Retrieve for each query
            all_docs = []
            seen_content = set()  # Deduplicate

            for query in queries:
                docs = self.vector_store.max_marginal_relevance_search(
                    query, k=k * 4, fetch_k=k * 8  # Retrieve more to account for filtering
                )
                for doc in docs:
                    # Deduplicate by content hash
                    content_hash = hash(doc.page_content[:200])
                    if content_hash not in seen_content:
                        seen_content.add(content_hash)
                        all_docs.append(doc)

            # 4. Apply temporal filtering - only docs from before or during simulation month
            all_docs = self._filter_by_date(all_docs, sim_date)
            logger.info(f"Multi-query retrieved {len(all_docs)} docs after temporal filtering (date <= {sim_date})")

            # 4. Rerank all candidates with the main query
            main_query = f"financial market conditions risks {date}"
            reranked_docs = self.reranker.rerank(main_query, all_docs, top_k=k * 3)

            # 5. Apply source diversity
            final_docs = self._apply_source_diversity(reranked_docs, k)

            # 6. Format results
            context_list = self._format_results(final_docs)

            # Log actual sources for verification
            sources = [os.path.basename(doc.metadata.get('source', 'Unknown')) for doc in final_docs]
            unique_sources = set(sources)
            logger.info(f"Final context: {len(context_list)} chunks from {len(unique_sources)} unique sources:")
            for src in sources:
                logger.info(f"  - {src}")

            return context_list

        except Exception as e:
            logger.error(f"Error in multi-query retrieval: {e}")
            return []

    def get_agent_context(
        self,
        bank_name: str,
        date: str,
        capital: float,
        liquidity: float,
        risk_score: float,
        volatility: float,
        liquidity_factor: float = 1.0,
        k: int = 3
    ) -> List[str]:
        """
        Get context tailored to a specific bank's situation.

        Args:
            bank_name: Name of the bank
            date: Current simulation date
            capital: Bank's capital
            liquidity: Bank's liquidity ratio
            risk_score: Bank's risk score
            risk_score: Bank's risk score
            volatility: Market volatility
            liquidity_factor: Global liquidity multiplier
            k: Number of documents to return

        Returns:
            List of relevant document strings for this bank
        """
        if not self.vector_store:
            return []

        try:
            # Parse current simulation date
            try:
                sim_date = datetime.strptime(date, "%B %Y").date()
                # Set to end of month
                if sim_date.month == 12:
                    sim_date = sim_date.replace(day=31)
                else:
                     # Get last day of current month
                     next_month = sim_date.replace(month=sim_date.month+1, day=1)
                     sim_date = next_month - timedelta(days=1)
            except ValueError:
                sim_date = date(2008, 12, 31)

            # 1. Generate agent-specific queries
            queries = QueryGenerator.generate_agent_queries(
                bank_name, date, capital, liquidity, risk_score, volatility, liquidity_factor
            )

            # 2. Retrieve for each query
            all_docs = []
            seen_content = set()

            for query in queries:
                docs = self.vector_store.max_marginal_relevance_search(
                    query, k=k * 3, fetch_k=k * 6  # Retrieve more to account for filtering
                )
                for doc in docs:
                    content_hash = hash(doc.page_content[:200])
                    if content_hash not in seen_content:
                        seen_content.add(content_hash)
                        all_docs.append(doc)

            # 3. Apply temporal filtering
            all_docs = self._filter_by_date(all_docs, sim_date)

            # 4. Rerank with agent context
            rerank_query = f"{bank_name} liquidity {liquidity:.0%} capital {capital}B risk management {date}"
            reranked_docs = self.reranker.rerank(rerank_query, all_docs, top_k=k * 2)

            # 4. Take top k
            final_docs = reranked_docs[:k]

            # 5. Format
            context_list = self._format_results(final_docs)

            # Log actual sources for verification
            sources = [os.path.basename(doc.metadata.get('source', 'Unknown')) for doc in final_docs]
            logger.info(f"Agent {bank_name}: Retrieved {len(context_list)} chunks from sources:")
            for src in sources:
                logger.info(f"  - {src}")

            return context_list

        except Exception as e:
            logger.error(f"Error in agent retrieval for {bank_name}: {e}")
            return []

    def _apply_source_diversity(self, docs, k: int):
        """Apply round-robin source diversity to documents."""
        source_buckets = {'JPM': [], 'BIS': [], 'FT': [], 'FCIC': [], 'Other': []}

        for doc in docs:
            src_path = doc.metadata.get('source', 'Other')
            if 'JPM' in src_path:
                key = 'JPM'
            elif 'BIS' in src_path:
                key = 'BIS'
            elif 'FT' in src_path:
                key = 'FT'
            elif 'Financial Crisis' in src_path:
                key = 'FCIC'
            else:
                key = 'Other'
            source_buckets[key].append(doc)

        # Interleave
        final_docs = []
        keys = list(source_buckets.keys())

        while len(final_docs) < k:
            added = False
            for key in keys:
                if source_buckets[key] and len(final_docs) < k:
                    final_docs.append(source_buckets[key].pop(0))
                    added = True
            if not added:
                break

        return final_docs

    def _extract_date_from_filename(self, filename: str) -> str:
        """Extract date from filename patterns."""
        # JPM pattern: JPM_..._2008-12-13_481961.pdf
        jpm_match = re.search(r'(\d{4}-\d{2}-\d{2})', filename)
        if jpm_match:
            return jpm_match.group(1)

        # BIS Quarterly pattern: r_qt0809.pdf (2008-09)
        bis_q_match = re.search(r'r_qt(\d{2})(\d{2})\.pdf', filename)
        if bis_q_match:
            year = bis_q_match.group(1)
            month = bis_q_match.group(2)
            # Handle Y2K
            year_full = f"20{year}" if int(year) < 50 else f"19{year}"
            return f"{year_full}-{month}"

        # BIS Annual pattern: ar99e.pdf (1999) or ar2008e.pdf
        bis_a_match = re.search(r'ar(\d{2,4})e?\.pdf', filename)
        if bis_a_match:
            year = bis_a_match.group(1)
            if len(year) == 2:
                year = f"20{year}" if int(year) < 50 else f"19{year}"
            return year

        # FT articles have date in metadata, fall back
        return None

    def _extract_date_from_filename(self, filename: str) -> Optional[date]:
        """Extract date object from filename patterns."""
        try:
            # JPM pattern: JPM_..._2008-12-13_481961.pdf
            jpm_match = re.search(r'(\d{4}-\d{2}-\d{2})', filename)
            if jpm_match:
                return datetime.strptime(jpm_match.group(1), "%Y-%m-%d").date()

            # BIS Quarterly pattern: r_qt0809.pdf (2008-09)
            bis_q_match = re.search(r'r_qt(\d{2})(\d{2})\.pdf', filename)
            if bis_q_match:
                year = bis_q_match.group(1)
                month = bis_q_match.group(2)
                # Handle Y2K
                year_full = int(f"20{year}") if int(year) < 50 else int(f"19{year}")
                # Default to end of month
                return date(year_full, int(month), 28) # Approximate end of month

            # BIS Annual pattern: ar99e.pdf (1999) or ar2008e.pdf
            bis_a_match = re.search(r'ar(\d{2,4})e?\.pdf', filename)
            if bis_a_match:
                year_str = bis_a_match.group(1)
                if len(year_str) == 2:
                    year = int(f"20{year_str}") if int(year_str) < 50 else int(f"19{year_str}")
                else:
                    year = int(year_str)
                return date(year, 12, 31) # Annual report = end of year

            # FT articles have date in metadata, fall back
            return None
        except Exception as e:
            logger.warning(f"Error extracting date from {filename}: {e}")
            return None

    def _filter_by_date(self, docs, max_date: date):
        """Filter documents to only include those from before or equal to max_date."""
        filtered = []
        # If max_date wasn't parsed correctly (e.g. it's just a year-end default), 
        # we might want to be careful. But assuming it's valid.
        
        # Handle case where max_date might be just a "Month Year" resolution mapped to start of month?
        # For now, we assume max_date is the cutoff (inclusive).
        
        for doc in docs:
            source = doc.metadata.get('source', '')
            filename = os.path.basename(source)
            
            # Try metadata first
            doc_date_str = doc.metadata.get('date', '')
            doc_date = None
            
            if doc_date_str and doc_date_str != 'Unknown Date':
                try:
                    # Try parsing standard formats
                    # FT often has YYYY-MM-DDTHH:MM:SS...
                    if 'T' in doc_date_str:
                        doc_date = datetime.strptime(doc_date_str.split('T')[0], "%Y-%m-%d").date()
                    else:
                        doc_date = datetime.strptime(doc_date_str, "%Y-%m-%d").date()
                except:
                    pass
            
            # Fallback to filename
            if not doc_date:
                doc_date = self._extract_date_from_filename(filename)
            
            if doc_date:
                # Compare dates
                # We want doc_date <= max_date
                # Note: If max_date is "September 2008" (mapped to Sept 1 or Sept 30?)
                # In the calling code, we need to decide. 
                # Let's assume calling code sets max_date to the END of the current simulation period.
                
                # Special case: If doc_date is just a year (annual report), it defaults to Dec 31.
                # If we are in Sept 2008, we should NOT see 2008 Annual Report (Dec 31).
                # So doc_date (2008-12-31) > max_date (2008-09-30) -> Filtered out. CORRECT.
                
                if doc_date <= max_date:
                    filtered.append(doc)
                else:
                    # logger.debug(f"Filtered out future doc: {filename} ({doc_date} > {max_date})")
                    pass
            else:
                # If no date found, include it? Or exclude?
                # Safer to include if uncertain, or exclude?
                # Let's include but log warning
                # logger.warning(f"No date found for {filename}, including by default.")
                filtered.append(doc)
                
        return filtered

    def _format_results(self, docs) -> List[str]:
        """Format documents into context strings."""
        context_list = []
        for doc in docs:
            source = doc.metadata.get('source', 'Unknown')
            filename = os.path.basename(source)
            page = doc.metadata.get('page', 0)

            # Try to get date from metadata, then from filename
            date_val = doc.metadata.get('date', '')
            if not date_val or date_val == 'Unknown Date':
                extracted = self._extract_date_from_filename(filename)
                date_val = extracted.strftime("%Y-%m-%d") if extracted else 'Unknown'

            content = doc.page_content
            context_list.append(
                f"[Source: {filename}, Date: {date_val}, Page: {page}]\n{content}"
            )
        return context_list

# Singleton instance for easy import
_retriever_instance = None

def _get_retriever():
    """Get or create singleton retriever instance."""
    global _retriever_instance
    if _retriever_instance is None:
        _retriever_instance = RAGRetriever()
    return _retriever_instance

def get_relevant_context(query, k=3, filter_metadata=None):
    """Legacy single-query retrieval."""
    return _get_retriever().get_relevant_context(query, k, filter_metadata)

def get_context_multi_query(date, volatility, liquidity_factor, k=5, use_hyde=True):
    """SOTA multi-query retrieval with HyDE."""
    return _get_retriever().get_context_multi_query(date, volatility, liquidity_factor, k, use_hyde)

def get_agent_context(bank_name, date, capital, liquidity, risk_score, volatility, liquidity_factor=1.0, k=3):
    """Agent-specific retrieval based on bank state."""
    return _get_retriever().get_agent_context(bank_name, date, capital, liquidity, risk_score, volatility, liquidity_factor, k)
