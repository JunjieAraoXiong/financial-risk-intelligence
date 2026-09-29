#!/usr/bin/env python3
"""
Efficient FEEKG Analyzer - Fast queries and analysis

Provides pre-built queries for common analysis tasks
"""
import os
import requests
import json
from typing import List, Dict, Optional
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

class FEEKGAnalyzer:
    """Efficient analyzer for FEEKG AllegroGraph data"""

    def __init__(self):
        self.base_url = os.getenv('AG_URL', 'https://qa-agraph.nelumbium.ai/').rstrip('/')
        self.user = os.getenv('AG_USER')
        self.password = os.getenv('AG_PASS')
        self.catalog = os.getenv('AG_CATALOG', 'mycatalog')
        self.repo = os.getenv('AG_REPO', 'FEEKG')

        self.repo_url = f"{self.base_url}/catalogs/{self.catalog}/repositories/{self.repo}"
        self.auth = (self.user, self.password)

    def query(self, sparql: str) -> List[Dict]:
        """Execute SPARQL query and return results"""
        try:
            response = requests.get(
                self.repo_url,
                params={'query': sparql},
                headers={'Accept': 'application/sparql-results+json'},
                auth=self.auth,
                timeout=30
            )
            response.raise_for_status()
            result = response.json()
            return result.get('results', {}).get('bindings', [])
        except Exception as e:
            print(f"Query failed: {e}")
            return []

    # ========== ENTITY QUERIES ==========

    def get_all_entities(self) -> List[Dict]:
        """Get all entities with their properties"""
        query = """
        PREFIX feekg: <http://feekg.org/ontology#>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

        SELECT ?entity ?label ?type
        WHERE {
            ?entity a feekg:Entity .
            ?entity rdfs:label ?label .
            OPTIONAL { ?entity feekg:entityType ?type . }
        }
        ORDER BY ?label
        """
        return self.query(query)

    def get_entity_by_name(self, name: str) -> Optional[Dict]:
        """Find entity by name (case-insensitive)"""
        query = f"""
        PREFIX feekg: <http://feekg.org/ontology#>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

        SELECT ?entity ?label ?type
        WHERE {{
            ?entity a feekg:Entity .
            ?entity rdfs:label ?label .
            FILTER(CONTAINS(LCASE(?label), LCASE("{name}")))
            OPTIONAL {{ ?entity feekg:entityType ?type . }}
        }}
        LIMIT 1
        """
        results = self.query(query)
        return results[0] if results else None

    def get_entity_events(self, entity_name: str) -> List[Dict]:
        """Get all events involving an entity"""
        query = f"""
        PREFIX feekg: <http://feekg.org/ontology#>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

        SELECT ?event ?date ?eventType ?label
        WHERE {{
            ?entity rdfs:label ?entityLabel .
            FILTER(CONTAINS(LCASE(?entityLabel), LCASE("{entity_name}")))
            ?event feekg:involves ?entity .
            ?event a feekg:Event .
            ?event feekg:date ?date .
            ?event feekg:eventType ?eventType .
            ?event rdfs:label ?label .
        }}
        ORDER BY ?date
        """
        return self.query(query)

    # ========== EVENT QUERIES ==========

    def get_events_by_date_range(self, start_date: str, end_date: str) -> List[Dict]:
        """Get events within date range (format: YYYY-MM-DD)"""
        query = f"""
        PREFIX feekg: <http://feekg.org/ontology#>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

        SELECT ?event ?date ?eventType ?label ?severity
        WHERE {{
            ?event a feekg:Event .
            ?event feekg:date ?date .
            ?event feekg:eventType ?eventType .
            ?event rdfs:label ?label .
            OPTIONAL {{ ?event feekg:severity ?severity . }}
            FILTER(?date >= "{start_date}"^^xsd:date && ?date <= "{end_date}"^^xsd:date)
        }}
        ORDER BY ?date
        """
        return self.query(query)

    def get_events_by_type(self, event_type: str, limit: int = 50) -> List[Dict]:
        """Get events of specific type"""
        query = f"""
        PREFIX feekg: <http://feekg.org/ontology#>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

        SELECT ?event ?date ?label ?severity
        WHERE {{
            ?event a feekg:Event .
            ?event feekg:eventType "{event_type}" .
            ?event feekg:date ?date .
            ?event rdfs:label ?label .
            OPTIONAL {{ ?event feekg:severity ?severity . }}
        }}
        ORDER BY ?date
        LIMIT {limit}
        """
        return self.query(query)

    def get_events_by_severity(self, severity: str = "high") -> List[Dict]:
        """Get high-severity events"""
        query = f"""
        PREFIX feekg: <http://feekg.org/ontology#>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

        SELECT ?event ?date ?eventType ?label
        WHERE {{
            ?event a feekg:Event .
            ?event feekg:severity "{severity}" .
            ?event feekg:date ?date .
            ?event feekg:eventType ?eventType .
            ?event rdfs:label ?label .
        }}
        ORDER BY ?date
        """
        return self.query(query)

    # ========== TIMELINE ANALYSIS ==========

    def get_event_timeline(self, entity_name: str) -> List[Dict]:
        """Get chronological timeline of events for an entity"""
        query = f"""
        PREFIX feekg: <http://feekg.org/ontology#>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

        SELECT ?date ?eventType ?severity ?label
        WHERE {{
            ?entity rdfs:label ?entityLabel .
            FILTER(CONTAINS(LCASE(?entityLabel), LCASE("{entity_name}")))
            ?event feekg:involves ?entity .
            ?event feekg:date ?date .
            ?event feekg:eventType ?eventType .
            ?event rdfs:label ?label .
            OPTIONAL {{ ?event feekg:severity ?severity . }}
        }}
        ORDER BY ?date
        """
        return self.query(query)

    def get_crisis_events(self, start_date: str = "2008-01-01", end_date: str = "2009-12-31") -> List[Dict]:
        """Get crisis-related events (high/critical severity)"""
        query = f"""
        PREFIX feekg: <http://feekg.org/ontology#>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

        SELECT ?date ?eventType ?severity ?label ?actor
        WHERE {{
            ?event a feekg:Event .
            ?event feekg:severity ?severity .
            FILTER(?severity IN ("high", "critical"))
            ?event feekg:date ?date .
            FILTER(?date >= "{start_date}"^^xsd:date && ?date <= "{end_date}"^^xsd:date)
            ?event feekg:eventType ?eventType .
            ?event rdfs:label ?label .
            OPTIONAL {{ ?event feekg:actor ?actor . }}
        }}
        ORDER BY ?date
        """
        return self.query(query)

    # ========== STATISTICS ==========

    def get_event_type_distribution(self) -> Dict[str, int]:
        """Get count of events by type"""
        query = """
        PREFIX feekg: <http://feekg.org/ontology#>

        SELECT ?eventType (COUNT(?event) as ?count)
        WHERE {
            ?event a feekg:Event .
            ?event feekg:eventType ?eventType .
        }
        GROUP BY ?eventType
        ORDER BY DESC(?count)
        """
        results = self.query(query)
        return {
            r['eventType']['value']: int(r['count']['value'])
            for r in results
        }

    def get_severity_distribution(self) -> Dict[str, int]:
        """Get count of events by severity"""
        query = """
        PREFIX feekg: <http://feekg.org/ontology#>

        SELECT ?severity (COUNT(?event) as ?count)
        WHERE {
            ?event a feekg:Event .
            ?event feekg:severity ?severity .
        }
        GROUP BY ?severity
        ORDER BY DESC(?count)
        """
        results = self.query(query)
        return {
            r['severity']['value']: int(r['count']['value'])
            for r in results
        }

    def get_monthly_event_counts(self, year: int = 2008) -> Dict[str, int]:
        """Get event count per month for a given year"""
        query = f"""
        PREFIX feekg: <http://feekg.org/ontology#>

        SELECT (SUBSTR(?date, 1, 7) as ?month) (COUNT(?event) as ?count)
        WHERE {{
            ?event a feekg:Event .
            ?event feekg:date ?date .
            FILTER(YEAR(?date) = {year})
        }}
        GROUP BY (SUBSTR(?date, 1, 7))
        ORDER BY ?month
        """
        results = self.query(query)
        return {
            r['month']['value']: int(r['count']['value'])
            for r in results
        }

    # ========== EXPORT ==========

    def export_to_json(self, results: List[Dict], filename: str):
        """Export query results to JSON file"""
        # Simplify the results structure
        simplified = []
        for r in results:
            item = {}
            for key, value in r.items():
                item[key] = value.get('value', '')
            simplified.append(item)

        with open(filename, 'w') as f:
            json.dump(simplified, f, indent=2)

        print(f"✓ Exported {len(simplified)} records to {filename}")

    # ========== DISPLAY HELPERS ==========

    def display_results(self, results: List[Dict], limit: int = 10):
        """Pretty print query results"""
        if not results:
            print("No results found")
            return

        print(f"\nFound {len(results)} results (showing first {min(limit, len(results))}):\n")

        for i, result in enumerate(results[:limit], 1):
            print(f"{i}.")
            for key, value in result.items():
                val = value.get('value', 'N/A')
                # Shorten URIs
                if val.startswith('http'):
                    val = val.split('#')[-1].split('/')[-1]
                print(f"  {key}: {val}")
            print()


# ========== COMMAND LINE INTERFACE ==========

def main():
    import argparse

    parser = argparse.ArgumentParser(description='Efficient FEEKG Analyzer')
    parser.add_argument('command', choices=[
        'entities', 'entity-events', 'events-by-date',
        'events-by-type', 'high-severity', 'crisis-events',
        'timeline', 'stats'
    ])
    parser.add_argument('--entity', help='Entity name')
    parser.add_argument('--start', help='Start date (YYYY-MM-DD)')
    parser.add_argument('--end', help='End date (YYYY-MM-DD)')
    parser.add_argument('--type', help='Event type')
    parser.add_argument('--severity', default='high', help='Severity level')
    parser.add_argument('--export', help='Export to JSON file')
    parser.add_argument('--limit', type=int, default=50, help='Result limit')

    args = parser.parse_args()

    analyzer = FEEKGAnalyzer()

    # Execute command
    results = []

    if args.command == 'entities':
        results = analyzer.get_all_entities()

    elif args.command == 'entity-events':
        if not args.entity:
            print("Error: --entity required")
            return
        results = analyzer.get_entity_events(args.entity)

    elif args.command == 'events-by-date':
        if not args.start or not args.end:
            print("Error: --start and --end dates required")
            return
        results = analyzer.get_events_by_date_range(args.start, args.end)

    elif args.command == 'events-by-type':
        if not args.type:
            print("Error: --type required")
            return
        results = analyzer.get_events_by_type(args.type, args.limit)

    elif args.command == 'high-severity':
        results = analyzer.get_events_by_severity(args.severity)

    elif args.command == 'crisis-events':
        start = args.start or "2008-01-01"
        end = args.end or "2009-12-31"
        results = analyzer.get_crisis_events(start, end)

    elif args.command == 'timeline':
        if not args.entity:
            print("Error: --entity required")
            return
        results = analyzer.get_event_timeline(args.entity)

    elif args.command == 'stats':
        print("\n=== Event Type Distribution ===")
        dist = analyzer.get_event_type_distribution()
        for event_type, count in list(dist.items())[:10]:
            print(f"{event_type:30} {count:>6,}")

        print("\n=== Severity Distribution ===")
        sev = analyzer.get_severity_distribution()
        for severity, count in sev.items():
            print(f"{severity:30} {count:>6,}")

        print("\n=== 2008 Monthly Events ===")
        monthly = analyzer.get_monthly_event_counts(2008)
        for month, count in monthly.items():
            print(f"{month:30} {count:>6,}")
        return

    # Display or export results
    if args.export:
        analyzer.export_to_json(results, args.export)
    else:
        analyzer.display_results(results, args.limit)


if __name__ == '__main__':
    main()
