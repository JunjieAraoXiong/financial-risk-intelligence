"""
Risk Analysis Module

Provides Python functions for querying and analyzing the FE-EKG graph
"""

import sys
import os
from typing import List, Dict, Optional, Tuple
from datetime import datetime

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from shared.config.graph_backend import get_connection


class RiskAnalyzer:
    """High-level interface for risk analysis queries"""

    def __init__(self):
        """Initialize with database connection"""
        self.backend = get_connection()

    def close(self):
        """Close database connection"""
        self.backend.close()

    # =========================================================================
    # ENTITY RISK QUERIES
    # =========================================================================

    def get_entity_risk_profile(self, entity_name: str) -> List[Dict]:
        """
        Get all risks targeting a specific entity

        Args:
            entity_name: Name of the entity (e.g., 'China Evergrande Group')

        Returns:
            List of risk dicts with type, score, severity, status
        """
        query = """
        MATCH (e:Entity {name: $entityName})
        MATCH (r:Risk)-[:TARGETS_ENTITY]->(e)
        MATCH (r)-[:HAS_RISK_TYPE]->(rt:RiskType)
        RETURN rt.label as riskType,
               r.score as score,
               r.severity as severity,
               r.status as status
        ORDER BY r.score DESC
        """

        results = self.backend.execute_query(query, {'entityName': entity_name})
        return results

    def get_high_risk_entities(self, min_risk_count: int = 2) -> List[Dict]:
        """
        Find entities with multiple high-severity risks

        Args:
            min_risk_count: Minimum number of risks to qualify

        Returns:
            List of entity dicts with risk counts and average scores
        """
        query = """
        MATCH (e:Entity)<-[:TARGETS_ENTITY]-(r:Risk)
        WHERE r.severity IN ['high', 'critical']
        WITH e, count(r) as riskCount, avg(r.score) as avgScore
        WHERE riskCount >= $minCount
        RETURN e.name as entity,
               e.type as entityType,
               riskCount,
               round(avgScore * 100) / 100 as avgRiskScore
        ORDER BY avgScore DESC, riskCount DESC
        """

        results = self.backend.execute_query(query, {'minCount': min_risk_count})
        return results

    def get_entity_risk_timeline(self, entity_name: str) -> List[Dict]:
        """
        Track how risks evolved for an entity over time

        Args:
            entity_name: Name of the entity

        Returns:
            List of risk snapshot dicts with dates and scores
        """
        query = """
        MATCH (e:Entity {name: $entityName})<-[:TARGETS_ENTITY]-(r:Risk)
        MATCH (r)-[:HAS_SNAPSHOT]->(rs:RiskSnapshot)
        MATCH (r)-[:HAS_RISK_TYPE]->(rt:RiskType)
        RETURN rt.label as riskType,
               toString(rs.date) as date,
               rs.score as score
        ORDER BY rs.date, rt.label
        """

        results = self.backend.execute_query(query, {'entityName': entity_name})
        return results

    # =========================================================================
    # EVENT EVOLUTION QUERIES
    # =========================================================================

    def get_evolution_chains(self, start_event_id: str, max_length: int = 3) -> List[Dict]:
        """
        Find sequences of events that evolved from a starting event

        Args:
            start_event_id: ID of the starting event
            max_length: Maximum chain length

        Returns:
            List of chain dicts with event sequences
        """
        query = f"""
        MATCH path = (e1:Event {{eventId: $startId}})-[:EVOLVES_TO*1..{max_length}]->(e2:Event)
        RETURN [e in nodes(path) | e.type] as eventChain,
               [e in nodes(path) | toString(e.date)] as dateChain,
               length(path) as chainLength
        ORDER BY chainLength DESC
        LIMIT 10
        """

        results = self.backend.execute_query(query, {'startId': start_event_id})
        return results

    def get_strongest_evolution_links(self, min_score: float = 0.5, limit: int = 20) -> List[Dict]:
        """
        Find the most significant event evolution relationships

        Args:
            min_score: Minimum evolution score threshold
            limit: Maximum number of results

        Returns:
            List of evolution link dicts with scores and component breakdowns
        """
        query = """
        MATCH (e1:Event)-[r:EVOLVES_TO {type: 'enhanced'}]->(e2:Event)
        WHERE r.score > $minScore
        RETURN e1.type as fromEvent,
               toString(e1.date) as fromDate,
               e2.type as toEvent,
               toString(e2.date) as toDate,
               round(r.score * 1000) / 1000 as overallScore,
               round(r.causality * 1000) / 1000 as causalityScore,
               round(r.emotional * 1000) / 1000 as emotionalScore,
               round(r.temporal * 1000) / 1000 as temporalScore
        ORDER BY r.score DESC
        LIMIT $limit
        """

        results = self.backend.execute_query(query, {'minScore': min_score, 'limit': limit})
        return results

    def get_causal_chains(self, min_causality: float = 0.6,
                         min_length: int = 2, max_length: int = 5) -> List[Dict]:
        """
        Find event chains with strong causal relationships

        Args:
            min_causality: Minimum causality score for each link
            min_length: Minimum chain length
            max_length: Maximum chain length

        Returns:
            List of causal chain dicts
        """
        query = f"""
        MATCH path = (e1:Event)-[:EVOLVES_TO*{min_length}..{max_length}]->(e2:Event)
        WHERE all(r in relationships(path) WHERE r.causality > $minCausality)
        WITH path,
             [e in nodes(path) | e.type] as chain,
             [r in relationships(path) | r.causality] as causal_scores
        RETURN chain as eventChain,
               length(path) as chainLength,
               round(reduce(sum = 0.0, score in causal_scores | sum + score) /
                     size(causal_scores) * 1000) / 1000 as avgCausality
        ORDER BY chainLength DESC, avgCausality DESC
        LIMIT 10
        """

        results = self.backend.execute_query(query, {'minCausality': min_causality})
        return results

    def get_event_impact_analysis(self) -> List[Dict]:
        """
        Find events that triggered the most subsequent events

        Returns:
            List of event dicts with impact metrics
        """
        query = """
        MATCH (e:Event)-[r:EVOLVES_TO]->(next:Event)
        WITH e, count(next) as directImpact, avg(r.score) as avgLinkStrength
        WHERE directImpact > 0
        RETURN e.eventId as eventId,
               e.type as eventType,
               toString(e.date) as date,
               directImpact,
               round(avgLinkStrength * 1000) / 1000 as avgEvolutionScore
        ORDER BY directImpact DESC, avgLinkStrength DESC
        """

        results = self.backend.execute_query(query)
        return results

    # =========================================================================
    # RISK PROPAGATION QUERIES
    # =========================================================================

    def detect_systemic_risk(self) -> List[Dict]:
        """
        Identify entities at risk of contagion

        Returns:
            List of entity dicts with contagion risk details
        """
        query = """
        MATCH (e:Entity)<-[:TARGETS_ENTITY]-(r:Risk)
        MATCH (r)-[:HAS_RISK_TYPE]->(rt:RiskType {name: 'ContagionRisk'})
        OPTIONAL MATCH (e)-[:RELATED_TO]-(connected:Entity)
        RETURN e.name as sourceEntity,
               collect(DISTINCT connected.name) as connectedEntities,
               r.score as contagionScore,
               r.severity as severity
        ORDER BY r.score DESC
        """

        results = self.backend.execute_query(query)
        return results

    def get_multi_risk_entities(self, min_risk_types: int = 3) -> List[Dict]:
        """
        Find entities facing multiple types of risks simultaneously

        Args:
            min_risk_types: Minimum number of different risk types

        Returns:
            List of entity dicts with risk type details
        """
        query = """
        MATCH (e:Entity)<-[:TARGETS_ENTITY]-(r:Risk)
        MATCH (r)-[:HAS_RISK_TYPE]->(rt:RiskType)
        WITH e, collect(DISTINCT rt.label) as riskTypes, avg(r.score) as avgScore
        WHERE size(riskTypes) >= $minTypes
        RETURN e.name as entity,
               riskTypes,
               size(riskTypes) as riskTypeCount,
               round(avgScore * 100) / 100 as avgRiskScore
        ORDER BY riskTypeCount DESC, avgScore DESC
        """

        results = self.backend.execute_query(query, {'minTypes': min_risk_types})
        return results

    # =========================================================================
    # TEMPORAL ANALYSIS QUERIES
    # =========================================================================

    def get_event_timeline(self, start_date: Optional[str] = None,
                          end_date: Optional[str] = None) -> List[Dict]:
        """
        Get chronological view of events, optionally filtered by date range

        Args:
            start_date: Start date in YYYY-MM-DD format (optional)
            end_date: End date in YYYY-MM-DD format (optional)

        Returns:
            List of event dicts in chronological order
        """
        if start_date and end_date:
            query = """
            MATCH (e:Event)
            WHERE date(e.date) >= date($startDate) AND date(e.date) <= date($endDate)
            OPTIONAL MATCH (e)-[:HAS_ACTOR]->(actor:Entity)
            OPTIONAL MATCH (e)-[:HAS_TARGET]->(target:Entity)
            RETURN toString(e.date) as date,
                   e.type as eventType,
                   actor.name as actor,
                   target.name as target,
                   e.description as description
            ORDER BY e.date
            """
            params = {'startDate': start_date, 'endDate': end_date}
        else:
            query = """
            MATCH (e:Event)
            OPTIONAL MATCH (e)-[:HAS_ACTOR]->(actor:Entity)
            OPTIONAL MATCH (e)-[:HAS_TARGET]->(target:Entity)
            RETURN toString(e.date) as date,
                   e.type as eventType,
                   actor.name as actor,
                   target.name as target,
                   e.description as description
            ORDER BY e.date
            """
            params = {}

        results = self.backend.execute_query(query, params)
        return results

    def get_crisis_escalation_points(self, min_events: int = 2) -> List[Dict]:
        """
        Identify dates with multiple significant events (crisis points)

        Args:
            min_events: Minimum number of events on a date to qualify

        Returns:
            List of date dicts with event clusters
        """
        query = """
        MATCH (e:Event)
        WITH toString(e.date) as date, collect(e.type) as events, count(e) as eventCount
        WHERE eventCount >= $minEvents
        RETURN date, events, eventCount
        ORDER BY date
        """

        results = self.backend.execute_query(query, {'minEvents': min_events})
        return results

    # =========================================================================
    # PATTERN DETECTION QUERIES
    # =========================================================================

    def detect_debt_default_cascades(self) -> List[Dict]:
        """
        Detect debt default → credit downgrade → stock crash patterns

        Returns:
            List of cascade pattern dicts
        """
        query = """
        MATCH path = (e1:Event {type: 'debt_default'})-[:EVOLVES_TO*1..3]->(e2:Event)
        WHERE any(e in nodes(path) WHERE e.type IN ['credit_downgrade', 'stock_crash'])
        RETURN [e in nodes(path) | {type: e.type, date: toString(e.date)}] as cascadePattern,
               length(path) as steps
        ORDER BY length(path) DESC
        """

        results = self.backend.execute_query(query)
        return results

    def analyze_regulatory_intervention_impact(self) -> List[Dict]:
        """
        Analyze events following regulatory interventions

        Returns:
            List of intervention impact dicts
        """
        query = """
        MATCH (reg:Event {type: 'regulatory_intervention'})
        OPTIONAL MATCH path = (reg)-[:EVOLVES_TO*1..2]->(subsequent:Event)
        WITH reg, collect(DISTINCT subsequent.type) as subsequentEvents,
             count(DISTINCT subsequent) as eventCount
        RETURN toString(reg.date) as interventionDate,
               subsequentEvents,
               eventCount
        ORDER BY reg.date
        """

        results = self.backend.execute_query(query)
        return results

    # =========================================================================
    # STATISTICS QUERIES
    # =========================================================================

    def get_evolution_statistics(self) -> Dict:
        """
        Get overall statistics on evolution link quality

        Returns:
            Dict with aggregated evolution scores
        """
        query = """
        MATCH ()-[r:EVOLVES_TO {type: 'enhanced'}]->()
        RETURN count(r) as totalLinks,
               round(avg(r.score) * 1000) / 1000 as avgOverallScore,
               round(avg(r.temporal) * 1000) / 1000 as avgTemporal,
               round(avg(r.entity_overlap) * 1000) / 1000 as avgEntityOverlap,
               round(avg(r.semantic) * 1000) / 1000 as avgSemantic,
               round(avg(r.topic) * 1000) / 1000 as avgTopic,
               round(avg(r.causality) * 1000) / 1000 as avgCausality,
               round(avg(r.emotional) * 1000) / 1000 as avgEmotional
        """

        results = self.backend.execute_query(query)
        return results[0] if results else {}

    def get_risk_distribution(self) -> List[Dict]:
        """
        Get distribution of risks by severity and score bands

        Returns:
            List of distribution dicts
        """
        query = """
        MATCH (r:Risk)
        WITH r.severity as severity,
             CASE
               WHEN r.score < 0.3 THEN 'Low (0-0.3)'
               WHEN r.score < 0.6 THEN 'Medium (0.3-0.6)'
               WHEN r.score < 0.8 THEN 'High (0.6-0.8)'
               ELSE 'Critical (0.8-1.0)'
             END as scoreBand,
             count(*) as count
        RETURN severity, scoreBand, count
        ORDER BY severity, scoreBand
        """

        results = self.backend.execute_query(query)
        return results

    def get_event_type_frequency(self) -> List[Dict]:
        """
        Get frequency of each event type

        Returns:
            List of event type frequency dicts
        """
        query = """
        MATCH (e:Event)
        RETURN e.type as eventType,
               count(*) as frequency
        ORDER BY frequency DESC
        """

        results = self.backend.execute_query(query)
        return results

    # =========================================================================
    # DATABASE OVERVIEW
    # =========================================================================

    def get_database_overview(self) -> Dict:
        """
        Get comprehensive overview of database contents

        Returns:
            Dict with node counts, relationship counts, and summary stats
        """
        # Node counts
        node_query = """
        MATCH (n)
        RETURN labels(n) as nodeType, count(n) as count
        ORDER BY count DESC
        """
        nodes = self.backend.execute_query(node_query)

        # Relationship counts
        rel_query = """
        MATCH ()-[r]->()
        RETURN type(r) as relationType, count(r) as count
        ORDER BY count DESC
        """
        rels = self.backend.execute_query(rel_query)

        # Risk type distribution
        risk_query = """
        MATCH (r:Risk)-[:HAS_RISK_TYPE]->(rt:RiskType)
        RETURN rt.label as riskType, count(r) as count
        ORDER BY count DESC
        """
        risks = self.backend.execute_query(risk_query)

        return {
            'nodes': nodes,
            'relationships': rels,
            'risks': risks
        }


if __name__ == "__main__":
    # Test the analyzer
    analyzer = RiskAnalyzer()

    print("=" * 70)
    print("FE-EKG Risk Analyzer - Test Suite")
    print("=" * 70)

    # Test 1: Database overview
    print("\n1. Database Overview")
    print("-" * 70)
    overview = analyzer.get_database_overview()
    print("Nodes:")
    for node in overview['nodes']:
        print(f"  {node['nodeType']}: {node['count']}")

    # Test 2: Entity risk profile
    print("\n2. Entity Risk Profile: China Evergrande Group")
    print("-" * 70)
    risks = analyzer.get_entity_risk_profile('China Evergrande Group')
    for risk in risks:
        print(f"  {risk['riskType']}: {risk['score']:.3f} ({risk['severity']}, {risk['status']})")

    # Test 3: Evolution statistics
    print("\n3. Evolution Link Statistics")
    print("-" * 70)
    stats = analyzer.get_evolution_statistics()
    print(f"  Total Links: {stats.get('totalLinks', 0)}")
    print(f"  Avg Overall Score: {stats.get('avgOverallScore', 0):.3f}")
    print(f"  Avg Causality: {stats.get('avgCausality', 0):.3f}")
    print(f"  Avg Emotional: {stats.get('avgEmotional', 0):.3f}")

    # Test 4: Strongest evolution links
    print("\n4. Top 5 Strongest Evolution Links")
    print("-" * 70)
    links = analyzer.get_strongest_evolution_links(min_score=0.0, limit=5)
    for i, link in enumerate(links, 1):
        print(f"  {i}. {link['fromEvent']} → {link['toEvent']}")
        print(f"     ({link['fromDate']} → {link['toDate']}, score: {link['overallScore']:.3f})")

    # Test 5: Causal chains
    print("\n5. Causal Event Chains")
    print("-" * 70)
    chains = analyzer.get_causal_chains(min_causality=0.5)
    for i, chain in enumerate(chains[:3], 1):
        chain_str = " → ".join(chain['eventChain'])
        print(f"  {i}. {chain_str}")
        print(f"     (Length: {chain['chainLength']}, Avg Causality: {chain['avgCausality']:.3f})")

    analyzer.close()

    print("\n" + "=" * 70)
    print("✅ Test Suite Complete")
    print("=" * 70)
