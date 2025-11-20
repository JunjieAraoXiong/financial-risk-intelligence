"""
Demo: FE-EKG Visualizations

Generate all visualizations and save to results/
"""

import sys
import os
import matplotlib.pyplot as plt

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from feekg_core.viz.graph_viz import ThreeLayerVisualizer
from feekg_core.viz.plot_utils import (plot_risk_timeline, plot_evolution_heatmap,
                            plot_event_network, plot_component_breakdown,
                            plot_risk_distribution)


def main():
    """Run all visualization demos"""
    print("\n" + "=" * 70)
    print("FE-EKG VISUALIZATION DEMO")
    print("=" * 70)

    # Ensure results directory exists
    os.makedirs('results', exist_ok=True)

    # Initialize visualizer
    viz = ThreeLayerVisualizer()

    # ==========================================================================
    # 1. THREE-LAYER GRAPH
    # ==========================================================================
    print("\n1️⃣  Creating Three-Layer Knowledge Graph...")
    print("   This shows the complete Entity → Event → Risk architecture")
    try:
        fig1 = viz.create_three_layer_graph(
            limit_events=15,
            save_path='results/three_layer_graph.png'
        )
        print("   ✅ Saved to results/three_layer_graph.png")
    except Exception as e:
        print(f"   ❌ Failed: {e}")

    # ==========================================================================
    # 2. EVOLUTION NETWORK
    # ==========================================================================
    print("\n2️⃣  Creating Event Evolution Network...")
    print("   This shows how events evolve into each other")
    try:
        fig2 = viz.create_evolution_network(
            min_score=0.5,
            save_path='results/evolution_network.png'
        )
        print("   ✅ Saved to results/evolution_network.png")
    except Exception as e:
        print(f"   ❌ Failed: {e}")

    # ==========================================================================
    # 3. RISK PROPAGATION
    # ==========================================================================
    print("\n3️⃣  Creating Risk Propagation View...")
    print("   This shows how risks target entities")
    try:
        fig3 = viz.create_risk_propagation_view(
            save_path='results/risk_propagation.png'
        )
        print("   ✅ Saved to results/risk_propagation.png")
    except Exception as e:
        print(f"   ❌ Failed: {e}")

    viz.close()

    # ==========================================================================
    # 4. RISK TIMELINE
    # ==========================================================================
    print("\n4️⃣  Creating Risk Timeline Plot...")
    print("   This shows how risks evolved over time")
    try:
        fig4 = plot_risk_timeline(
            entity_name='China Evergrande Group',
            save_path='results/risk_timeline.png'
        )
        print("   ✅ Saved to results/risk_timeline.png")
    except Exception as e:
        print(f"   ❌ Failed: {e}")

    # ==========================================================================
    # 5. EVOLUTION HEATMAP
    # ==========================================================================
    print("\n5️⃣  Creating Evolution Heatmap...")
    print("   This shows evolution scores between event types")
    try:
        fig5 = plot_evolution_heatmap(
            save_path='results/evolution_heatmap.png'
        )
        print("   ✅ Saved to results/evolution_heatmap.png")
    except Exception as e:
        print(f"   ❌ Failed: {e}")

    # ==========================================================================
    # 6. EVENT NETWORK TIMELINE
    # ==========================================================================
    print("\n6️⃣  Creating Event Network Timeline...")
    print("   This shows events on a temporal axis with evolution links")
    try:
        fig6 = plot_event_network(
            save_path='results/event_network_timeline.png'
        )
        print("   ✅ Saved to results/event_network_timeline.png")
    except Exception as e:
        print(f"   ❌ Failed: {e}")

    # ==========================================================================
    # 7. COMPONENT BREAKDOWN
    # ==========================================================================
    print("\n7️⃣  Creating Component Breakdown...")
    print("   This shows contribution of each evolution method")
    try:
        fig7 = plot_component_breakdown(
            save_path='results/component_breakdown.png'
        )
        print("   ✅ Saved to results/component_breakdown.png")
    except Exception as e:
        print(f"   ❌ Failed: {e}")

    # ==========================================================================
    # 8. RISK DISTRIBUTION
    # ==========================================================================
    print("\n8️⃣  Creating Risk Distribution...")
    print("   This shows risk distribution by severity and score")
    try:
        fig8 = plot_risk_distribution(
            save_path='results/risk_distribution.png'
        )
        print("   ✅ Saved to results/risk_distribution.png")
    except Exception as e:
        print(f"   ❌ Failed: {e}")

    # ==========================================================================
    # SUMMARY
    # ==========================================================================
    print("\n" + "=" * 70)
    print("✅ VISUALIZATION DEMO COMPLETE")
    print("=" * 70)

    print("\n📊 Generated Visualizations:")
    print("   1. results/three_layer_graph.png          - Full 3-layer architecture")
    print("   2. results/evolution_network.png          - Event evolution network")
    print("   3. results/risk_propagation.png           - Risk → Entity connections")
    print("   4. results/risk_timeline.png              - Risk evolution over time")
    print("   5. results/evolution_heatmap.png          - Event type evolution matrix")
    print("   6. results/event_network_timeline.png     - Temporal event network")
    print("   7. results/component_breakdown.png        - Evolution method contributions")
    print("   8. results/risk_distribution.png          - Risk severity distribution")

    print("\n💡 Tips:")
    print("   • Open images with your favorite image viewer")
    print("   • Use these in papers, presentations, or reports")
    print("   • Customize parameters in viz/graph_viz.py and viz/plot_utils.py")

    print("\n🚀 Next Step:")
    print("   • Start the REST API: python api/app.py")
    print("   • Access API at: http://localhost:5000")
    print()

    # Optionally display one
    print("Displaying three-layer graph...")
    plt.show()


if __name__ == "__main__":
    main()
