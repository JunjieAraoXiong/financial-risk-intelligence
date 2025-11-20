#!/usr/bin/env python3
"""
Capital IQ ETL Pipeline v4 - Entity Deduplication

Improvements over v3:
- Entity alias resolution (AIG vs American International Group)
- Canonical entity naming throughout pipeline
- Consolidated entity references in graph

Usage:
    python ingestion/process_capital_iq_v4.py \
        --input data/capital_iq_raw/capital_iq_download.csv \
        --output data/capital_iq_processed/lehman_v4_deduped.json
"""

import pandas as pd
import json
import os
import sys
import argparse
from datetime import datetime
from typing import List, Dict, Set, Optional, Tuple
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from ingestion.process_capital_iq_v3 import CapitalIQProcessorV3
from shared.config.entity_aliases import get_canonical_name, get_all_aliases


class CapitalIQProcessorV4(CapitalIQProcessorV3):
    """
    Enhanced processor with entity deduplication:
    - Resolves entity aliases to canonical names
    - Prevents duplicate entities in graph (e.g., AIG vs American International Group)
    - Updates CRISIS_ENTITIES with all known aliases
    """

    # Expanded CRISIS_ENTITIES with all aliases for better detection
    CRISIS_ENTITIES_EXPANDED = {
        # AIG variations (canonical: AIG)
        'AIG': 'insurance',
        'American International Group': 'insurance',
        'American International Group Inc.': 'insurance',
        'American International Group, Inc.': 'insurance',

        # JPMorgan variations (canonical: JPMorgan)
        'JPMorgan': 'bank',
        'JP Morgan': 'bank',
        'JPMorgan Chase': 'bank',
        'JP Morgan Chase': 'bank',
        'JPMorgan Chase & Co.': 'bank',
        'J.P. Morgan': 'bank',

        # Bank of America variations (canonical: Bank of America)
        'Bank of America': 'bank',
        'BofA': 'bank',
        'B of A': 'bank',
        'Bank of America Corporation': 'bank',
        'Bank of America Corp.': 'bank',

        # Lehman Brothers variations (canonical: Lehman Brothers)
        'Lehman Brothers': 'investment_bank',
        'Lehman Brothers Holdings Inc.': 'investment_bank',
        'Lehman Brothers Holdings': 'investment_bank',
        'Lehman Brothers Inc.': 'investment_bank',

        # Bear Stearns variations (canonical: Bear Stearns)
        'Bear Stearns': 'investment_bank',
        'Bear Stearns Companies Inc.': 'investment_bank',
        'Bear Stearns & Co.': 'investment_bank',
        'The Bear Stearns Companies': 'investment_bank',

        # Merrill Lynch variations (canonical: Merrill Lynch)
        'Merrill Lynch': 'investment_bank',
        'Merrill Lynch & Co.': 'investment_bank',
        'Merrill Lynch, Pierce, Fenner & Smith': 'investment_bank',

        # Goldman Sachs variations (canonical: Goldman Sachs)
        'Goldman Sachs': 'investment_bank',
        'Goldman Sachs Group Inc.': 'investment_bank',
        'The Goldman Sachs Group': 'investment_bank',
        'Goldman Sachs & Co.': 'investment_bank',

        # Morgan Stanley variations (canonical: Morgan Stanley)
        'Morgan Stanley': 'investment_bank',
        'Morgan Stanley & Co.': 'investment_bank',
        'Morgan Stanley Inc.': 'investment_bank',

        # Citigroup variations (canonical: Citigroup)
        'Citigroup': 'bank',
        'Citi': 'bank',
        'Citibank': 'bank',
        'Citigroup Inc.': 'bank',
        'Citicorp': 'bank',

        # Barclays variations (canonical: Barclays)
        'Barclays': 'bank',
        'Barclays PLC': 'bank',
        'Barclays plc': 'bank',
        'Barclays Bank': 'bank',
        'Barclays Capital': 'bank',

        # Deutsche Bank variations (canonical: Deutsche Bank)
        'Deutsche Bank': 'bank',
        'Deutsche Bank AG': 'bank',

        # Wells Fargo variations (canonical: Wells Fargo)
        'Wells Fargo': 'bank',
        'Wells Fargo & Company': 'bank',
        'Wells Fargo & Co.': 'bank',
        'Wells Fargo Bank': 'bank',

        # UBS variations (canonical: UBS)
        'UBS': 'bank',
        'UBS AG': 'bank',
        'UBS Group AG': 'bank',

        # Credit Suisse variations (canonical: Credit Suisse)
        'Credit Suisse': 'bank',
        'Credit Suisse Group AG': 'bank',
        'Credit Suisse AG': 'bank',
        'CSFB': 'bank',

        # HSBC variations (canonical: HSBC)
        'HSBC': 'bank',
        'HSBC Holdings plc': 'bank',
        'HSBC Holdings': 'bank',
        'HSBC Bank': 'bank',

        # Wachovia variations (canonical: Wachovia)
        'Wachovia': 'bank',
        'Wachovia Corporation': 'bank',
        'Wachovia Corp.': 'bank',
        'Wachovia Bank': 'bank',

        # Washington Mutual variations (canonical: Washington Mutual)
        'Washington Mutual': 'bank',
        'Washington Mutual Inc.': 'bank',
        'WaMu': 'bank',
        'Washington Mutual Bank': 'bank',

        # Freddie Mac variations (canonical: Freddie Mac)
        'Freddie Mac': 'gse',
        'Federal Home Loan Mortgage Corporation': 'gse',
        'Federal Home Loan Mortgage Corp.': 'gse',
        'FHLMC': 'gse',

        # Fannie Mae variations (canonical: Fannie Mae)
        'Fannie Mae': 'gse',
        'Federal National Mortgage Association': 'gse',
        'Federal National Mortgage Assn.': 'gse',
        'FNMA': 'gse',

        # Regulators
        'Federal Reserve': 'regulator',
        'Fed': 'regulator',
        'Federal Reserve System': 'regulator',
        'The Federal Reserve': 'regulator',

        'Treasury': 'regulator',
        'U.S. Treasury': 'regulator',
        'Department of the Treasury': 'regulator',
        'U.S. Department of the Treasury': 'regulator',

        'SEC': 'regulator',
        'Securities and Exchange Commission': 'regulator',
        'U.S. Securities and Exchange Commission': 'regulator',

        'FDIC': 'regulator',
        'Federal Deposit Insurance Corporation': 'regulator',
    }

    def __init__(self, input_file: str):
        # Call parent init but override CRISIS_ENTITIES
        super().__init__(input_file)
        # Use expanded entity list for better detection
        self.CRISIS_ENTITIES = self.CRISIS_ENTITIES_EXPANDED

    def extract_entities_from_text(self, text: str) -> Set[str]:
        """
        Extract financial entities and return CANONICAL names

        Enhancement over parent:
        - Returns canonical entity names instead of aliases
        - e.g., "American International Group" → "AIG"
        """
        # Use parent method to extract raw entity names
        raw_entities = super().extract_entities_from_text(text)

        # Resolve to canonical names
        canonical_entities = set()
        for entity_name in raw_entities:
            canonical = get_canonical_name(entity_name)
            canonical_entities.add(canonical)

        return canonical_entities

    def process_events_with_source_tracking(self) -> Dict:
        """
        Process events with entity deduplication

        Enhancement over parent:
        - Resolves actor names to canonical form
        - Consolidated entity references
        """
        print(f"\n📊 Processing with entity deduplication...")

        # Extract crisis events
        crisis_df = self.extract_lehman_crisis_events()

        events = []
        entities = {}

        for idx, (df_idx, row) in enumerate(crisis_df.iterrows(), 1):
            if idx % 500 == 0:
                print(f"   Processing event {idx}/{len(crisis_df)}...")

            # Extract entities (now returns canonical names)
            headline = row.get('headline', '')
            extracted_entities = self.extract_entities_from_text(headline)

            # Create canonical entity objects
            for canonical_entity_name in extracted_entities:
                if canonical_entity_name not in entities:
                    entity_id = f"ent_{canonical_entity_name.lower().replace(' ', '_')}"

                    # Get entity type from expanded mapping
                    # Try canonical name first, then try to find any alias
                    entity_type = self.CRISIS_ENTITIES.get(canonical_entity_name)
                    if not entity_type:
                        # Fallback: try all aliases
                        all_aliases = get_all_aliases(canonical_entity_name)
                        for alias in all_aliases:
                            entity_type = self.CRISIS_ENTITIES.get(alias)
                            if entity_type:
                                break
                    if not entity_type:
                        entity_type = 'company'  # Default fallback

                    entities[entity_id] = {
                        'entityId': entity_id,
                        'name': canonical_entity_name,  # Use canonical name
                        'type': entity_type
                    }

            # Classify event with confidence
            capital_iq_type = row.get('eventtype', '')
            event_type, confidence = self.classify_event_type_with_confidence(
                headline,
                capital_iq_type,
                df_idx
            )

            # Infer severity
            severity = self.infer_event_severity(event_type, headline)

            # Resolve actor to canonical name
            raw_actor = row.get('companyname', 'unknown')
            canonical_actor = get_canonical_name(raw_actor)

            # Build event with canonical entity references
            event_id = f"evt_{row.get('keydevid', idx)}"

            event = {
                'eventId': event_id,
                'date': row['announcedate'].strftime('%Y-%m-%d') if pd.notna(row['announcedate']) else None,
                'type': event_type,
                'severity': severity,
                'actor': canonical_actor,  # CANONICAL NAME
                'headline': headline,
                'description': headline,
                'source': row.get('sourcetypename', 'Capital IQ'),
                'entities': list(extracted_entities),  # CANONICAL NAMES

                # CSV source metadata (preserves original for traceability)
                'csvSource': {
                    'filename': os.path.basename(self.input_file),
                    'rowNumber': int(df_idx),
                    'capitalIqId': str(row.get('keydevid', '')),
                    'companyId': str(row.get('companyid', '')),
                    'companyName': raw_actor,  # Keep original for reference
                    'companyNameCanonical': canonical_actor,  # Add canonical version
                    'originalEventType': capital_iq_type,
                    'announceDate': row.get('announcedate').isoformat() if pd.notna(row['announcedate']) else None
                },

                # Classification metadata
                'classification': {
                    'confidence': confidence,
                    'method': 'pattern_match' if confidence >= 0.95 else 'capital_iq_mapping' if confidence >= 0.75 else 'fallback'
                }
            }

            events.append(event)
            self.row_index_map[event_id] = int(df_idx)

        # Calculate statistics
        unknown_count = sum(1 for e in events if e['type'] == 'unknown')
        avg_confidence = sum(e['classification']['confidence'] for e in events) / len(events) if events else 0

        print(f"\n   ✅ Processed {len(events)} events")
        print(f"   ✅ Extracted {len(entities)} unique entities (deduplicated)")
        print(f"   ✅ Unknown events: {unknown_count} ({(unknown_count/len(events)*100):.1f}%)")
        print(f"   ✅ Avg confidence: {avg_confidence:.2%}")

        return {
            'metadata': {
                'source': 'Capital IQ',
                'processor_version': 'v4_deduped',
                'created_at': datetime.now().isoformat(),
                'events_count': len(events),
                'entities_count': len(entities),
                'unknown_events_count': unknown_count,
                'avg_classification_confidence': round(avg_confidence, 3),
                'date_range': {
                    'start': crisis_df['announcedate'].min().strftime('%Y-%m-%d'),
                    'end': crisis_df['announcedate'].max().strftime('%Y-%m-%d')
                },
                'enhancements': {
                    'entity_deduplication': True,
                    'canonical_naming': True,
                    'alias_resolution': True
                }
            },
            'events': events,
            'entities': list(entities.values())
        }


def main():
    parser = argparse.ArgumentParser(
        description='Process Capital IQ data with entity deduplication'
    )
    parser.add_argument(
        '--input',
        default='data/capital_iq_raw/capital_iq_download.csv',
        help='Input CSV file'
    )
    parser.add_argument(
        '--output',
        default='data/capital_iq_processed/lehman_v4_deduped.json',
        help='Output JSON file'
    )

    args = parser.parse_args()

    print("\n" + "=" * 70)
    print("  Capital IQ ETL Pipeline v4 - Entity Deduplication")
    print("=" * 70)

    # Process
    processor = CapitalIQProcessorV4(args.input)
    data = processor.process_events_with_source_tracking()

    # Save
    output_dir = os.path.dirname(args.output)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)

    with open(args.output, 'w') as f:
        json.dump(data, f, indent=2)

    print(f"\n✅ Saved to: {args.output}")
    print(f"\nQuality Metrics:")
    print(f"  • Total events: {data['metadata']['events_count']:,}")
    print(f"  • Unique entities: {data['metadata']['entities_count']} (deduplicated)")
    print(f"  • Unknown events: {data['metadata']['unknown_events_count']} ({(data['metadata']['unknown_events_count']/data['metadata']['events_count']*100):.1f}%)")
    print(f"  • Avg confidence: {data['metadata']['avg_classification_confidence']:.1%}")
    print(f"  • Entity deduplication: ✅ Enabled")
    print("=" * 70 + "\n")


if __name__ == '__main__':
    main()
