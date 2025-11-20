#!/usr/bin/env python3
"""
Optimized Capital IQ to AllegroGraph Loader

Loads all Capital IQ processed files from data/capital_iq_processed/
and converts them to RDF triples in AllegroGraph.

Features:
- Batch processing for large files (4000+ events)
- RDF/Turtle format for efficient upload
- Evolution link computation
- Progress tracking

Usage:
    # Load all files
    python ingestion/load_capital_iq_to_allegrograph.py

    # Load specific file
    python ingestion/load_capital_iq_to_allegrograph.py --input lehman_case_study_v2_improved.json

    # Load without clearing existing data
    python ingestion/load_capital_iq_to_allegrograph.py --no-clear
"""

import os
import sys
import json
import argparse
import glob
import requests
from datetime import datetime
from typing import List, Dict, Tuple

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
from evolution.methods import compute_all_evolution_links

load_dotenv()


class AllegroGraphRDFLoader:
    """Optimized RDF loader for AllegroGraph via HTTPS"""

    def __init__(self):
        self.base_url = os.getenv('AG_URL', 'https://qa-agraph.nelumbium.ai/').rstrip('/')
        self.user = os.getenv('AG_USER', 'sadmin')
        self.password = os.getenv('AG_PASS')
        self.catalog = os.getenv('AG_CATALOG', 'mycatalog')
        self.repo = os.getenv('AG_REPO', 'FEEKG')

        # Build repository URL
        self.repo_url = f"{self.base_url}/catalogs/{self.catalog}/repositories/{self.repo}"
        self.statements_url = f"{self.repo_url}/statements"

        self.auth = (self.user, self.password)

        # Namespaces
        self.ns = {
            'feekg': 'http://feekg.org/ontology#',
            'rdf': 'http://www.w3.org/1999/02/22-rdf-syntax-ns#',
            'rdfs': 'http://www.w3.org/2000/01/rdf-schema#',
            'xsd': 'http://www.w3.org/2001/XMLSchema#'
        }

    def get_triple_count(self) -> int:
        """Get current triple count"""
        try:
            response = requests.get(f"{self.repo_url}/size", auth=self.auth, timeout=10)
            response.raise_for_status()
            return int(response.text.strip())
        except Exception as e:
            print(f"   ⚠️  Error getting triple count: {e}")
            return 0

    def clear_repository(self):
        """Clear all triples from repository"""
        try:
            response = requests.delete(self.statements_url, auth=self.auth, timeout=30)
            response.raise_for_status()
            print("   ✅ Repository cleared")
        except Exception as e:
            print(f"   ❌ Failed to clear repository: {e}")
            raise

    def upload_turtle(self, turtle_content: str) -> bool:
        """Upload Turtle content to AllegroGraph"""
        try:
            response = requests.post(
                self.statements_url,
                data=turtle_content.encode('utf-8'),
                headers={'Content-Type': 'text/turtle'},
                auth=self.auth,
                timeout=60
            )
            response.raise_for_status()
            return True
        except Exception as e:
            print(f"   ❌ Upload failed: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"   Response: {e.response.text[:200]}")
            return False

    def upload_turtle_with_retry(self, turtle_content: str, max_retries: int = 3) -> bool:
        """
        Upload Turtle content with retry logic and exponential backoff

        Args:
            turtle_content: Turtle format RDF data
            max_retries: Maximum number of retry attempts (default: 3)

        Returns:
            True if upload succeeded, False otherwise
        """
        import time

        for attempt in range(max_retries):
            try:
                response = requests.post(
                    self.statements_url,
                    data=turtle_content.encode('utf-8'),
                    headers={'Content-Type': 'text/turtle'},
                    auth=self.auth,
                    timeout=120  # Increased timeout for large batches
                )
                response.raise_for_status()
                return True

            except requests.exceptions.Timeout as e:
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt  # Exponential backoff: 1s, 2s, 4s
                    print(f"   ⏰ Timeout. Retrying in {wait_time}s... (attempt {attempt + 1}/{max_retries})")
                    time.sleep(wait_time)
                else:
                    print(f"   ❌ Upload failed after {max_retries} attempts: Timeout")
                    return False

            except requests.exceptions.ConnectionError as e:
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt
                    print(f"   🔌 Connection error. Retrying in {wait_time}s... (attempt {attempt + 1}/{max_retries})")
                    time.sleep(wait_time)
                else:
                    print(f"   ❌ Upload failed after {max_retries} attempts: Connection error")
                    return False

            except requests.exceptions.HTTPError as e:
                # Don't retry on client errors (4xx)
                if e.response.status_code < 500:
                    print(f"   ❌ Upload failed: HTTP {e.response.status_code}")
                    if hasattr(e, 'response') and e.response is not None:
                        print(f"   Response: {e.response.text[:200]}")
                    return False
                else:
                    # Retry on server errors (5xx)
                    if attempt < max_retries - 1:
                        wait_time = 2 ** attempt
                        print(f"   ⚠️  Server error {e.response.status_code}. Retrying in {wait_time}s...")
                        time.sleep(wait_time)
                    else:
                        print(f"   ❌ Upload failed after {max_retries} attempts: Server error")
                        return False

            except Exception as e:
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt
                    print(f"   ⚠️  Unexpected error: {e}. Retrying in {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    print(f"   ❌ Upload failed after {max_retries} attempts: {e}")
                    return False

        return False

    def convert_to_turtle(self, data: Dict, batch_size: int = 500) -> List[str]:
        """
        Convert JSON data to Turtle format in batches

        Args:
            data: Capital IQ JSON data
            batch_size: Number of events per batch

        Returns:
            List of Turtle strings (one per batch)
        """
        batches = []
        events = data['events']
        entities = data['entities']

        # Create namespace prefixes
        header = """@prefix feekg: <http://feekg.org/ontology#> .
@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .

"""

        # Batch 1: Entities (always in first batch)
        entity_triples = []
        for entity in entities:
            entity_id = entity['entityId']
            entity_uri = f"feekg:{entity_id}"

            entity_triples.append(f"{entity_uri} rdf:type feekg:Entity .")
            entity_triples.append(f'{entity_uri} rdfs:label "{self._escape(entity["name"])}" .')
            entity_triples.append(f'{entity_uri} feekg:entityType "{entity["type"]}" .')

        batches.append(header + "\n".join(entity_triples))

        # Batch events in chunks
        for i in range(0, len(events), batch_size):
            batch_events = events[i:i + batch_size]
            event_triples = []

            for event in batch_events:
                event_id = event['eventId']
                event_uri = f"feekg:{event_id}"

                # Core event properties
                event_triples.append(f"{event_uri} rdf:type feekg:Event .")
                event_triples.append(f'{event_uri} feekg:eventType "{event["type"]}" .')
                event_triples.append(f'{event_uri} feekg:date "{event["date"]}"^^xsd:date .')
                event_triples.append(f'{event_uri} rdfs:label "{self._escape(event["headline"][:100])}" .')

                # Optional properties
                if 'description' in event and event['description']:
                    event_triples.append(f'{event_uri} feekg:description "{self._escape(event["description"][:500])}" .')

                if 'actor' in event and event['actor']:
                    event_triples.append(f'{event_uri} feekg:actor "{self._escape(event["actor"])}" .')

                if 'source' in event:
                    event_triples.append(f'{event_uri} feekg:source "{self._escape(event["source"])}" .')

                if 'severity' in event:
                    event_triples.append(f'{event_uri} feekg:severity "{event["severity"]}" .')

                # CSV Source metadata (for traceability back to original CSV)
                if 'csvSource' in event:
                    csv_src = event['csvSource']
                    if 'rowNumber' in csv_src:
                        event_triples.append(f'{event_uri} feekg:csvRowNumber "{csv_src["rowNumber"]}"^^xsd:integer .')
                    if 'filename' in csv_src:
                        event_triples.append(f'{event_uri} feekg:csvFilename "{csv_src["filename"]}" .')
                    if 'capitalIqId' in csv_src:
                        event_triples.append(f'{event_uri} feekg:capitalIqId "{csv_src["capitalIqId"]}" .')
                    if 'companyId' in csv_src:
                        event_triples.append(f'{event_uri} feekg:companyId "{csv_src["companyId"]}" .')
                    if 'companyName' in csv_src:
                        event_triples.append(f'{event_uri} feekg:companyName "{self._escape(csv_src["companyName"])}" .')
                    if 'originalEventType' in csv_src:
                        event_triples.append(f'{event_uri} feekg:originalEventType "{self._escape(csv_src["originalEventType"])}" .')

                # Classification metadata (for quality tracking)
                if 'classification' in event:
                    classification = event['classification']
                    if 'confidence' in classification:
                        event_triples.append(f'{event_uri} feekg:classificationConfidence "{classification["confidence"]:.2f}"^^xsd:float .')
                    if 'method' in classification:
                        event_triples.append(f'{event_uri} feekg:classificationMethod "{classification["method"]}" .')

                # Link to entities
                for entity_name in event.get('entities', []):
                    # Find entity ID
                    entity_id = next((e['entityId'] for e in entities if e['name'] == entity_name), None)
                    if entity_id:
                        entity_uri = f"feekg:{entity_id}"
                        event_triples.append(f"{event_uri} feekg:involves {entity_uri} .")

            if event_triples:
                batches.append(header + "\n".join(event_triples))

        return batches

    def add_evolution_links(self, links: List[Dict]) -> bool:
        """Add evolution links as RDF triples"""
        if not links:
            return True

        # Process in batches
        batch_size = 1000
        for i in range(0, len(links), batch_size):
            batch_links = links[i:i + batch_size]
            triples = []

            header = """@prefix feekg: <http://feekg.org/ontology#> .
@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .

"""

            for link in batch_links:
                from_uri = f"feekg:{link['from']}"
                to_uri = f"feekg:{link['to']}"

                # Main evolution relationship
                triples.append(f"{from_uri} feekg:evolvesTo {to_uri} .")

                # Evolution scores (using blank nodes for structured data)
                link_id = f"_:link_{link['from']}_{link['to']}"
                triples.append(f"{link_id} rdf:type feekg:EvolutionLink .")
                triples.append(f"{link_id} feekg:from {from_uri} .")
                triples.append(f"{link_id} feekg:to {to_uri} .")
                triples.append(f'{link_id} feekg:score "{link["score"]:.4f}"^^xsd:float .')

                # Component scores
                components = link.get('components', {})
                if components:
                    for comp_name, comp_value in components.items():
                        triples.append(f'{link_id} feekg:{comp_name}Score "{comp_value:.4f}"^^xsd:float .')

            turtle = header + "\n".join(triples)
            if not self.upload_turtle_with_retry(turtle, max_retries=3):
                print(f"   ⚠️  Failed to upload evolution link batch {i+1}. Skipping...")
                # Don't return False - continue with other batches
                continue

        return True

    @staticmethod
    def _escape(text: str) -> str:
        """Escape special characters for Turtle format"""
        if not text:
            return ""
        return (text
                .replace('\\', '\\\\')
                .replace('"', '\\"')
                .replace('\n', '\\n')
                .replace('\r', '\\r')
                .replace('\t', '\\t'))


def load_file_to_allegrograph(
    loader: AllegroGraphRDFLoader,
    file_path: str,
    compute_evolution: bool = True
) -> Tuple[int, int, int]:
    """
    Load a single Capital IQ file to AllegroGraph

    Returns:
        (entity_count, event_count, link_count)
    """
    print(f"\n{'='*70}")
    print(f"Loading: {os.path.basename(file_path)}")
    print(f"{'='*70}")

    # Load JSON
    with open(file_path, 'r') as f:
        data = json.load(f)

    metadata = data.get('metadata', {})
    events = data.get('events', [])
    entities = data.get('entities', [])

    print(f"\n1. Data summary:")
    print(f"   - Events: {len(events):,}")
    print(f"   - Entities: {len(entities)}")
    print(f"   - Date range: {metadata.get('date_range', {}).get('start', 'N/A')} to {metadata.get('date_range', {}).get('end', 'N/A')}")

    # Convert to Turtle batches
    print(f"\n2. Converting to RDF (Turtle format)...")
    batches = loader.convert_to_turtle(data, batch_size=500)
    print(f"   ✅ Created {len(batches)} batches")

    # Upload batches with retry and checkpoint tracking
    print(f"\n3. Uploading to AllegroGraph...")
    initial_count = loader.get_triple_count()

    successful_batches = 0
    failed_batches = []

    for i, batch in enumerate(batches, 1):
        print(f"   Batch {i}/{len(batches)}... ", end='', flush=True)
        if loader.upload_turtle_with_retry(batch, max_retries=3):
            print("✅")
            successful_batches += 1
        else:
            print("❌")
            failed_batches.append(i)
            # Continue processing other batches instead of stopping

    new_count = loader.get_triple_count()
    uploaded_count = new_count - initial_count

    if failed_batches:
        print(f"   ⚠️  Uploaded {uploaded_count:,} triples ({successful_batches}/{len(batches)} batches)")
        print(f"   ⚠️  Failed batches: {failed_batches} (continuing anyway)")
    else:
        print(f"   ✅ Uploaded {uploaded_count:,} triples (all {len(batches)} batches successful)")

    # Compute evolution links
    link_count = 0
    if compute_evolution and len(events) > 1:
        print(f"\n4. Computing evolution links...")
        print("   Methods: Temporal, Entity Overlap, Semantic, Topic, Causality, Emotional")

        try:
            links = compute_all_evolution_links(events, entities, threshold=0.5)
            print(f"   ✅ Computed {len(links)} links (score ≥ 0.5)")

            if links:
                print(f"\n5. Uploading evolution links...")
                if loader.add_evolution_links(links):
                    link_count = len(links)
                    final_count = loader.get_triple_count()
                    print(f"   ✅ Uploaded {final_count - new_count:,} evolution triples")
        except Exception as e:
            print(f"   ⚠️  Evolution computation failed: {e}")

    return (len(entities), len(events), link_count)


def main():
    parser = argparse.ArgumentParser(
        description='Load Capital IQ data to AllegroGraph',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Load all files
  python ingestion/load_capital_iq_to_allegrograph.py

  # Load specific file
  python ingestion/load_capital_iq_to_allegrograph.py --input lehman_case_study_v2_improved.json

  # Load without clearing
  python ingestion/load_capital_iq_to_allegrograph.py --no-clear
        """
    )
    parser.add_argument(
        '--input',
        help='Specific JSON file to load (default: load all files in capital_iq_processed/)'
    )
    parser.add_argument(
        '--no-clear',
        action='store_true',
        help='Do not clear existing data before loading'
    )
    parser.add_argument(
        '--no-evolution',
        action='store_true',
        help='Skip evolution link computation (faster for testing)'
    )

    args = parser.parse_args()

    print("\n" + "=" * 70)
    print("  Capital IQ to AllegroGraph Loader")
    print("=" * 70)

    # Initialize loader
    loader = AllegroGraphRDFLoader()

    print(f"\nConfiguration:")
    print(f"  Repository: {loader.catalog}/{loader.repo}")
    print(f"  URL: {loader.repo_url}")

    # Check connection
    initial_count = loader.get_triple_count()
    print(f"  Current triples: {initial_count:,}")

    # Clear if requested
    if not args.no_clear:
        print(f"\nClearing existing data...")
        loader.clear_repository()

    # Determine files to load
    if args.input:
        # Single file
        if not args.input.startswith('/'):
            file_path = f"data/capital_iq_processed/{args.input}"
        else:
            file_path = args.input

        if not os.path.exists(file_path):
            print(f"\n❌ Error: File not found: {file_path}")
            sys.exit(1)

        files_to_load = [file_path]
    else:
        # All files in directory
        pattern = "data/capital_iq_processed/*.json"
        files_to_load = sorted(glob.glob(pattern))

        if not files_to_load:
            print(f"\n❌ Error: No JSON files found in data/capital_iq_processed/")
            sys.exit(1)

    print(f"\nFiles to load: {len(files_to_load)}")
    for f in files_to_load:
        print(f"  - {os.path.basename(f)}")

    # Load files
    total_entities = 0
    total_events = 0
    total_links = 0

    for file_path in files_to_load:
        entity_count, event_count, link_count = load_file_to_allegrograph(
            loader,
            file_path,
            compute_evolution=not args.no_evolution
        )
        total_entities += entity_count
        total_events += event_count
        total_links += link_count

    # Final summary
    final_count = loader.get_triple_count()

    print("\n" + "=" * 70)
    print("  Summary")
    print("=" * 70)
    print(f"\n✅ Data loaded successfully!")
    print(f"\nStatistics:")
    print(f"  - Files processed: {len(files_to_load)}")
    print(f"  - Entities: {total_entities:,}")
    print(f"  - Events: {total_events:,}")
    print(f"  - Evolution links: {total_links:,}")
    print(f"  - Total triples: {final_count:,}")
    print(f"\nNext steps:")
    print(f"  1. View in AllegroGraph: {loader.repo_url}")
    print(f"  2. Run SPARQL queries")
    print(f"  3. Visualize the knowledge graph")
    print("=" * 70 + "\n")


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Cancelled by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
