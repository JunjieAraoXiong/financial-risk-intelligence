"""
Demo: Risk Analysis Queries

Demonstrates the RiskAnalyzer capabilities with sample queries
"""

import sys
import os
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from feekg_core.query.risk_analyzer import RiskAnalyzer


def print_section(title):
    """Print a formatted section header"""
    print("\n" + "=" * 70)
    print(title)
    print("=" * 70)


def print_subsection(title):
    """Print a formatted subsection header"""
    print(f"\n{title}")
    print("-" * 70)


def demo_entity_risk_analysis(analyzer):
    """Demonstrate entity risk queries"""
    print_section("📊 ENTITY RISK ANALYSIS")

    # Query 1: Risk profile for Evergrande
    print_subsection("1.1 Risk Profile: China Evergrande Group")
    risks = analyzer.get_entity_risk_profile('China Evergrande Group')

    if risks:
        print(f"   Found {len(risks)} risks:")
        for risk in risks:
            print(f"   • {risk['riskType']:<25} Score: {risk['score']:.3f}  "
                  f"Severity: {risk['severity']:<8}  Status: {risk['status']}")
    else:
        print("   ⚠️  No risks found")

    # Query 2: High-risk entities
    print_subsection("1.2 High-Risk Entities (multiple high-severity risks)")
    entities = analyzer.get_high_risk_entities(min_risk_count=2)

    if entities:
        for entity in entities:
            print(f"   • {entity['entity']:<30} ({entity['entityType']})")
            print(f"     Risk Count: {entity['riskCount']}, "
                  f"Avg Score: {entity['avgRiskScore']:.3f}")
    else:
        print("   ℹ️  No entities with multiple high-severity risks")


def demo_evolution_analysis(analyzer):
    """Demonstrate event evolution queries"""
    print_section("🔗 EVENT EVOLUTION ANALYSIS")

    # Query 1: Strongest evolution links
    print_subsection("2.1 Top 10 Strongest Evolution Links")
    links = analyzer.get_strongest_evolution_links(min_score=0.3, limit=10)

    if links:
        for i, link in enumerate(links, 1):
            print(f"   {i:2d}. {link['fromEvent']:<25} → {link['toEvent']:<25}")
            print(f"       {link['fromDate']} → {link['toDate']}")
            print(f"       Overall: {link['overallScore']:.3f}  "
                  f"Causal: {link['causalityScore']:.3f}  "
                  f"Emotional: {link['emotionalScore']:.3f}")
    else:
        print("   ⚠️  No strong evolution links found")

    # Query 2: Causal chains
    print_subsection("2.2 Causal Event Chains (high causality score)")
    chains = analyzer.get_causal_chains(min_causality=0.5, min_length=2)

    if chains:
        for i, chain in enumerate(chains[:5], 1):
            chain_str = " → ".join(chain['eventChain'])
            print(f"   {i}. {chain_str}")
            print(f"      Length: {chain['chainLength']}, "
                  f"Avg Causality: {chain['avgCausality']:.3f}")
    else:
        print("   ℹ️  No multi-hop causal chains found")

    # Query 3: Event impact
    print_subsection("2.3 Most Influential Events (triggered most subsequent events)")
    impacts = analyzer.get_event_impact_analysis()

    if impacts:
        for i, impact in enumerate(impacts[:5], 1):
            print(f"   {i}. {impact['eventType']:<30} ({impact['date']})")
            print(f"      Triggered {impact['directImpact']} events, "
                  f"Avg link strength: {impact['avgEvolutionScore']:.3f}")
    else:
        print("   ⚠️  No impact data found")


def demo_risk_propagation(analyzer):
    """Demonstrate risk propagation queries"""
    print_section("⚠️  RISK PROPAGATION ANALYSIS")

    # Query 1: Systemic risk (contagion)
    print_subsection("3.1 Systemic Risk Detection (Contagion)")
    systemic = analyzer.detect_systemic_risk()

    if systemic:
        for entity in systemic:
            print(f"   • {entity['sourceEntity']}")
            print(f"     Contagion Score: {entity['contagionScore']:.3f} ({entity['severity']})")
            if entity['connectedEntities']:
                print(f"     Connected to: {', '.join(entity['connectedEntities'][:3])}")
    else:
        print("   ✅ No active contagion risks detected")

    # Query 2: Multi-risk entities
    print_subsection("3.2 Entities Facing Multiple Risk Types")
    multi_risk = analyzer.get_multi_risk_entities(min_risk_types=2)

    if multi_risk:
        for entity in multi_risk[:5]:
            print(f"   • {entity['entity']}")
            print(f"     {entity['riskTypeCount']} risk types, "
                  f"Avg score: {entity['avgRiskScore']:.3f}")
            print(f"     Types: {', '.join(entity['riskTypes'][:3])}")
    else:
        print("   ℹ️  No entities with multiple risk types")


def demo_temporal_analysis(analyzer):
    """Demonstrate temporal analysis queries"""
    print_section("📅 TEMPORAL ANALYSIS")

    # Query 1: Crisis escalation points
    print_subsection("4.1 Crisis Escalation Points (multiple events on same date)")
    crisis_points = analyzer.get_crisis_escalation_points(min_events=2)

    if crisis_points:
        for point in crisis_points[:5]:
            print(f"   • {point['date']}: {point['eventCount']} events")
            print(f"     {', '.join(point['events'][:3])}")
    else:
        print("   ℹ️  No crisis escalation points found")

    # Query 2: Event timeline (first 10 events)
    print_subsection("4.2 Event Timeline (first 10 events)")
    timeline = analyzer.get_event_timeline()

    if timeline:
        for event in timeline[:10]:
            print(f"   • {event['date']}: {event['eventType']}")
            if event['actor'] and event['target']:
                print(f"     {event['actor']} → {event['target']}")
    else:
        print("   ⚠️  No events found")


def demo_pattern_detection(analyzer):
    """Demonstrate pattern detection queries"""
    print_section("🔍 PATTERN DETECTION")

    # Query 1: Debt default cascades
    print_subsection("5.1 Debt Default Cascade Patterns")
    cascades = analyzer.detect_debt_default_cascades()

    if cascades:
        for i, cascade in enumerate(cascades[:3], 1):
            pattern_str = " → ".join([step['type'] for step in cascade['cascadePattern']])
            print(f"   {i}. {pattern_str}")
            print(f"      Steps: {cascade['steps']}")
    else:
        print("   ℹ️  No debt default cascades detected")

    # Query 2: Regulatory intervention impact
    print_subsection("5.2 Regulatory Intervention Impact")
    interventions = analyzer.analyze_regulatory_intervention_impact()

    if interventions:
        for intervention in interventions:
            print(f"   • {intervention['interventionDate']}")
            if intervention['eventCount'] > 0:
                print(f"     Followed by {intervention['eventCount']} events:")
                print(f"     {', '.join(intervention['subsequentEvents'][:3])}")
            else:
                print(f"     No subsequent events tracked")
    else:
        print("   ℹ️  No regulatory interventions found")


def demo_statistics(analyzer):
    """Demonstrate statistical queries"""
    print_section("📈 STATISTICAL OVERVIEW")

    # Query 1: Evolution statistics
    print_subsection("6.1 Evolution Link Statistics")
    stats = analyzer.get_evolution_statistics()

    if stats:
        print(f"   Total Evolution Links: {stats.get('totalLinks', 0)}")
        print(f"\n   Component Scores (averages):")
        print(f"   • Overall Score:    {stats.get('avgOverallScore', 0):.3f}")
        print(f"   • Temporal:         {stats.get('avgTemporal', 0):.3f}")
        print(f"   • Entity Overlap:   {stats.get('avgEntityOverlap', 0):.3f}")
        print(f"   • Semantic:         {stats.get('avgSemantic', 0):.3f}")
        print(f"   • Topic:            {stats.get('avgTopic', 0):.3f}")
        print(f"   • Causality:        {stats.get('avgCausality', 0):.3f}")
        print(f"   • Emotional:        {stats.get('avgEmotional', 0):.3f}")
    else:
        print("   ⚠️  No statistics available")

    # Query 2: Event type frequency
    print_subsection("6.2 Event Type Frequency")
    frequencies = analyzer.get_event_type_frequency()

    if frequencies:
        for i, freq in enumerate(frequencies[:10], 1):
            print(f"   {i:2d}. {freq['eventType']:<30} {freq['frequency']:>3} events")
    else:
        print("   ⚠️  No event data found")

    # Query 3: Risk distribution
    print_subsection("6.3 Risk Score Distribution")
    distribution = analyzer.get_risk_distribution()

    if distribution:
        for dist in distribution:
            print(f"   {dist['severity']:<10} {dist['scoreBand']:<20} {dist['count']:>3} risks")
    else:
        print("   ⚠️  No risk data found")


def demo_database_overview(analyzer):
    """Show database overview"""
    print_section("🗄️  DATABASE OVERVIEW")

    overview = analyzer.get_database_overview()

    print_subsection("Nodes")
    for node in overview['nodes']:
        print(f"   {str(node['nodeType']):<30} {node['count']:>4}")

    print_subsection("Relationships")
    for rel in overview['relationships']:
        print(f"   {rel['relationType']:<30} {rel['count']:>4}")

    print_subsection("Risk Type Distribution")
    if overview['risks']:
        for risk in overview['risks']:
            print(f"   {risk['riskType']:<30} {risk['count']:>4}")
    else:
        print("   ℹ️  No risk distribution data")


def main():
    """Run all demo queries"""
    print("\n" + "=" * 70)
    print("FE-EKG RISK ANALYSIS QUERY DEMO")
    print("=" * 70)
    print("\nConnecting to Neo4j...")

    try:
        analyzer = RiskAnalyzer()
        print("✅ Connected successfully!")

        # Run all demo sections
        demo_database_overview(analyzer)
        demo_entity_risk_analysis(analyzer)
        demo_evolution_analysis(analyzer)
        demo_risk_propagation(analyzer)
        demo_temporal_analysis(analyzer)
        demo_pattern_detection(analyzer)
        demo_statistics(analyzer)

        analyzer.close()

        print("\n" + "=" * 70)
        print("✅ DEMO COMPLETE")
        print("=" * 70)
        print("\n💡 Tips:")
        print("   • Use query/risk_analyzer.py functions in your own scripts")
        print("   • See query/risk_queries.cypher for raw Cypher queries")
        print("   • Run queries in Neo4j Browser: http://localhost:7474")
        print()

        return True

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
