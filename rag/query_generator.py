"""
SOTA Query Generation for RAG Pipeline

Implements:
1. Dynamic query generation based on market state
2. Multi-query variations for better coverage
3. HyDE (Hypothetical Document Embeddings)
4. Agent-specific query customization
"""

import logging
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)

class QueryGenerator:
    """Generate diverse, context-aware queries for RAG retrieval."""

    # Market regime thresholds
    REGIME_THRESHOLDS = {
        'normal': (0.0, 0.20),
        'stress': (0.20, 0.50),
        'crisis': (0.50, 1.0)
    }

    # Query templates by market regime
    # Using specific financial terms and entities that appear in actual documents
    REGIME_TEMPLATES = {
        'normal': [
            "market outlook {date} GDP growth economic expansion",
            "banking sector earnings {date} loan growth deposits",
            "credit conditions {date} lending standards consumer credit"
        ],
        'stress': [
            "subprime mortgage defaults {date} housing market decline",
            "credit spreads widening {date} CDO writedowns MBS losses",
            "Bear Stearns {date} hedge fund collapse liquidity concerns",
            "counterparty risk {date} CDS exposure derivatives"
        ],
        'crisis': [
            "Lehman Brothers bankruptcy {date} financial crisis contagion",
            "AIG bailout {date} government intervention TARP",
            "credit freeze {date} commercial paper LIBOR TED spread",
            "Fannie Mae Freddie Mac {date} conservatorship mortgage crisis",
            "bank run {date} Washington Mutual Wachovia failure"
        ]
    }

    # Bank-specific query templates
    BANK_TEMPLATES = {
        'low_liquidity': [
            "liquidity management crisis {date} funding strategies",
            "emergency liquidity facilities {date} discount window",
            "asset fire sales {date} deleveraging"
        ],
        'high_exposure': [
            "credit losses {date} writedowns provisions",
            "capital raising {date} equity dilution",
            "risk reduction strategies {date} portfolio hedging"
        ],
        'default': [
            "bank risk management {date} best practices",
            "capital preservation {date} defensive strategies"
        ]
    }

    @classmethod
    def get_market_regime(cls, volatility: float) -> str:
        """Determine market regime from volatility."""
        for regime, (low, high) in cls.REGIME_THRESHOLDS.items():
            if low <= volatility < high:
                return regime
        return 'crisis'

    @classmethod
    def generate_market_queries(
        cls,
        date: str,
        volatility: float,
        liquidity_factor: float,
        num_queries: int = 3
    ) -> List[str]:
        """
        Generate diverse queries based on market conditions.

        Args:
            date: Current simulation date (e.g., "September 2008")
            volatility: Market volatility (0-1)
            liquidity_factor: Liquidity multiplier (1.0 = normal)
            num_queries: Number of query variations to generate

        Returns:
            List of query strings
        """
        regime = cls.get_market_regime(volatility)
        templates = cls.REGIME_TEMPLATES[regime]

        # Select templates (cycle if needed)
        queries = []
        for i in range(num_queries):
            template = templates[i % len(templates)]
            query = template.format(date=date)
            queries.append(query)

        # Add liquidity-specific query if stressed
        if liquidity_factor < 0.5:
            queries.append(f"liquidity crisis interbank market freeze {date}")

        logger.info(f"Generated {len(queries)} queries for regime '{regime}' at {date}")
        return queries

    @classmethod
    def generate_agent_queries(
        cls,
        bank_name: str,
        date: str,
        capital: float,
        liquidity: float,
        risk_score: float,
        volatility: float,
        liquidity_factor: float = 1.0
    ) -> List[str]:
        """
        Generate bank-specific queries based on agent state.

        Args:
            bank_name: Name of the bank
            date: Current simulation date
            capital: Bank's capital (billions)
            liquidity: Bank's liquidity ratio
            risk_score: Bank's risk score
            volatility: Market volatility
            liquidity_factor: Global liquidity multiplier (default 1.0)

        Returns:
            List of query strings tailored to this bank's situation
        """
        queries = []
        regime = cls.get_market_regime(volatility)

        # Categorize bank state for more specific queries
        liquidity_state = "critical" if liquidity < 0.08 else "low" if liquidity < 0.15 else "adequate"
        capital_state = "weak" if capital < 50 else "moderate" if capital < 80 else "strong"
        risk_state = "high" if risk_score > 0.5 else "moderate" if risk_score > 0.2 else "low"

        # Global liquidity crisis check - use specific terms from 2008 crisis
        if liquidity_factor < 0.5:
            queries.append(f"LIBOR TED spread {date} interbank lending freeze")
            queries.append(f"Federal Reserve emergency lending {date} discount window TAF")
            if liquidity_factor < 0.3:
                 queries.append(f"Lehman Brothers AIG {date} systemic risk contagion")

        # Generate queries based on specific bank situation
        if liquidity_state == "critical":
            queries.append(f"emergency liquidity crisis bank failure {date} Fed discount window")
            queries.append(f"liquidity crunch funding freeze {date} survival strategies")
        elif liquidity_state == "low":
            queries.append(f"liquidity management stress {date} funding strategies")
            queries.append(f"short-term funding markets {date} commercial paper")
        else:
            queries.append(f"liquidity buffer maintenance {date} best practices")

        if capital_state == "weak":
            queries.append(f"capital raising dilution {date} bank recapitalization")
            queries.append(f"asset sales deleveraging {date} balance sheet reduction")
        elif capital_state == "moderate":
            queries.append(f"capital preservation {date} risk reduction strategies")

        if risk_state == "high":
            queries.append(f"credit losses writedowns {date} loan provisions")
            queries.append(f"counterparty risk exposure {date} default contagion")
        elif risk_state == "moderate":
            queries.append(f"risk management hedging {date} portfolio protection")

        # Add regime-specific query with variation based on bank ID
        bank_id = int(bank_name.split('_')[-1]) if '_' in bank_name else 0
        market_templates = cls.REGIME_TEMPLATES[regime]
        template_idx = bank_id % len(market_templates)
        queries.append(market_templates[template_idx].format(date=date))

        # Ensure we have at least 2 queries
        if len(queries) < 2:
            queries.append(f"bank risk management {date} defensive strategies")
            queries.append(f"financial stability {date} market conditions")

        logger.debug(f"Generated {len(queries)} agent queries for {bank_name} (liq={liquidity_state}, cap={capital_state}, risk={risk_state})")
        return queries

    @classmethod
    def generate_hyde_document(
        cls,
        date: str,
        volatility: float,
        liquidity_factor: float
    ) -> str:
        """
        Generate a hypothetical document (HyDE) for embedding.

        Instead of searching with a question, we generate what an ideal
        document would look like and search for similar documents.

        Args:
            date: Current simulation date
            volatility: Market volatility
            liquidity_factor: Liquidity multiplier

        Returns:
            Hypothetical document text
        """
        regime = cls.get_market_regime(volatility)

        if regime == 'normal':
            hyde_doc = f"""
            Market Analysis Report - {date}

            Economic conditions remain stable with moderate growth expectations.
            Credit markets are functioning normally with adequate liquidity.
            Banking sector shows healthy capital ratios and manageable risk levels.
            Key indicators: volatility low, spreads tight, funding available.
            Recommendation: maintain current positions with standard risk management.
            """
        elif regime == 'stress':
            hyde_doc = f"""
            Market Risk Assessment - {date}

            Warning signs emerging in credit markets. Spreads widening across
            investment grade and high yield sectors. Funding conditions tightening
            in short-term markets. Banks reporting increased counterparty concerns.
            Liquidity hoarding behavior observed. Volatility elevated.
            Recommendation: reduce risk exposures, increase liquidity buffers,
            monitor counterparty credit carefully.
            """
        else:  # crisis
            hyde_doc = f"""
            Emergency Market Briefing - {date}

            Severe financial crisis underway. Lehman Brothers has filed for bankruptcy,
            triggering global contagion. AIG requires emergency government bailout.
            LIBOR-OIS and TED spreads at record highs. Commercial paper market frozen.
            Interbank lending has seized up. CDO and MBS writedowns accelerating.
            Federal Reserve implementing emergency lending facilities including TAF and PDCF.
            TARP legislation being considered. Washington Mutual and Wachovia facing runs.
            Recommendation: immediate defensive action required. Maximize liquidity buffers.
            Reduce counterparty exposure. Prepare for extended market dysfunction.
            """

        return hyde_doc.strip()


def generate_temporal_filter(date: str, range_months: int = 3) -> Dict:
    """
    Generate metadata filter for temporal proximity.

    Args:
        date: Current date string (e.g., "September 2008")
        range_months: Number of months to include

    Returns:
        Filter dict for ChromaDB
    """
    # Parse date
    month_map = {
        'january': 1, 'february': 2, 'march': 3, 'april': 4,
        'may': 5, 'june': 6, 'july': 7, 'august': 8,
        'september': 9, 'october': 10, 'november': 11, 'december': 12
    }

    parts = date.lower().split()
    if len(parts) >= 2:
        month_str = parts[0]
        year = int(parts[1])
        month = month_map.get(month_str, 1)
    else:
        return None  # Can't parse, skip filtering

    # Calculate date range
    # For simplicity, filter by year only (ChromaDB metadata filtering is limited)
    # In production, you'd use more sophisticated date filtering

    return {"year": {"$gte": year - 1, "$lte": year}}
