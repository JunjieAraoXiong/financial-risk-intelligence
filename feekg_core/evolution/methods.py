"""
Event Evolution Methods - Six algorithms from FEEKG paper

Implements evolution relationship scoring between events:
1. Temporal Correlation (TCDI)
2. Entity Overlap
3. Semantic Similarity
4. Topic Relevance
5. Event Type Patterns (causal chains)
6. Emotional Consistency (sentiment)
"""

import re
from datetime import datetime, timedelta
from typing import List, Dict, Tuple, Set
from collections import Counter


class EventEvolutionScorer:
    """Calculates evolution scores between event pairs"""

    def __init__(self, events: List[Dict], entities: List[Dict]):
        """
        Initialize with events and entities data

        Args:
            events: List of event dicts from JSON
            entities: List of entity dicts from JSON
        """
        self.events = events
        self.entities = entities
        self.entity_map = {e['entityId']: e for e in entities}

        # Event type transition patterns (from paper's analysis)
        self.causal_patterns = {
            'regulatory_pressure': ['liquidity_warning', 'credit_downgrade'],
            'liquidity_warning': ['missed_payment', 'credit_downgrade', 'stock_decline'],
            'credit_downgrade': ['debt_default', 'stock_crash', 'contagion'],
            'missed_payment': ['debt_default', 'trading_halt'],
            'debt_default': ['credit_downgrade', 'restructuring_announcement', 'asset_seizure'],
            'stock_decline': ['stock_crash', 'contagion'],
            'stock_crash': ['trading_halt', 'contagion'],
            'contagion': ['regulatory_intervention'],
        }

    def compute_temporal_correlation(self, evt_a: Dict, evt_b: Dict,
                                     max_days: int = 30, k: float = 1.0,
                                     alpha: float = 0.1) -> float:
        """
        Temporal Correlation Decay Index (TCDI) from paper

        Formula: TCDI(ΔT) = Ke^(-αΔT)

        Args:
            evt_a: Earlier event
            evt_b: Later event
            max_days: Maximum days for correlation
            k: Constant (theme-dependent, default 1.0)
            alpha: Decay rate (default 0.1)

        Returns:
            TCDI score (0.0 to 1.0), 0 if outside window
        """
        date_a = datetime.strptime(evt_a['date'], '%Y-%m-%d')
        date_b = datetime.strptime(evt_b['date'], '%Y-%m-%d')

        delta_days = (date_b - date_a).days

        # Must be forward in time and within window
        if delta_days <= 0 or delta_days > max_days:
            return 0.0

        # TCDI formula from paper
        import math
        tcdi = k * math.exp(-alpha * delta_days)

        # Threshold: paper says < 10^-1 is not significant
        if tcdi < 0.1:
            return 0.0

        return min(1.0, tcdi)

    def compute_entity_overlap(self, evt_a: Dict, evt_b: Dict) -> float:
        """
        Entity overlap score - events sharing entities are related

        From paper: Events with same subjects have higher evolution intensity

        Args:
            evt_a: First event
            evt_b: Second event

        Returns:
            Overlap score (0.0 to 1.0)
        """
        # Get entities involved in each event
        entities_a = set()
        if evt_a.get('actor'):
            entities_a.add(evt_a['actor'])
        if evt_a.get('target'):
            entities_a.add(evt_a['target'])

        entities_b = set()
        if evt_b.get('actor'):
            entities_b.add(evt_b['actor'])
        if evt_b.get('target'):
            entities_b.add(evt_b['target'])

        if not entities_a or not entities_b:
            return 0.0

        # Jaccard similarity
        intersection = entities_a & entities_b
        union = entities_a | entities_b

        overlap = len(intersection) / len(union)

        # Paper mentions: same subject (actor/patient) = higher score
        # Boost if actor matches
        if evt_a.get('actor') and evt_a.get('actor') == evt_b.get('actor'):
            overlap = min(1.0, overlap + 0.2)

        return overlap

    def compute_semantic_similarity(self, evt_a: Dict, evt_b: Dict) -> float:
        """
        Semantic similarity using simple text features

        Paper uses TextRank + word2vec. For MVP, we use:
        - Keyword overlap
        - Event type similarity

        Args:
            evt_a: First event
            evt_b: Second event

        Returns:
            Similarity score (0.0 to 1.0)
        """
        # Extract keywords from descriptions
        def get_keywords(desc: str) -> Set[str]:
            # Simple keyword extraction
            words = re.findall(r'\b\w{4,}\b', desc.lower())
            # Remove common stopwords
            stopwords = {'this', 'that', 'with', 'from', 'were', 'have', 'been',
                        'said', 'will', 'would', 'their', 'them', 'than', 'then'}
            return set(w for w in words if w not in stopwords)

        desc_a = evt_a.get('description', '')
        desc_b = evt_b.get('description', '')

        keywords_a = get_keywords(desc_a)
        keywords_b = get_keywords(desc_b)

        if not keywords_a or not keywords_b:
            return 0.0

        # Jaccard similarity of keywords
        intersection = keywords_a & keywords_b
        union = keywords_a | keywords_b

        keyword_sim = len(intersection) / len(union) if union else 0.0

        # Event type similarity (same type = higher)
        type_sim = 1.0 if evt_a.get('type') == evt_b.get('type') else 0.0

        # Combined score (weighted)
        similarity = 0.7 * keyword_sim + 0.3 * type_sim

        return similarity

    def compute_topic_relevance(self, evt_a: Dict, evt_b: Dict) -> float:
        """
        Topic relevance from paper's topic model

        Paper uses trigger words (R_A vs R_B). For MVP, we check:
        - Event type topic categories
        - Financial domain relevance

        Args:
            evt_a: First event
            evt_b: Second event

        Returns:
            Relevance score (0.0 to 1.0)
        """
        # Group event types by topic
        topics = {
            'credit': ['credit_downgrade', 'debt_default', 'missed_payment'],
            'market': ['stock_decline', 'stock_crash', 'trading_halt'],
            'regulatory': ['regulatory_pressure', 'regulatory_intervention'],
            'corporate': ['restructuring_announcement', 'asset_seizure', 'debt_restructuring'],
            'systemic': ['contagion'],
        }

        type_a = evt_a.get('type', '')
        type_b = evt_b.get('type', '')

        # Find topics for each event
        topics_a = [t for t, types in topics.items() if type_a in types]
        topics_b = [t for t, types in topics.items() if type_b in types]

        if not topics_a or not topics_b:
            # Different topics but related domain
            return 0.3

        # Same topic = high relevance
        if set(topics_a) & set(topics_b):
            return 1.0

        # Related topics (credit ↔ market, credit ↔ corporate)
        related_pairs = [
            ('credit', 'market'),
            ('credit', 'corporate'),
            ('market', 'systemic'),
            ('regulatory', 'credit'),
        ]

        for topic_a in topics_a:
            for topic_b in topics_b:
                if (topic_a, topic_b) in related_pairs or (topic_b, topic_a) in related_pairs:
                    return 0.7

        # Different but in financial domain
        return 0.3

    def compute_event_type_causality(self, evt_a: Dict, evt_b: Dict) -> float:
        """
        Event type causality patterns

        Based on domain knowledge: certain event types cause others
        Example: credit_downgrade → debt_default → restructuring

        Args:
            evt_a: Cause event
            evt_b: Effect event

        Returns:
            Causality score (0.0 to 1.0)
        """
        type_a = evt_a.get('type', '')
        type_b = evt_b.get('type', '')

        # Check if type_a → type_b is a known pattern
        if type_a in self.causal_patterns:
            if type_b in self.causal_patterns[type_a]:
                return 0.9  # Strong causal link

        # Check for indirect causality (2-hop)
        if type_a in self.causal_patterns:
            for intermediate in self.causal_patterns[type_a]:
                if intermediate in self.causal_patterns:
                    if type_b in self.causal_patterns[intermediate]:
                        return 0.6  # Weaker indirect link

        return 0.0

    def compute_emotional_consistency(self, evt_a: Dict, evt_b: Dict) -> float:
        """
        Emotional Volatility Index (EVI) from paper

        Paper formula: EVI = |sentiment_score_A - sentiment_score_B|

        For MVP, we use simple sentiment from event types and keywords

        Args:
            evt_a: First event
            evt_b: Second event

        Returns:
            EVI score (0.0 to 1.0), lower = more consistent
        """
        # Sentiment mapping for event types
        sentiment_map = {
            'regulatory_pressure': -0.6,
            'liquidity_warning': -0.7,
            'credit_downgrade': -0.8,
            'debt_default': -0.9,
            'missed_payment': -0.8,
            'stock_decline': -0.7,
            'stock_crash': -0.9,
            'trading_halt': -0.8,
            'contagion': -0.8,
            'regulatory_intervention': -0.3,  # Mixed (intervention = help)
            'restructuring_announcement': 0.2,  # Slightly positive (plan)
            'asset_seizure': -0.9,
            'debt_restructuring': 0.1,
        }

        sent_a = sentiment_map.get(evt_a.get('type', ''), -0.5)
        sent_b = sentiment_map.get(evt_b.get('type', ''), -0.5)

        # EVI = difference in sentiment
        evi = abs(sent_a - sent_b)

        # Paper threshold: if EVI < threshold (0.6), events are emotionally consistent
        # Convert to consistency score (inverse)
        consistency = max(0.0, 1.0 - evi)

        return consistency

    def compute_evolution_score(self, evt_a: Dict, evt_b: Dict,
                               weights: Dict[str, float] = None) -> Tuple[float, Dict[str, float]]:
        """
        Compute overall evolution score combining all methods

        Paper formula (simplified):
        Evo_score = w1*TCDI + w2*EntityOverlap + w3*Semantic + w4*Topic + w5*Causal + w6*EVI

        Args:
            evt_a: Earlier event (potential cause)
            evt_b: Later event (potential effect)
            weights: Optional custom weights for each method

        Returns:
            Tuple of (overall_score, component_scores dict)
        """
        # Default weights from paper insights
        if weights is None:
            weights = {
                'temporal': 0.25,
                'entity_overlap': 0.20,
                'semantic': 0.15,
                'topic': 0.15,
                'causality': 0.15,
                'emotional': 0.10,
            }

        # Compute all components
        scores = {
            'temporal': self.compute_temporal_correlation(evt_a, evt_b),
            'entity_overlap': self.compute_entity_overlap(evt_a, evt_b),
            'semantic': self.compute_semantic_similarity(evt_a, evt_b),
            'topic': self.compute_topic_relevance(evt_a, evt_b),
            'causality': self.compute_event_type_causality(evt_a, evt_b),
            'emotional': self.compute_emotional_consistency(evt_a, evt_b),
        }

        # Weighted sum
        overall_score = sum(weights[k] * scores[k] for k in weights.keys())

        # Paper threshold: score > 0.2 = significant evolution relationship
        if overall_score < 0.2:
            overall_score = 0.0

        return overall_score, scores


def _compute_event_pair_batch(args):
    """
    Helper function for parallel processing of event pairs

    Args:
        args: Tuple of (event_pairs, events_list, entities_list, threshold)

    Returns:
        List of evolution links for this batch
    """
    event_pairs, events_list, entities_list, threshold = args
    scorer = EventEvolutionScorer(events_list, entities_list)
    links = []

    for evt_a, evt_b in event_pairs:
        score, components = scorer.compute_evolution_score(evt_a, evt_b)

        if score >= threshold:
            links.append({
                'from': evt_a['eventId'],
                'to': evt_b['eventId'],
                'score': score,
                'components': components,
                'from_date': evt_a['date'],
                'to_date': evt_b['date'],
                'from_type': evt_a['type'],
                'to_type': evt_b['type'],
            })

    return links


def compute_all_evolution_links(events: List[Dict], entities: List[Dict],
                               threshold: float = 0.2,
                               use_parallel: bool = True,
                               max_workers: int = None) -> List[Dict]:
    """
    Compute evolution links for all event pairs

    Args:
        events: List of events from JSON
        entities: List of entities from JSON
        threshold: Minimum score to create link (paper uses 0.2)
        use_parallel: Use multiprocessing for faster computation (default: True)
        max_workers: Number of parallel workers (default: CPU count)

    Returns:
        List of evolution link dicts with scores
    """
    # Sort events by date
    sorted_events = sorted(events, key=lambda e: e['date'])

    # Generate all event pairs (forward-looking only)
    event_pairs = []
    for i, evt_a in enumerate(sorted_events):
        for evt_b in sorted_events[i+1:]:
            event_pairs.append((evt_a, evt_b))

    print(f"   Total pairs to evaluate: {len(event_pairs):,}")

    if not use_parallel or len(event_pairs) < 1000:
        # Serial processing for small datasets
        scorer = EventEvolutionScorer(sorted_events, entities)
        links = []

        for i, (evt_a, evt_b) in enumerate(event_pairs):
            if i % 10000 == 0 and i > 0:
                print(f"   Progress: {i:,}/{len(event_pairs):,} pairs ({i*100//len(event_pairs)}%)")

            score, components = scorer.compute_evolution_score(evt_a, evt_b)

            if score >= threshold:
                links.append({
                    'from': evt_a['eventId'],
                    'to': evt_b['eventId'],
                    'score': score,
                    'components': components,
                    'from_date': evt_a['date'],
                    'to_date': evt_b['date'],
                    'from_type': evt_a['type'],
                    'to_type': evt_b['type'],
                })

        return links

    # Parallel processing for large datasets
    from multiprocessing import Pool, cpu_count
    import os

    if max_workers is None:
        max_workers = min(cpu_count(), 8)  # Cap at 8 to avoid overhead

    print(f"   Using {max_workers} parallel workers")

    # Split pairs into chunks for parallel processing
    chunk_size = max(1, len(event_pairs) // (max_workers * 4))  # 4 chunks per worker
    chunks = []

    for i in range(0, len(event_pairs), chunk_size):
        chunk = event_pairs[i:i + chunk_size]
        chunks.append((chunk, sorted_events, entities, threshold))

    print(f"   Processing in {len(chunks)} batches")

    # Process in parallel
    try:
        with Pool(max_workers) as pool:
            results = pool.map(_compute_event_pair_batch, chunks)

        # Flatten results
        links = []
        for batch_links in results:
            links.extend(batch_links)

        return links

    except Exception as e:
        print(f"   ⚠️  Parallel processing failed: {e}")
        print(f"   Falling back to serial processing...")

        # Fallback to serial if parallel fails
        return compute_all_evolution_links(
            events, entities,
            threshold=threshold,
            use_parallel=False
        )


if __name__ == "__main__":
    # Test with sample events
    sample_events = [
        {
            'eventId': 'evt_001',
            'type': 'regulatory_pressure',
            'date': '2021-01-01',
            'actor': 'ent_regulator',
            'target': 'ent_company',
            'description': 'New regulations introduced for financial sector'
        },
        {
            'eventId': 'evt_002',
            'type': 'liquidity_warning',
            'date': '2021-01-15',
            'actor': 'ent_company',
            'target': None,
            'description': 'Company warns of liquidity problems and cash shortage'
        },
        {
            'eventId': 'evt_003',
            'type': 'credit_downgrade',
            'date': '2021-01-20',
            'actor': 'ent_rating',
            'target': 'ent_company',
            'description': 'Credit rating downgraded due to financial problems'
        },
    ]

    sample_entities = [
        {'entityId': 'ent_company', 'name': 'Test Company'},
        {'entityId': 'ent_regulator', 'name': 'Regulator'},
        {'entityId': 'ent_rating', 'name': 'Rating Agency'},
    ]

    scorer = EventEvolutionScorer(sample_events, sample_entities)

    print("Testing Event Evolution Scoring:")
    print("=" * 60)

    for i in range(len(sample_events) - 1):
        evt_a = sample_events[i]
        evt_b = sample_events[i + 1]

        score, components = scorer.compute_evolution_score(evt_a, evt_b)

        print(f"\n{evt_a['eventId']} → {evt_b['eventId']}")
        print(f"Overall Score: {score:.3f}")
        print("Components:")
        for name, val in components.items():
            print(f"  {name}: {val:.3f}")
