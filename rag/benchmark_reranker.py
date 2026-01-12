#!/usr/bin/env python3
"""
Benchmark script for evaluating BGE Reranker effectiveness.

Compares retrieval quality and latency with and without the reranker
to determine if the reranker provides sufficient value for its cost.

Metrics measured:
- Retrieval latency (ms) with and without reranker
- Rank correlation between approaches (Spearman's rho)
- Relevance estimation based on keyword overlap
- Source diversity analysis

Usage:
    python rag/benchmark_reranker.py
    python rag/benchmark_reranker.py --mock  # Use mock data if ChromaDB unavailable
"""

import os
import sys
import time
import logging
import argparse
import random
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from collections import defaultdict
import statistics

import torch
from scipy import stats as scipy_stats

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rag.reranker import Reranker

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Suppress noisy logs during benchmarking
logging.getLogger('sentence_transformers').setLevel(logging.WARNING)
logging.getLogger('transformers').setLevel(logging.WARNING)

DB_DIR = "rag/data/chroma_db"

# Mock documents for testing when ChromaDB is unavailable
# These simulate real financial crisis documents
MOCK_DOCUMENTS = [
    {
        "content": """EMERGENCY MARKET UPDATE - September 15, 2008
        Lehman Brothers has filed for Chapter 11 bankruptcy, the largest bankruptcy filing in U.S. history.
        Markets are in severe distress with the VIX spiking above 80. Interbank lending has effectively frozen.
        The Federal Reserve is considering emergency liquidity facilities. Counterparty risk is at extreme levels.
        All financial institutions should take immediate defensive action to preserve liquidity and capital.""",
        "source": "JPM_Weekly_2008-09-15.pdf",
        "date": "2008-09-15"
    },
    {
        "content": """The collapse of Lehman Brothers triggered a global liquidity crisis. Credit default swap spreads widened
        dramatically. The commercial paper market effectively shut down with issuers unable to roll over debt.
        Central banks worldwide are coordinating emergency interventions. Bank failures and forced mergers
        are occurring across major financial centers. Systemic risk has reached unprecedented levels.""",
        "source": "BIS_Quarterly_2008-09.pdf",
        "date": "2008-09-28"
    },
    {
        "content": """The week of September 15, 2008 marked the peak of the financial crisis. Following Lehman's bankruptcy,
        AIG required emergency government assistance to prevent collapse. Money market funds broke the buck
        triggering massive redemptions. The Treasury implemented the TARP program to recapitalize banks.
        The crisis demonstrated the severe consequences of inadequate liquidity management and excessive leverage.""",
        "source": "FCIC_Report.pdf",
        "date": "2008-09-20"
    },
    {
        "content": """Global stock markets plunged as panic spread following Lehman's collapse. The Fed and Treasury are
        working on unprecedented intervention measures. Goldman Sachs and Morgan Stanley face severe pressure.
        Banks worldwide are hoarding liquidity. The TED spread has reached 3% indicating extreme stress in
        interbank markets. Investor confidence has collapsed with fears of systemic banking failure.""",
        "source": "FT_Article_2008-09-18.json",
        "date": "2008-09-18"
    },
    {
        "content": """Bear Stearns collapsed over the weekend and was acquired by JPMorgan Chase with Federal Reserve backing.
        The Fed opened the discount window to investment banks for the first time since the Great Depression.
        This marks a significant escalation in the credit crisis. Market volatility remains elevated with
        concerns about additional failures in the financial sector.""",
        "source": "JPM_Weekly_2008-03-17.pdf",
        "date": "2008-03-17"
    },
    {
        "content": """Subprime mortgage defaults have accelerated dramatically in Q3 2007. CDO writedowns at major banks
        are approaching $50 billion. Housing prices continue to decline with foreclosures at record levels.
        Credit rating agencies are downgrading thousands of mortgage-backed securities. The contagion from
        subprime is spreading to prime mortgage markets.""",
        "source": "JPM_Weekly_2007-10-15.pdf",
        "date": "2007-10-15"
    },
    {
        "content": """AIG received an $85 billion emergency loan from the Federal Reserve to prevent bankruptcy. The insurance
        giant's exposure to credit default swaps on mortgage-backed securities threatened to trigger a cascade
        of failures across the financial system. Counterparty exposure to AIG spans virtually every major bank.
        The bailout is the largest single company rescue in history.""",
        "source": "FT_Article_2008-09-16.json",
        "date": "2008-09-16"
    },
    {
        "content": """Washington Mutual was seized by the FDIC in the largest bank failure in U.S. history. JPMorgan Chase
        acquired WaMu's banking operations. Wachovia is also in severe distress and seeking a merger partner.
        The FDIC deposit insurance fund is under significant strain. Regional bank failures are accelerating.""",
        "source": "JPM_Weekly_2008-09-26.pdf",
        "date": "2008-09-26"
    },
    {
        "content": """Market conditions remain favorable with steady economic growth. Credit spreads are tight and
        liquidity is abundant. Banking sector profitability is strong with low default rates.
        Current outlook supports maintaining existing positions and strategies. Consumer confidence
        is elevated and housing market fundamentals appear solid.""",
        "source": "JPM_Weekly_2007-02-12.pdf",
        "date": "2007-02-12"
    },
    {
        "content": """The global banking system showed resilience in 2006 with strong capital ratios across major
        institutions. Credit conditions are healthy with adequate lending standards. Economic indicators
        suggest continued stable growth in the near term. Basel II implementation is proceeding smoothly
        and banks are well-positioned for the new regulatory environment.""",
        "source": "BIS_Annual_2006.pdf",
        "date": "2006-12-31"
    },
    {
        "content": """The TARP program authorized $700 billion for troubled asset purchases and bank recapitalization.
        Treasury Secretary Paulson announced the Capital Purchase Program to inject equity into banks.
        Nine major banks including JPMorgan, Bank of America, Citigroup, and Wells Fargo received initial
        capital injections. The government's intervention aims to restore confidence in the banking system.""",
        "source": "BIS_Quarterly_2008-12.pdf",
        "date": "2008-10-14"
    },
    {
        "content": """LIBOR-OIS spreads have widened to 350 basis points, indicating severe stress in interbank lending.
        Banks are refusing to lend to each other beyond overnight maturities. The Federal Reserve has
        expanded the Term Auction Facility and created new lending programs including the PDCF for
        primary dealers. Dollar funding shortages are acute in overseas markets.""",
        "source": "BIS_Quarterly_2008-09.pdf",
        "date": "2008-09-22"
    },
    {
        "content": """Credit default swap spreads on major banks have reached record levels. CDS spreads on Goldman Sachs,
        Morgan Stanley, and Citigroup all exceed 500 basis points. The cost of credit protection reflects
        severe doubts about bank solvency. Counterparty risk in the CDS market itself is a growing concern
        as AIG's troubles highlighted interconnected exposures.""",
        "source": "FT_Article_2008-09-17.json",
        "date": "2008-09-17"
    },
    {
        "content": """Risk management practices at major financial institutions are being scrutinized. Excessive leverage,
        inadequate capital buffers, and overreliance on short-term funding contributed to the crisis.
        Value-at-Risk models failed to capture tail risks. Stress testing methodologies proved inadequate
        for extreme market conditions. Banks are now focused on deleveraging and raising capital.""",
        "source": "BIS_Annual_2008.pdf",
        "date": "2008-12-31"
    },
    {
        "content": """The Financial Crisis Inquiry Commission identified several causes of the 2008 crisis: widespread
        failures in financial regulation, dramatic breakdowns in corporate governance, an explosive mix
        of excessive borrowing and risk by households and Wall Street, key policy makers ill-prepared
        for the crisis, and systemic breaches in accountability and ethics at all levels.""",
        "source": "FCIC_Report.pdf",
        "date": "2011-01-27"
    },
    {
        "content": """Merrill Lynch agreed to be acquired by Bank of America for $50 billion as the investment bank
        faced potential collapse. The deal was announced hours before Lehman's bankruptcy filing.
        CEO John Thain negotiated the sale as counterparties pulled back from Merrill. The transaction
        marked the end of Merrill Lynch as an independent firm after 94 years.""",
        "source": "FT_Article_2008-09-14.json",
        "date": "2008-09-14"
    },
    {
        "content": """Fannie Mae and Freddie Mac were placed into conservatorship by the Federal Housing Finance Agency.
        The government-sponsored enterprises held or guaranteed $5.4 trillion in mortgages. Losses on
        mortgage exposures had depleted their capital. The Treasury committed to providing unlimited
        support to prevent their failure, which would have devastating consequences for housing finance.""",
        "source": "JPM_Weekly_2008-09-08.pdf",
        "date": "2008-09-08"
    },
    {
        "content": """Northern Rock experienced the first bank run in Britain in over 150 years. Depositors queued
        outside branches to withdraw savings after the Bank of England provided emergency liquidity support.
        The run demonstrated how quickly confidence can evaporate and how social media accelerates panic.
        The UK government ultimately nationalized Northern Rock in February 2008.""",
        "source": "BIS_Annual_2007.pdf",
        "date": "2007-09-14"
    },
    {
        "content": """Money market funds are experiencing unprecedented redemption requests following Reserve Primary Fund
        breaking the buck. The fund held Lehman Brothers commercial paper and suffered losses that pushed
        its net asset value below $1.00. The Treasury announced a temporary guarantee program for money
        market funds to stem the outflows threatening short-term credit markets.""",
        "source": "JPM_Weekly_2008-09-19.pdf",
        "date": "2008-09-19"
    },
    {
        "content": """The VIX volatility index has spiked to 80, the highest level in its history. Equity markets have
        experienced multiple days of 5%+ declines. Correlation across asset classes has increased to near 1
        as investors flee to safety. Treasury yields on short-term bills have turned negative as demand
        for safe assets overwhelms supply. Market functioning is severely impaired.""",
        "source": "FT_Article_2008-10-10.json",
        "date": "2008-10-10"
    }
]


class MockDocument:
    """Mock document class to simulate LangChain Document objects."""
    def __init__(self, content: str, metadata: Dict):
        self.page_content = content
        self.metadata = metadata

# Test queries covering different financial scenarios and market regimes
TEST_QUERIES = [
    # Crisis-related queries
    "Lehman Brothers bankruptcy September 2008 financial crisis",
    "AIG bailout government intervention systemic risk",
    "Bear Stearns hedge fund collapse liquidity crisis",
    "subprime mortgage crisis CDO writedowns MBS losses",
    "credit freeze commercial paper LIBOR TED spread",
    "Fannie Mae Freddie Mac conservatorship mortgage crisis",
    "Washington Mutual bank failure FDIC seizure",
    "interbank lending freeze counterparty risk contagion",

    # Risk management queries
    "liquidity management crisis funding strategies",
    "capital raising dilution bank recapitalization",
    "credit risk assessment default probability",
    "counterparty exposure derivatives CDS",
    "stress testing scenarios bank capital adequacy",

    # Market condition queries
    "market volatility VIX index equity decline",
    "credit spreads widening investment grade bonds",
    "short-term funding markets commercial paper rates",
    "Federal Reserve emergency lending TAF PDCF",

    # Historical context queries
    "financial crisis history banking panics",
    "bank regulation reform Basel requirements",
    "systemic risk monitoring early warning",
    "contagion effects cross-border spillovers",

    # Specific entity queries
    "JPMorgan Chase risk management practices",
    "Goldman Sachs trading losses 2008",
    "Morgan Stanley liquidity position",
    "Merrill Lynch Bank of America merger",
    "Citigroup government support TARP"
]

# Expected keywords for relevance estimation (query -> relevant terms)
RELEVANCE_KEYWORDS = {
    "Lehman Brothers bankruptcy": ["lehman", "bankruptcy", "september", "2008", "crisis", "failure"],
    "AIG bailout": ["aig", "bailout", "government", "insurance", "systemic"],
    "Bear Stearns": ["bear", "stearns", "hedge", "fund", "collapse"],
    "subprime mortgage": ["subprime", "mortgage", "cdo", "mbs", "writedown"],
    "credit freeze": ["credit", "freeze", "libor", "ted", "spread"],
    "liquidity management": ["liquidity", "funding", "management", "crisis"],
    "Federal Reserve": ["federal", "reserve", "fed", "lending", "emergency"],
}


@dataclass
class BenchmarkResult:
    """Stores results for a single query benchmark."""
    query: str
    embedding_latency_ms: float
    rerank_latency_ms: float
    total_latency_with_rerank_ms: float
    total_latency_without_rerank_ms: float
    rerank_overhead_ms: float
    rerank_overhead_pct: float
    rank_correlation: float
    top_k_overlap: float
    relevance_score_with_rerank: float
    relevance_score_without_rerank: float
    relevance_improvement: float
    num_candidates: int


class RerankerBenchmark:
    """Benchmark suite for evaluating reranker effectiveness."""

    def __init__(self, k: int = 5, candidate_multiplier: int = 4, use_mock: bool = False):
        """
        Initialize benchmark.

        Args:
            k: Number of final results to return
            candidate_multiplier: How many more candidates to fetch for reranking
            use_mock: Use mock documents instead of ChromaDB (for testing without DB)
        """
        self.k = k
        self.candidate_multiplier = candidate_multiplier
        self.initial_k = k * candidate_multiplier
        self.use_mock = use_mock
        self.vector_store = None
        self.embeddings = None

        # Detect device
        if torch.cuda.is_available():
            self.device = 'cuda'
        elif torch.backends.mps.is_available():
            self.device = 'mps'
        else:
            self.device = 'cpu'
        logger.info(f"Using device: {self.device}")

        # Initialize vector store if not in mock mode
        if not use_mock:
            try:
                from langchain_community.vectorstores import Chroma
                from langchain_community.embeddings import HuggingFaceEmbeddings

                # Initialize embedding model
                logger.info("Loading embedding model...")
                self.embeddings = HuggingFaceEmbeddings(
                    model_name="BAAI/bge-large-en-v1.5",
                    model_kwargs={'device': self.device},
                    encode_kwargs={'normalize_embeddings': True}
                )

                # Load vector store
                logger.info(f"Loading vector store from {DB_DIR}...")
                if not os.path.exists(DB_DIR):
                    logger.warning(f"ChromaDB not found at {DB_DIR}, switching to mock mode")
                    self.use_mock = True
                else:
                    self.vector_store = Chroma(
                        persist_directory=DB_DIR,
                        embedding_function=self.embeddings
                    )
            except Exception as e:
                logger.warning(f"Failed to initialize ChromaDB: {e}")
                logger.warning("Switching to mock mode")
                self.use_mock = True

        if self.use_mock:
            logger.info("Using MOCK MODE with synthetic documents")
            # Create mock documents
            self.mock_docs = [
                MockDocument(doc["content"], {"source": doc["source"], "date": doc["date"], "page": 1})
                for doc in MOCK_DOCUMENTS
            ]

        # Initialize reranker
        logger.info("Loading reranker model...")
        self.reranker = Reranker()

        # Warmup models (first inference is slower)
        self._warmup()

    def _warmup(self):
        """Warmup models to get accurate timing."""
        logger.info("Warming up models...")
        warmup_query = "financial crisis 2008"

        if self.use_mock:
            # Warmup reranker with mock docs
            _ = self.reranker.rerank(warmup_query, self.mock_docs[:10], top_k=5)
        else:
            # Warmup embedding search
            _ = self.vector_store.similarity_search(warmup_query, k=5)

            # Warmup reranker
            docs = self.vector_store.similarity_search(warmup_query, k=10)
            _ = self.reranker.rerank(warmup_query, docs, top_k=5)

        logger.info("Warmup complete.")

    def _get_mock_candidates(self, query: str, num_candidates: int) -> List[MockDocument]:
        """
        Get mock candidates with simulated relevance ordering.
        Simulates embedding search by doing keyword matching to create
        a reasonable baseline ordering.
        """
        query_lower = query.lower()
        query_words = set(query_lower.split())

        # Score documents by keyword overlap (simulating embedding similarity)
        doc_scores = []
        for doc in self.mock_docs:
            content_lower = doc.page_content.lower()
            # Count matching words
            score = sum(1 for word in query_words if word in content_lower)
            # Add random noise to simulate embedding imperfection
            score += random.random() * 0.5
            doc_scores.append((doc, score))

        # Sort by score descending
        doc_scores.sort(key=lambda x: x[1], reverse=True)

        # Return top candidates
        return [doc for doc, score in doc_scores[:num_candidates]]

    def _estimate_relevance(self, query: str, docs: List) -> float:
        """
        Estimate relevance using keyword overlap heuristic.

        A simple but effective proxy for relevance when we don't have
        gold labels. Checks for presence of query-related keywords.
        """
        if not docs:
            return 0.0

        query_lower = query.lower()

        # Find matching keyword set
        keywords = []
        for key, kw_list in RELEVANCE_KEYWORDS.items():
            if key.lower() in query_lower:
                keywords = kw_list
                break

        # Fallback: use query words as keywords
        if not keywords:
            keywords = [w.lower() for w in query.split() if len(w) > 3]

        if not keywords:
            return 0.5  # Neutral score if no keywords

        # Calculate average keyword presence across docs
        scores = []
        for doc in docs:
            content = doc.page_content.lower() if hasattr(doc, 'page_content') else str(doc).lower()
            present = sum(1 for kw in keywords if kw in content)
            scores.append(present / len(keywords))

        return statistics.mean(scores) if scores else 0.0

    def _get_doc_id(self, doc) -> str:
        """Get unique identifier for a document."""
        if hasattr(doc, 'page_content'):
            return hash(doc.page_content[:200])
        return hash(str(doc)[:200])

    def benchmark_query(self, query: str) -> BenchmarkResult:
        """
        Run benchmark for a single query.

        Compares retrieval with and without reranking, measuring:
        - Latency for each approach
        - Rank correlation between results
        - Estimated relevance improvement
        """
        # Step 1: Get candidates (embedding search or mock)
        start_embed = time.perf_counter()
        if self.use_mock:
            candidates = self._get_mock_candidates(query, self.initial_k)
            # Simulate embedding latency for mock mode (based on typical times)
            embed_time = 50 + random.random() * 20  # 50-70ms simulated
        else:
            candidates = self.vector_store.similarity_search(query, k=self.initial_k)
            embed_time = (time.perf_counter() - start_embed) * 1000

        if not candidates:
            logger.warning(f"No candidates found for query: {query}")
            return BenchmarkResult(
                query=query,
                embedding_latency_ms=embed_time,
                rerank_latency_ms=0,
                total_latency_with_rerank_ms=embed_time,
                total_latency_without_rerank_ms=embed_time,
                rerank_overhead_ms=0,
                rerank_overhead_pct=0,
                rank_correlation=1.0,
                top_k_overlap=1.0,
                relevance_score_with_rerank=0,
                relevance_score_without_rerank=0,
                relevance_improvement=0,
                num_candidates=0
            )

        # Step 2: Without reranker - just take top k from embedding search
        top_k_without_rerank = candidates[:self.k]

        # Step 3: With reranker
        start_rerank = time.perf_counter()
        top_k_with_rerank = self.reranker.rerank(query, candidates, top_k=self.k)
        rerank_time = (time.perf_counter() - start_rerank) * 1000

        # Calculate metrics
        total_with_rerank = embed_time + rerank_time
        total_without_rerank = embed_time
        rerank_overhead = rerank_time
        rerank_overhead_pct = (rerank_time / total_without_rerank) * 100 if total_without_rerank > 0 else 0

        # Rank correlation: compare position of documents in both rankings
        without_ids = [self._get_doc_id(d) for d in candidates[:self.k * 2]]  # Extended for correlation
        with_ids = [self._get_doc_id(d) for d in top_k_with_rerank]

        # Build rank mappings
        without_ranks = {doc_id: i for i, doc_id in enumerate(without_ids)}
        with_ranks = []
        common_ids = []
        for i, doc_id in enumerate(with_ids):
            if doc_id in without_ranks:
                common_ids.append(doc_id)
                with_ranks.append(i)

        if len(common_ids) >= 3:
            without_ranks_for_corr = [without_ranks[doc_id] for doc_id in common_ids]
            correlation, _ = scipy_stats.spearmanr(without_ranks_for_corr, with_ranks)
            if correlation is None or str(correlation) == 'nan':
                correlation = 0.0
        else:
            correlation = 0.0

        # Top-k overlap: what fraction of top-k results are the same?
        without_set = set(self._get_doc_id(d) for d in top_k_without_rerank)
        with_set = set(self._get_doc_id(d) for d in top_k_with_rerank)
        overlap = len(without_set & with_set) / self.k if self.k > 0 else 0

        # Relevance estimation
        relevance_with = self._estimate_relevance(query, top_k_with_rerank)
        relevance_without = self._estimate_relevance(query, top_k_without_rerank)
        relevance_improvement = relevance_with - relevance_without

        return BenchmarkResult(
            query=query,
            embedding_latency_ms=embed_time,
            rerank_latency_ms=rerank_time,
            total_latency_with_rerank_ms=total_with_rerank,
            total_latency_without_rerank_ms=total_without_rerank,
            rerank_overhead_ms=rerank_overhead,
            rerank_overhead_pct=rerank_overhead_pct,
            rank_correlation=correlation,
            top_k_overlap=overlap,
            relevance_score_with_rerank=relevance_with,
            relevance_score_without_rerank=relevance_without,
            relevance_improvement=relevance_improvement,
            num_candidates=len(candidates)
        )

    def run_benchmark(self, queries: List[str] = None) -> Dict:
        """
        Run full benchmark suite.

        Args:
            queries: List of queries to test (defaults to TEST_QUERIES)

        Returns:
            Dictionary with aggregate statistics and individual results
        """
        if queries is None:
            queries = TEST_QUERIES

        logger.info(f"Running benchmark with {len(queries)} queries...")
        results = []

        for i, query in enumerate(queries):
            logger.info(f"[{i+1}/{len(queries)}] Testing: {query[:50]}...")
            result = self.benchmark_query(query)
            results.append(result)

        # Calculate aggregate statistics
        embed_latencies = [r.embedding_latency_ms for r in results]
        rerank_latencies = [r.rerank_latency_ms for r in results]
        total_with = [r.total_latency_with_rerank_ms for r in results]
        total_without = [r.total_latency_without_rerank_ms for r in results]
        overhead_pcts = [r.rerank_overhead_pct for r in results]
        correlations = [r.rank_correlation for r in results if r.rank_correlation != 0]
        overlaps = [r.top_k_overlap for r in results]
        relevance_improvements = [r.relevance_improvement for r in results]
        relevance_with = [r.relevance_score_with_rerank for r in results]
        relevance_without = [r.relevance_score_without_rerank for r in results]

        stats = {
            'num_queries': len(queries),
            'k': self.k,
            'candidate_multiplier': self.candidate_multiplier,
            'mode': 'mock' if self.use_mock else 'chromadb',
            'latency': {
                'embedding_mean_ms': statistics.mean(embed_latencies),
                'embedding_std_ms': statistics.stdev(embed_latencies) if len(embed_latencies) > 1 else 0,
                'rerank_mean_ms': statistics.mean(rerank_latencies),
                'rerank_std_ms': statistics.stdev(rerank_latencies) if len(rerank_latencies) > 1 else 0,
                'total_with_rerank_mean_ms': statistics.mean(total_with),
                'total_without_rerank_mean_ms': statistics.mean(total_without),
                'overhead_mean_pct': statistics.mean(overhead_pcts),
                'overhead_std_pct': statistics.stdev(overhead_pcts) if len(overhead_pcts) > 1 else 0,
            },
            'rank_analysis': {
                'spearman_correlation_mean': statistics.mean(correlations) if correlations else 0,
                'spearman_correlation_std': statistics.stdev(correlations) if len(correlations) > 1 else 0,
                'top_k_overlap_mean': statistics.mean(overlaps),
                'top_k_overlap_std': statistics.stdev(overlaps) if len(overlaps) > 1 else 0,
            },
            'relevance': {
                'with_rerank_mean': statistics.mean(relevance_with),
                'without_rerank_mean': statistics.mean(relevance_without),
                'improvement_mean': statistics.mean(relevance_improvements),
                'improvement_std': statistics.stdev(relevance_improvements) if len(relevance_improvements) > 1 else 0,
                'queries_improved': sum(1 for r in relevance_improvements if r > 0),
                'queries_unchanged': sum(1 for r in relevance_improvements if r == 0),
                'queries_degraded': sum(1 for r in relevance_improvements if r < 0),
            },
            'individual_results': [
                {
                    'query': r.query,
                    'embed_ms': round(r.embedding_latency_ms, 1),
                    'rerank_ms': round(r.rerank_latency_ms, 1),
                    'overhead_pct': round(r.rerank_overhead_pct, 1),
                    'correlation': round(r.rank_correlation, 3),
                    'overlap': round(r.top_k_overlap, 2),
                    'relevance_improvement': round(r.relevance_improvement, 3),
                }
                for r in results
            ]
        }

        return stats

    def generate_report(self, stats: Dict) -> str:
        """Generate human-readable benchmark report."""
        report = []
        report.append("=" * 70)
        report.append("BGE RERANKER BENCHMARK REPORT")
        report.append("=" * 70)
        report.append("")
        mode = stats.get('mode', 'unknown')
        if mode == 'mock':
            report.append("NOTE: Running in MOCK MODE (simulated documents)")
            report.append("      Reranker latency is real, but embedding latency is simulated.")
            report.append("")
        report.append(f"Configuration:")
        report.append(f"  - Mode: {mode.upper()}")
        report.append(f"  - Queries tested: {stats['num_queries']}")
        report.append(f"  - Top-k results: {stats['k']}")
        report.append(f"  - Candidate multiplier: {stats['candidate_multiplier']}x")
        report.append(f"  - Total candidates per query: {stats['k'] * stats['candidate_multiplier']}")
        report.append("")

        report.append("-" * 70)
        report.append("LATENCY ANALYSIS")
        report.append("-" * 70)
        lat = stats['latency']
        report.append(f"  Embedding search:    {lat['embedding_mean_ms']:.1f} +/- {lat['embedding_std_ms']:.1f} ms")
        report.append(f"  Reranker:           {lat['rerank_mean_ms']:.1f} +/- {lat['rerank_std_ms']:.1f} ms")
        report.append(f"  Total (with rerank): {lat['total_with_rerank_mean_ms']:.1f} ms")
        report.append(f"  Total (no rerank):   {lat['total_without_rerank_mean_ms']:.1f} ms")
        report.append(f"  Rerank overhead:     {lat['overhead_mean_pct']:.1f}% +/- {lat['overhead_std_pct']:.1f}%")
        report.append("")

        report.append("-" * 70)
        report.append("RANK ANALYSIS")
        report.append("-" * 70)
        rank = stats['rank_analysis']
        report.append(f"  Spearman correlation: {rank['spearman_correlation_mean']:.3f} +/- {rank['spearman_correlation_std']:.3f}")
        report.append(f"  Top-k overlap:        {rank['top_k_overlap_mean']:.1%} +/- {rank['top_k_overlap_std']:.1%}")
        report.append("")
        report.append("  Interpretation:")
        if rank['spearman_correlation_mean'] > 0.8:
            report.append("    - High correlation: reranker makes minor adjustments")
        elif rank['spearman_correlation_mean'] > 0.5:
            report.append("    - Moderate correlation: reranker makes meaningful reorderings")
        else:
            report.append("    - Low correlation: reranker significantly changes rankings")
        report.append("")

        report.append("-" * 70)
        report.append("RELEVANCE ANALYSIS (keyword-based estimation)")
        report.append("-" * 70)
        rel = stats['relevance']
        report.append(f"  With reranker:    {rel['with_rerank_mean']:.3f}")
        report.append(f"  Without reranker: {rel['without_rerank_mean']:.3f}")
        report.append(f"  Improvement:      {rel['improvement_mean']:+.3f} +/- {rel['improvement_std']:.3f}")
        report.append("")
        report.append(f"  Queries improved:  {rel['queries_improved']}/{stats['num_queries']}")
        report.append(f"  Queries unchanged: {rel['queries_unchanged']}/{stats['num_queries']}")
        report.append(f"  Queries degraded:  {rel['queries_degraded']}/{stats['num_queries']}")
        report.append("")

        report.append("-" * 70)
        report.append("RECOMMENDATION")
        report.append("-" * 70)

        # Generate recommendation based on metrics
        recommendation = self._generate_recommendation(stats)
        for line in recommendation:
            report.append(line)

        report.append("")
        report.append("=" * 70)
        report.append("DETAILED RESULTS BY QUERY")
        report.append("=" * 70)
        report.append("")
        report.append(f"{'Query':<45} {'Embed':>7} {'Rerank':>7} {'Overhead':>8} {'Improve':>8}")
        report.append("-" * 80)

        for r in stats['individual_results']:
            query_short = r['query'][:42] + "..." if len(r['query']) > 45 else r['query']
            report.append(f"{query_short:<45} {r['embed_ms']:>6.0f}ms {r['rerank_ms']:>6.0f}ms {r['overhead_pct']:>7.0f}% {r['relevance_improvement']:>+7.3f}")

        return "\n".join(report)

    def _generate_recommendation(self, stats: Dict) -> List[str]:
        """Generate recommendation based on benchmark results."""
        lines = []
        lat = stats['latency']
        rel = stats['relevance']
        rank = stats['rank_analysis']

        # Decision criteria
        significant_improvement = rel['improvement_mean'] > 0.02  # >2% relevance improvement
        marginal_improvement = rel['improvement_mean'] > 0.005   # >0.5% improvement
        acceptable_overhead = lat['overhead_mean_pct'] < 100     # Less than 2x latency
        low_overhead = lat['overhead_mean_pct'] < 50             # Less than 1.5x latency
        mostly_improves = rel['queries_improved'] > rel['queries_degraded']
        changes_ranking = rank['top_k_overlap_mean'] < 0.8       # Changes >20% of results

        if significant_improvement and acceptable_overhead:
            lines.append("  RECOMMENDATION: KEEP RERANKER (Significant Benefit)")
            lines.append("")
            lines.append("  Rationale:")
            lines.append(f"    - Relevance improvement of {rel['improvement_mean']*100:.1f}% justifies the cost")
            lines.append(f"    - Latency overhead of {lat['overhead_mean_pct']:.0f}% is acceptable")
            lines.append(f"    - Improves {rel['queries_improved']}/{stats['num_queries']} queries")

        elif marginal_improvement and low_overhead and mostly_improves:
            lines.append("  RECOMMENDATION: MAKE RERANKER OPTIONAL (Marginal Benefit)")
            lines.append("")
            lines.append("  Rationale:")
            lines.append(f"    - Small relevance improvement ({rel['improvement_mean']*100:.1f}%)")
            lines.append(f"    - Low overhead ({lat['overhead_mean_pct']:.0f}%) makes it viable")
            lines.append("    - Recommend: Enable via config flag, default ON")
            lines.append("    - Use case: Disable for latency-sensitive applications")

        elif not mostly_improves or rel['improvement_mean'] <= 0:
            lines.append("  RECOMMENDATION: REMOVE RERANKER (No Benefit)")
            lines.append("")
            lines.append("  Rationale:")
            lines.append(f"    - No relevance improvement (mean: {rel['improvement_mean']*100:.1f}%)")
            lines.append(f"    - {rel['queries_degraded']} queries actually got worse")
            lines.append(f"    - Unnecessary latency cost ({lat['overhead_mean_pct']:.0f}%)")

        elif not changes_ranking:
            lines.append("  RECOMMENDATION: CONSIDER REMOVING (Redundant)")
            lines.append("")
            lines.append("  Rationale:")
            lines.append(f"    - High overlap ({rank['top_k_overlap_mean']*100:.0f}%) - results mostly unchanged")
            lines.append(f"    - BGE embeddings already rank well")
            lines.append(f"    - Reranker adds latency without changing results")

        else:
            lines.append("  RECOMMENDATION: MAKE RERANKER OPTIONAL (Mixed Results)")
            lines.append("")
            lines.append("  Rationale:")
            lines.append("    - Results are mixed - some queries improve, some don't")
            lines.append("    - Recommend: Add config flag to enable/disable")
            lines.append("    - Consider query-specific reranking (only for complex queries)")

        return lines


def main():
    """Run the benchmark and print results."""
    parser = argparse.ArgumentParser(description='BGE Reranker Benchmark')
    parser.add_argument('--mock', action='store_true',
                        help='Use mock documents instead of ChromaDB')
    parser.add_argument('-k', type=int, default=5,
                        help='Number of final results to return (default: 5)')
    parser.add_argument('--candidate-multiplier', type=int, default=4,
                        help='Multiplier for candidate retrieval (default: 4)')
    args = parser.parse_args()

    print("\n" + "=" * 70)
    print("BGE RERANKER BENCHMARK")
    print("Evaluating: BAAI/bge-reranker-v2-m3")
    print("=" * 70 + "\n")

    try:
        benchmark = RerankerBenchmark(
            k=args.k,
            candidate_multiplier=args.candidate_multiplier,
            use_mock=args.mock
        )
        stats = benchmark.run_benchmark()
        report = benchmark.generate_report(stats)
        print("\n")
        print(report)

        # Save report to file
        report_path = "results/reranker_benchmark_report.txt"
        os.makedirs("results", exist_ok=True)
        with open(report_path, 'w') as f:
            f.write(report)
        print(f"\nReport saved to: {report_path}")

        # Return stats for programmatic use
        return stats

    except FileNotFoundError as e:
        print(f"Error: {e}")
        print("Make sure the ChromaDB is populated or use --mock flag.")
        sys.exit(1)
    except Exception as e:
        print(f"Error running benchmark: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
