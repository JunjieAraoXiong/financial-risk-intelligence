#!/usr/bin/env python3
"""
Capital IQ Data Processing Pipeline

Process bulk Capital IQ data and extract specific case studies.

Usage:
    # Load all data
    python ingestion/process_capital_iq.py --input data/capital_iq_raw/financial_crisis_2007_2009.xlsx

    # Extract Lehman Brothers case study
    python ingestion/process_capital_iq.py --input data/capital_iq_raw/financial_crisis_2007_2009.xlsx --filter lehman

    # Search for specific companies
    python ingestion/process_capital_iq.py --input data/capital_iq_raw/financial_crisis_2007_2009.xlsx --companies "Lehman Brothers,AIG,Bear Stearns"
"""

import pandas as pd
import json
import os
import sys
import argparse
from datetime import datetime
from typing import List, Dict, Optional


class CapitalIQProcessor:
    """
    Process Capital IQ bulk data

    Supports:
    - Loading Excel/CSV files
    - Filtering by company, date, event type
    - Extracting case studies
    - Converting to FE-EKG format
    """

    def __init__(self, input_file: str):
        """
        Initialize processor

        Args:
            input_file: Path to Capital IQ export (Excel or CSV)
        """
        self.input_file = input_file
        self.df = None
        self.load_data()

    def load_data(self):
        """Load Capital IQ data from file"""
        print(f"Loading data from: {self.input_file}")

        if self.input_file.endswith('.xlsx'):
            self.df = pd.read_excel(self.input_file)
        elif self.input_file.endswith('.csv'):
            # Try different encodings and handle CSV parsing issues
            try:
                self.df = pd.read_csv(self.input_file, encoding='utf-8', on_bad_lines='skip')
            except:
                try:
                    self.df = pd.read_csv(self.input_file, encoding='latin-1', on_bad_lines='skip')
                except:
                    self.df = pd.read_csv(self.input_file, encoding='ISO-8859-1', on_bad_lines='skip')
        else:
            raise ValueError("File must be .xlsx or .csv")

        print(f"✅ Loaded {len(self.df)} events")
        print(f"✅ Columns: {list(self.df.columns)}")

        # Normalize column names (Capital IQ uses different naming)
        self.df.columns = [self._normalize_column_name(col) for col in self.df.columns]

    def _normalize_column_name(self, col: str) -> str:
        """Normalize column names to standard format"""
        # Map common Capital IQ column names to our standard
        column_map = {
            'company name': 'company',
            'companyname': 'company',
            'event date': 'date',
            'eventdate': 'date',
            'announcement date': 'date',
            'announcedate': 'date',  # Real Capital IQ format
            'event type': 'event_type',
            'eventtype': 'event_type',
            'key development type': 'event_type',
            'headline': 'headline',
            'event headline': 'headline',
            'summary': 'description',
            'description': 'description',
            'event description': 'description',
            'key parties': 'entities',
            'related companies': 'entities',
            'source': 'source',
            'sourcetypename': 'source',  # Real Capital IQ format
            'objectroletype': 'role'  # Real Capital IQ format
        }

        col_lower = col.lower().strip()
        return column_map.get(col_lower, col_lower.replace(' ', '_'))

    def get_statistics(self) -> Dict:
        """Get dataset statistics"""
        # Convert date column to datetime first
        if 'date' in self.df.columns:
            self.df['date'] = pd.to_datetime(self.df['date'], errors='coerce')

        stats = {
            'total_events': len(self.df),
            'date_range': {
                'start': str(self.df['date'].min()) if 'date' in self.df.columns and not self.df['date'].isna().all() else 'N/A',
                'end': str(self.df['date'].max()) if 'date' in self.df.columns and not self.df['date'].isna().all() else 'N/A'
            },
            'unique_companies': self.df['company'].nunique() if 'company' in self.df.columns else 0,
            'event_types': self.df['event_type'].value_counts().head(10).to_dict() if 'event_type' in self.df.columns else {},
            'columns': list(self.df.columns)
        }

        return stats

    def filter_by_company(self, companies: List[str]) -> pd.DataFrame:
        """
        Filter events by company name

        Args:
            companies: List of company names (case-insensitive, partial match)

        Returns:
            Filtered DataFrame
        """
        if 'company' not in self.df.columns:
            print("⚠️  Warning: No 'company' column found")
            return self.df

        # Case-insensitive partial matching
        mask = self.df['company'].str.lower().str.contains('|'.join([c.lower() for c in companies]), na=False)
        filtered = self.df[mask].copy()

        print(f"✅ Filtered to {len(filtered)} events for: {', '.join(companies)}")
        return filtered

    def filter_by_date_range(self, start_date: str, end_date: str) -> pd.DataFrame:
        """Filter events by date range"""
        if 'date' not in self.df.columns:
            print("⚠️  Warning: No 'date' column found")
            return self.df

        self.df['date'] = pd.to_datetime(self.df['date'])
        mask = (self.df['date'] >= start_date) & (self.df['date'] <= end_date)
        filtered = self.df[mask].copy()

        print(f"✅ Filtered to {len(filtered)} events from {start_date} to {end_date}")
        return filtered

    def filter_by_event_type(self, event_types: List[str]) -> pd.DataFrame:
        """Filter by event types"""
        if 'event_type' not in self.df.columns:
            print("⚠️  Warning: No 'event_type' column found")
            return self.df

        mask = self.df['event_type'].str.lower().str.contains('|'.join([et.lower() for et in event_types]), na=False)
        filtered = self.df[mask].copy()

        print(f"✅ Filtered to {len(filtered)} events of types: {', '.join(event_types)}")
        return filtered

    def extract_lehman_case_study(self) -> pd.DataFrame:
        """
        Extract Lehman Brothers case study

        Includes:
        - Lehman Brothers events
        - Bear Stearns (precursor)
        - Related systemic events
        """
        print("\n" + "=" * 70)
        print("  Extracting Lehman Brothers Case Study")
        print("=" * 70)

        # Key entities related to Lehman crisis
        lehman_entities = [
            'Lehman Brothers',
            'Bear Stearns',
            'AIG',
            'Merrill Lynch',
            'Bank of America',
            'Barclays',
            'JPMorgan'
        ]

        # Filter by companies
        filtered = self.filter_by_company(lehman_entities)

        # Filter by date (2007-2009)
        if 'date' in filtered.columns:
            filtered = filtered[
                (pd.to_datetime(filtered['date']) >= '2007-01-01') &
                (pd.to_datetime(filtered['date']) <= '2009-12-31')
            ]

        # Sort by date
        if 'date' in filtered.columns:
            filtered = filtered.sort_values('date')

        print(f"\n✅ Extracted {len(filtered)} events for Lehman case study")

        return filtered

    def convert_to_feekg_format(self, df: pd.DataFrame, output_file: str):
        """
        Convert DataFrame to FE-EKG JSON format

        Args:
            df: Filtered DataFrame
            output_file: Output JSON file path
        """
        print(f"\nConverting to FE-EKG format...")

        events = []
        entities_set = set()

        for idx, row in df.iterrows():
            event = {
                'eventId': f"evt_{idx:03d}",
                'date': str(row.get('date', ''))[:10],  # YYYY-MM-DD
                'type': self._normalize_event_type(str(row.get('event_type', 'unknown'))),
                'actor': str(row.get('company', 'unknown')),
                'description': str(row.get('description', row.get('headline', ''))),
                'headline': str(row.get('headline', '')),
                'source': str(row.get('source', 'Capital IQ')),
                'entities': []
            }

            # Extract entities
            if 'entities' in row and pd.notna(row['entities']):
                event['entities'] = [e.strip() for e in str(row['entities']).split(';')]
            else:
                event['entities'] = [event['actor']]

            # Add to entities set
            entities_set.update(event['entities'])

            events.append(event)

        # Create entities list
        entities = []
        for idx, entity_name in enumerate(sorted(entities_set)):
            entities.append({
                'entityId': f"ent_{idx:03d}",
                'name': entity_name,
                'type': self._infer_entity_type(entity_name)
            })

        # Create output structure
        output = {
            'metadata': {
                'source': 'Capital IQ',
                'created_at': datetime.now().isoformat(),
                'events_count': len(events),
                'entities_count': len(entities)
            },
            'events': events,
            'entities': entities
        }

        # Save to file
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        with open(output_file, 'w') as f:
            json.dump(output, f, indent=2)

        print(f"✅ Saved {len(events)} events and {len(entities)} entities to: {output_file}")

        return output

    def _normalize_event_type(self, event_type: str) -> str:
        """Normalize event type to FE-EKG taxonomy"""
        event_type_lower = event_type.lower()

        type_map = {
            'bankruptcy': 'bankruptcy',
            'chapter 11': 'bankruptcy',
            'restructuring': 'restructuring',
            'credit rating': 'credit_downgrade',
            'downgrade': 'credit_downgrade',
            'upgrade': 'credit_upgrade',
            'earnings': 'earnings_announcement',
            'guidance': 'earnings_warning',
            'loss': 'earnings_loss',
            'merger': 'merger_acquisition',
            'acquisition': 'merger_acquisition',
            'm&a': 'merger_acquisition',
            'bailout': 'government_intervention',
            'rescue': 'government_intervention',
            'stock': 'stock_movement',
            'share price': 'stock_movement',
            'management': 'management_change',
            'ceo': 'management_change',
            'regulation': 'regulatory_action'
        }

        for key, value in type_map.items():
            if key in event_type_lower:
                return value

        return 'unknown'

    def _infer_entity_type(self, entity_name: str) -> str:
        """Infer entity type from name"""
        name_lower = entity_name.lower()

        if any(word in name_lower for word in ['bank', 'jpmorgan', 'citigroup', 'wells fargo']):
            return 'bank'
        elif any(word in name_lower for word in ['brothers', 'lynch', 'sachs', 'stanley']):
            return 'investment_bank'
        elif any(word in name_lower for word in ['aig', 'insurance']):
            return 'insurance'
        elif any(word in name_lower for word in ['federal reserve', 'treasury', 'government', 'fed']):
            return 'regulator'
        else:
            return 'company'


def main():
    parser = argparse.ArgumentParser(description='Process Capital IQ bulk data')
    parser.add_argument('--input', required=True, help='Input file (Excel or CSV)')
    parser.add_argument('--output', default='data/capital_iq_processed/lehman_case_study.json',
                       help='Output JSON file')
    parser.add_argument('--filter', choices=['lehman', 'all'], default='lehman',
                       help='Filter type')
    parser.add_argument('--companies', help='Comma-separated list of companies')

    args = parser.parse_args()

    # Check if input file exists
    if not os.path.exists(args.input):
        print(f"❌ Error: File not found: {args.input}")
        print("\n📖 See data/CAPITAL_IQ_DOWNLOAD_GUIDE.md for download instructions")
        sys.exit(1)

    # Load data
    processor = CapitalIQProcessor(args.input)

    # Show statistics
    print("\n" + "=" * 70)
    print("  Dataset Statistics")
    print("=" * 70)
    stats = processor.get_statistics()
    print(f"Total events: {stats['total_events']}")
    print(f"Date range: {stats['date_range']['start']} to {stats['date_range']['end']}")
    print(f"Unique companies: {stats['unique_companies']}")
    print(f"Columns: {', '.join(stats['columns'])}")

    # Apply filters
    if args.filter == 'lehman':
        filtered_df = processor.extract_lehman_case_study()
    elif args.companies:
        companies = [c.strip() for c in args.companies.split(',')]
        filtered_df = processor.filter_by_company(companies)
    else:
        filtered_df = processor.df

    # Convert to FE-EKG format
    processor.convert_to_feekg_format(filtered_df, args.output)

    print("\n" + "=" * 70)
    print("  Success!")
    print("=" * 70)
    print(f"\n✅ Processed Capital IQ data")
    print(f"✅ Output: {args.output}")
    print(f"\nNext steps:")
    print(f"  1. Review the output file")
    print(f"  2. Load into FE-EKG: python ingestion/load_lehman.py")
    print(f"  3. Generate visualizations")
    print("=" * 70 + "\n")


if __name__ == '__main__':
    main()
