"""
Event Evolution Scoring - Exact Methods from FE-EKG Paper
Implements only the methods with exact formulas specified in the paper
"""

import math
from datetime import datetime
from typing import Dict, List, Tuple, Set
from collections import defaultdict


class EventEvolutionScorer:
    """Compute evolution scores between events using exact formulas from paper"""

    def __init__(self):
        """Initialize with paper's exact parameters"""
        # Temporal correlation parameters (TCDI) - Formula explicitly in paper
        self.K = 1.0  # Temporal coefficient (from paper)
        self.alpha = 0.1  # Decay rate (from paper)

    def parse_date(self, date_str: str) -> datetime:
        """Parse RDF date string to datetime"""
        if not date_str or date_str == 'unknown':
            return None

        # Remove RDF datatype annotation
        if '^^' in date_str:
            date_str = date_str.split('^^')[0].strip(' "')
        date_str = date_str.strip(' "')

        try:
            return datetime.strptime(date_str, '%Y-%m-%d')
        except:
            return None

    def temporal_correlation(self, event1: Dict, event2: Dict) -> float:
        """
        Method 1: Temporal Correlation Decay Index (TCDI)
        Formula: TCDI(ΔT) = K * e^(-α * ΔT)
        where ΔT is time interval in days
        """
        date1 = self.parse_date(event1.get('date', ''))
        date2 = self.parse_date(event2.get('date', ''))

        if not date1 or not date2:
            return 0.0

        # Event1 should be before event2 for evolution
        if date1 > date2:
            return 0.0

        # Calculate time difference in days
        delta_t = (date2 - date1).days

        # Apply TCDI formula
        score = self.K * math.exp(-self.alpha * delta_t)

        return round(score, 4)

    def entity_overlap(self, event1: Dict, event2: Dict) -> float:
        """
        Method 2: Entity Overlap - Jaccard Similarity
        Measures shared entities between events
        """
        # Get entity sets
        entities1 = set(event1.get('entities', []))
        entities2 = set(event2.get('entities', []))

        if not entities1 or not entities2:
            return 0.0

        # Jaccard similarity: intersection / union
        intersection = entities1 & entities2
        union = entities1 | entities2

        if len(union) == 0:
            return 0.0

        score = len(intersection) / len(union)

        return round(score, 4)

    def compute_evolution_score(self, event1: Dict, event2: Dict) -> Dict[str, float]:
        """
        Compute evolution score using only exact formulas from paper:
        1. Temporal correlation (TCDI)
        2. Entity overlap (Jaccard similarity)

        Returns dict with individual scores and composite
        """
        # Compute the 2 methods with exact formulas
        scores = {
            'temporal': self.temporal_correlation(event1, event2),
            'entity_overlap': self.entity_overlap(event1, event2),
        }

        # Composite score: simple average of the 2 methods
        # (Paper's Formula 7 uses weights, but we don't have exact weights for all 6)
        composite = (scores['temporal'] + scores['entity_overlap']) / 2.0
        scores['composite'] = round(composite, 4)

        return scores


def compute_event_evolution_links(events: List[Dict],
                                  min_score: float = 0.2,
                                  max_time_window_days: int = 365) -> List[Dict]:
    """
    Compute evolution links between all event pairs using exact formulas from paper.

    Uses 2 methods with exact formulas:
    1. Temporal Correlation Decay Index (TCDI): K*e^(-α*ΔT)
    2. Entity Overlap: Jaccard similarity of shared entities

    Args:
        events: List of event dicts with id, date, type, description, entities
        min_score: Minimum composite score to create link (default 0.2 from paper)
        max_time_window_days: Maximum time gap for evolution (default 1 year)

    Returns:
        List of evolution link dicts with source, target, temporal, entity_overlap, and composite scores
    """
    scorer = EventEvolutionScorer()
    links = []

    # Sort events by date
    sorted_events = sorted(events, key=lambda e: scorer.parse_date(e.get('date', '')) or datetime.min)

    total_pairs = len(sorted_events) * (len(sorted_events) - 1) // 2
    print(f"Computing evolution scores for {len(sorted_events)} events ({total_pairs} pairs)...")

    count = 0
    for i, event1 in enumerate(sorted_events):
        date1 = scorer.parse_date(event1.get('date', ''))
        if not date1:
            continue

        for j, event2 in enumerate(sorted_events[i+1:], start=i+1):
            date2 = scorer.parse_date(event2.get('date', ''))
            if not date2:
                continue

            # Skip if time window too large
            if (date2 - date1).days > max_time_window_days:
                continue

            # Compute scores
            scores = scorer.compute_evolution_score(event1, event2)

            # Create link if above threshold
            if scores['composite'] >= min_score:
                links.append({
                    'source': event1['id'],
                    'target': event2['id'],
                    'type': 'evolvesTo',
                    'strength': scores['composite'],
                    **{k: v for k, v in scores.items() if k != 'composite'}
                })
                count += 1

        # Progress update every 10 events
        if (i + 1) % 10 == 0:
            print(f"  Processed {i+1}/{len(sorted_events)} events, found {count} evolution links so far...")

    print(f"✅ Created {len(links)} evolution links (min_score={min_score})")

    return links
