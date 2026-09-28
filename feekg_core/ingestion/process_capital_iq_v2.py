#!/usr/bin/env python3
"""
Optimized Capital IQ ETL Pipeline v2
Improvements over v1:
- Deduplication by (date + headline)
- Entity extraction from headlines using NLP
- Better event type classification (bankruptcy, bailout, downgrade)
- Crisis-specific filtering (not just company name matching)
- Richer risk generation logic
"""

import pandas as pd
import json
import os
import sys
import argparse
import re
from datetime import datetime
from typing import List, Dict, Set, Optional
from collections import defaultdict


class CapitalIQProcessorV2:
    """
    Improved Capital IQ data processor with:
    - Deduplication
    - NLP entity extraction
    - Crisis-specific event classification
    - Better risk inference
    """

    # Financial institutions related to Lehman crisis
    CRISIS_ENTITIES = {
        'Lehman Brothers': 'investment_bank',
        'Bear Stearns': 'investment_bank',
        'Merrill Lynch': 'investment_bank',
        'AIG': 'insurance',
        'American International Group': 'insurance',
        'JPMorgan': 'bank',
        'JP Morgan': 'bank',
        'Bank of America': 'bank',
        'BofA': 'bank',
        'Barclays': 'bank',
        'Goldman Sachs': 'investment_bank',
        'Morgan Stanley': 'investment_bank',
        'Citigroup': 'bank',
        'Citi': 'bank',
        'Federal Reserve': 'regulator',
        'Fed': 'regulator',
        'Treasury': 'regulator',
        'SEC': 'regulator'
    }

    # Crisis-related keywords for better filtering
    CRISIS_KEYWORDS = [
        'bankruptcy', 'bailout', 'rescue', 'collapse', 'downgrade',
        'subprime', 'mortgage', 'credit crisis', 'financial crisis',
        'liquidity', 'capital raise', 'emergency', 'restructuring',
        'writedown', 'write-down', 'loss', 'default', 'rating'
    ]

    # Event type classification patterns
    EVENT_PATTERNS = {
        'bankruptcy': ['bankruptcy', 'chapter 11', 'insolvency', 'files for bankruptcy'],
        'government_intervention': ['bailout', 'rescue', 'government support', 'fed provides', 'treasury provides'],
        'merger_acquisition': ['acquisition', 'acquires', 'acquired', 'merger', 'merges', 'purchased'],
        'credit_downgrade': ['downgrade', 'rating cut', 'credit rating', 'moody', 'fitch', 's&p'],
        'earnings_loss': ['loss', 'losses', 'writedown', 'write-down', 'impairment'],
        'capital_raising': ['capital raise', 'raises capital', 'funding', 'investment'],
        'management_change': ['ceo', 'chief executive', 'resignation', 'appointed', 'steps down']
    }

    def __init__(self, input_file: str):
        self.input_file = input_file
        self.df = None
        self.entities = {}  # entity_name -> entity_type
        self.load_data()

    def load_data(self):
        """Load and prepare Capital IQ data"""
        print(f"\n📥 Loading data from: {self.input_file}")

        # Load with robust error handling
        if self.input_file.endswith('.xlsx'):
            self.df = pd.read_excel(self.input_file)
        elif self.input_file.endswith('.csv'):
            try:
                self.df = pd.read_csv(self.input_file, encoding='utf-8', on_bad_lines='skip', low_memory=False)
            except:
                try:
                    self.df = pd.read_csv(self.input_file, encoding='latin-1', on_bad_lines='skip', low_memory=False)
                except:
                    self.df = pd.read_csv(self.input_file, encoding='ISO-8859-1', on_bad_lines='skip', low_memory=False)
        else:
            raise ValueError("File must be .xlsx or .csv")

        print(f"   ✅ Loaded {len(self.df):,} raw events")

        # Normalize column names
        self.df.columns = self.df.columns.str.lower().str.strip()

        # Convert date column
        self.df['announcedate'] = pd.to_datetime(self.df['announcedate'], errors='coerce')

        print(f"   ✅ Date range: {self.df['announcedate'].min()} to {self.df['announcedate'].max()}")

    def extract_lehman_crisis_events(self) -> pd.DataFrame:
        """
        Extract Lehman Brothers crisis events using:
        1. Date filter (2007-2009)
        2. Entity mentions in headlines
        3. Crisis keyword matching
        4. Deduplication
        """
        print(f"\n🎯 Extracting Lehman crisis events...")

        # Step 1: Filter by date range
        crisis_period = (self.df['announcedate'] >= '2007-01-01') & (self.df['announcedate'] <= '2009-12-31')
        filtered = self.df[crisis_period].copy()
        print(f"   ✅ Date filter (2007-2009): {len(filtered):,} events")

        # Step 2: Filter by entity mentions OR crisis keywords
        entity_pattern = '|'.join(self.CRISIS_ENTITIES.keys())
        keyword_pattern = '|'.join(self.CRISIS_KEYWORDS)

        entity_mask = filtered['headline'].str.contains(entity_pattern, case=False, na=False)
        keyword_mask = filtered['headline'].str.contains(keyword_pattern, case=False, na=False)

        # Keep events that mention crisis entities OR crisis keywords
        crisis_relevant = filtered[entity_mask | keyword_mask].copy()
        print(f"   ✅ Entity/keyword filter: {len(crisis_relevant):,} events")

        # Step 3: Deduplicate by (date + headline)
        before_dedup = len(crisis_relevant)
        crisis_relevant = crisis_relevant.drop_duplicates(subset=['announcedate', 'headline'], keep='first')
        duplicates_removed = before_dedup - len(crisis_relevant)
        print(f"   ✅ Deduplication: removed {duplicates_removed} duplicates → {len(crisis_relevant):,} unique events")

        # Step 4: Sort by date
        crisis_relevant = crisis_relevant.sort_values('announcedate')

        return crisis_relevant

    def extract_entities_from_text(self, text: str) -> Set[str]:
        """Extract financial entities from text using pattern matching"""
        if pd.isna(text):
            return set()

        entities = set()
        text_lower = text.lower()

        # Ambiguous short names that need special handling
        ambiguous_names = {
            'SEC': r'\bsec\b(?!ond|urity|tor|ure)',  # Match SEC but not second, security, sector, secure
            'Fed': r'\bfed\b(?!eral)',                # Match Fed but not federal
        }

        for entity_name in self.CRISIS_ENTITIES.keys():
            # Special handling for ambiguous short names
            if entity_name in ambiguous_names:
                pattern = ambiguous_names[entity_name]
                if re.search(pattern, text_lower):
                    entities.add(entity_name)
            else:
                # Standard case-insensitive matching with word boundaries
                if re.search(r'\b' + re.escape(entity_name.lower()) + r'\b', text_lower):
                    entities.add(entity_name)

        return entities

    def classify_event_type(self, headline: str, capital_iq_type: str) -> str:
        """Classify event type using headline analysis + Capital IQ type"""
        if pd.isna(headline):
            return 'unknown'

        headline_lower = headline.lower()

        # Check patterns in order of priority
        for event_type, patterns in self.EVENT_PATTERNS.items():
            for pattern in patterns:
                if pattern in headline_lower:
                    return event_type

        # Fallback: use Capital IQ type with comprehensive mapping
        if pd.notna(capital_iq_type):
            capital_iq_lower = capital_iq_type.lower()

            # M&A related
            if any(term in capital_iq_lower for term in ['m&a', 'acquisition', 'merger', 'closing', 'rumor', 'divestiture', 'spin-off']):
                return 'merger_acquisition'

            # Earnings & financial performance
            elif any(term in capital_iq_lower for term in ['earnings', 'guidance', 'sales', 'trading statement', 'results']):
                return 'earnings_announcement'

            # Management & board changes
            elif any(term in capital_iq_lower for term in ['executive', 'board', 'director', 'officer', 'management']):
                return 'management_change'

            # Capital raising & financing
            elif any(term in capital_iq_lower for term in ['fixed income', 'debt financing', 'private placement', 'offering', 'ipo', 'follow-on']):
                return 'capital_raising'

            # Buybacks & stock movements
            elif any(term in capital_iq_lower for term in ['buyback', 'repurchase', 'dividend', 'split', 'stock']):
                return 'stock_movement'

            # Credit events
            elif any(term in capital_iq_lower for term in ['credit', 'rating', 'default', 'covenant']):
                return 'credit_downgrade'

            # Restructuring & downsizing
            elif any(term in capital_iq_lower for term in ['restructur', 'downsi', 'discontin', 'reorgan', 'layoff']):
                return 'restructuring'

            # Bankruptcy & insolvency
            elif any(term in capital_iq_lower for term in ['bankruptcy', 'insolvency', 'liquidation', 'administration', 'receivership']):
                return 'bankruptcy'

            # Strategic actions
            elif any(term in capital_iq_lower for term in ['strategic alliance', 'joint venture', 'partnership']):
                return 'strategic_partnership'

            # Legal & regulatory
            elif any(term in capital_iq_lower for term in ['lawsuit', 'legal', 'litigation', 'settlement', 'regulatory']):
                return 'legal_issue'

            # Business operations (less crisis-relevant, but classify them)
            elif any(term in capital_iq_lower for term in ['expansion', 'client', 'product', 'contract', 'facility']):
                return 'business_operations'

        return 'unknown'

    def infer_event_severity(self, event_type: str, headline: str) -> str:
        """Infer event severity from type and headline keywords"""
        if event_type in ['bankruptcy', 'government_intervention']:
            return 'critical'

        headline_lower = headline.lower() if not pd.isna(headline) else ''

        critical_keywords = ['bankruptcy', 'collapse', 'bailout', 'emergency', 'rescue']
        high_keywords = ['downgrade', 'loss', 'writedown', 'default']
        medium_keywords = ['acquisition', 'merger', 'restructuring']

        if any(kw in headline_lower for kw in critical_keywords):
            return 'critical'
        elif any(kw in headline_lower for kw in high_keywords):
            return 'high'
        elif any(kw in headline_lower for kw in medium_keywords):
            return 'medium'
        else:
            return 'low'

    def convert_to_feekg_format(self, df: pd.DataFrame, output_file: str):
        """Convert DataFrame to FE-EKG JSON format with entity extraction"""
        print(f"\n🔄 Converting to FE-EKG format...")

        events = []
        all_entities = defaultdict(set)  # entity_name -> set of event_ids where it appears

        for idx, row in df.iterrows():
            # Extract entities from headline
            entities_in_headline = self.extract_entities_from_text(row['headline'])

            # Classify event type
            event_type = self.classify_event_type(row['headline'], row.get('eventtype', ''))

            # Infer severity
            severity = self.infer_event_severity(event_type, row['headline'])

            event = {
                'eventId': f"evt_{idx}",
                'date': str(row['announcedate'])[:10],  # YYYY-MM-DD
                'type': event_type,
                'severity': severity,
                'actor': str(row.get('companyname', 'unknown')),
                'headline': str(row.get('headline', '')),
                'description': str(row.get('headline', '')),  # Capital IQ doesn't have separate description
                'source': str(row.get('sourcetypename', 'Capital IQ')),
                'entities': list(entities_in_headline)
            }

            # Track entity appearances
            for entity in entities_in_headline:
                all_entities[entity].add(event['eventId'])

            events.append(event)

        # Create entities list with types
        entities = []
        for entity_idx, (entity_name, event_ids) in enumerate(sorted(all_entities.items())):
            entities.append({
                'entityId': f"ent_{entity_idx:03d}",
                'name': entity_name,
                'type': self.CRISIS_ENTITIES.get(entity_name, 'company'),
                'event_count': len(event_ids)  # Track how many events mention this entity
            })

        # Create output structure
        output = {
            'metadata': {
                'source': 'Capital IQ',
                'processor_version': 'v2_optimized',
                'created_at': datetime.now().isoformat(),
                'events_count': len(events),
                'entities_count': len(entities),
                'date_range': {
                    'start': str(df['announcedate'].min())[:10],
                    'end': str(df['announcedate'].max())[:10]
                }
            },
            'events': events,
            'entities': entities
        }

        # Save to file
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        with open(output_file, 'w') as f:
            json.dump(output, f, indent=2)

        print(f"\n✅ Saved {len(events)} events and {len(entities)} entities to: {output_file}")

        # Print statistics
        print(f"\n📊 Output Statistics:")
        print(f"   Events: {len(events):,}")
        print(f"   Entities: {len(entities)}")
        print(f"   Event type distribution:")
        type_counts = pd.Series([e['type'] for e in events]).value_counts()
        for event_type, count in type_counts.head(10).items():
            print(f"      {event_type:30} : {count:4} events")

        print(f"\n   Entities extracted:")
        for entity in entities[:10]:
            print(f"      {entity['name']:30} ({entity['type']:15}) - {entity['event_count']} events")

        return output


def main():
    parser = argparse.ArgumentParser(description='Process Capital IQ data (v2 - optimized)')
    parser.add_argument('--input', required=True, help='Input CSV/Excel file')
    parser.add_argument('--output', default='data/capital_iq_processed/lehman_case_study_v2.json',
                       help='Output JSON file')

    args = parser.parse_args()

    print("=" * 70)
    print("  Capital IQ ETL Pipeline v2 (Optimized)")
    print("=" * 70)

    # Check if input file exists
    if not os.path.exists(args.input):
        print(f"❌ Error: File not found: {args.input}")
        sys.exit(1)

    # Process data
    processor = CapitalIQProcessorV2(args.input)

    # Extract crisis events
    crisis_events = processor.extract_lehman_crisis_events()

    # Convert to FE-EKG format
    output = processor.convert_to_feekg_format(crisis_events, args.output)

    print("\n" + "=" * 70)
    print("  ETL Complete!")
    print("=" * 70)
    print(f"\n✅ Processed data ready: {args.output}")
    print(f"\nNext steps:")
    print(f"  1. Review output file")
    print(f"  2. Load into Neo4j: python ingestion/load_lehman.py --input {args.output}")
    print("=" * 70 + "\n")


if __name__ == '__main__':
    main()
