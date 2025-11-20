"""
Plotting utilities for FE-EKG analysis

Provides timeline plots, heatmaps, and statistical visualizations
"""

import sys
import os
from typing import List, Dict, Optional
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np
from datetime import datetime
import pandas as pd

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from query.risk_analyzer import RiskAnalyzer


def plot_risk_timeline(entity_name: str = 'China Evergrande Group',
                      save_path: Optional[str] = None):
    """
    Plot risk evolution timeline for an entity

    Args:
        entity_name: Name of entity to analyze
        save_path: Optional path to save figure
    """
    analyzer = RiskAnalyzer()

    # Get risk timeline data
    timeline = analyzer.get_entity_risk_timeline(entity_name)

    if not timeline:
        print(f"No risk timeline data for {entity_name}")
        analyzer.close()
        return None

    analyzer.close()

    # Convert to DataFrame
    df = pd.DataFrame(timeline)
    df['date'] = pd.to_datetime(df['date'])

    # Create plot
    fig, ax = plt.subplots(figsize=(14, 8))

    # Plot each risk type
    risk_types = df['riskType'].unique()
    colors = plt.cm.Set3(np.linspace(0, 1, len(risk_types)))

    for risk_type, color in zip(risk_types, colors):
        data = df[df['riskType'] == risk_type]
        ax.plot(data['date'], data['score'],
               marker='o', label=risk_type,
               color=color, linewidth=2, markersize=8)

    ax.set_xlabel('Date', fontsize=12, fontweight='bold')
    ax.set_ylabel('Risk Score', fontsize=12, fontweight='bold')
    ax.set_title(f'Risk Evolution Timeline: {entity_name}',
                fontsize=14, fontweight='bold', pad=20)
    ax.legend(loc='best', fontsize=10)
    ax.grid(True, alpha=0.3)

    # Format x-axis
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
    ax.xaxis.set_major_locator(mdates.MonthLocator())
    plt.xticks(rotation=45)

    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"Saved to {save_path}")

    return fig


def plot_evolution_heatmap(save_path: Optional[str] = None):
    """
    Create heatmap of evolution scores between event types

    Args:
        save_path: Optional path to save figure
    """
    analyzer = RiskAnalyzer()

    # Get evolution links
    query = """
    MATCH (e1:Event)-[r:EVOLVES_TO {type: 'enhanced'}]->(e2:Event)
    RETURN e1.type as source_type,
           e2.type as target_type,
           r.score as score
    """

    data = analyzer.backend.execute_query(query)
    analyzer.close()

    if not data:
        print("No evolution data found")
        return None

    # Convert to DataFrame
    df = pd.DataFrame(data)

    # Create pivot table
    pivot = df.pivot_table(values='score',
                           index='source_type',
                           columns='target_type',
                           aggfunc='mean',
                           fill_value=0)

    # Create heatmap
    fig, ax = plt.subplots(figsize=(12, 10))

    im = ax.imshow(pivot.values, cmap='YlOrRd', aspect='auto', vmin=0, vmax=1)

    # Set ticks and labels
    ax.set_xticks(np.arange(len(pivot.columns)))
    ax.set_yticks(np.arange(len(pivot.index)))
    ax.set_xticklabels([col.replace('_', ' ').title() for col in pivot.columns],
                       rotation=45, ha='right', fontsize=9)
    ax.set_yticklabels([idx.replace('_', ' ').title() for idx in pivot.index],
                       fontsize=9)

    # Add colorbar
    cbar = plt.colorbar(im, ax=ax)
    cbar.set_label('Evolution Score', rotation=270, labelpad=20, fontsize=11)

    # Add text annotations
    for i in range(len(pivot.index)):
        for j in range(len(pivot.columns)):
            value = pivot.values[i, j]
            if value > 0:
                text = ax.text(j, i, f'{value:.2f}',
                             ha='center', va='center',
                             color='white' if value > 0.5 else 'black',
                             fontsize=8, fontweight='bold')

    ax.set_title('Event Evolution Heatmap: Average Scores by Event Type',
                fontsize=14, fontweight='bold', pad=20)
    ax.set_xlabel('To Event Type', fontsize=11, fontweight='bold')
    ax.set_ylabel('From Event Type', fontsize=11, fontweight='bold')

    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"Saved to {save_path}")

    return fig


def plot_event_network(save_path: Optional[str] = None):
    """
    Create temporal event network showing crisis progression

    Args:
        save_path: Optional path to save figure
    """
    analyzer = RiskAnalyzer()

    # Get event timeline
    timeline = analyzer.get_event_timeline()

    if not timeline:
        print("No events found")
        analyzer.close()
        return None

    # Get evolution links
    links = analyzer.get_strongest_evolution_links(min_score=0.3, limit=50)

    analyzer.close()

    # Convert to DataFrames
    events_df = pd.DataFrame(timeline)
    events_df['date'] = pd.to_datetime(events_df['date'])

    # Create figure
    fig, ax = plt.subplots(figsize=(16, 10))

    # Plot events on timeline
    y_positions = {}
    event_types = events_df['eventType'].unique()

    for i, event_type in enumerate(event_types):
        y_positions[event_type] = i

    # Color mapping for event types
    colors = plt.cm.Set1(np.linspace(0, 1, len(event_types)))
    color_map = dict(zip(event_types, colors))

    for idx, event in events_df.iterrows():
        y = y_positions[event['eventType']]
        ax.scatter(event['date'], y,
                  s=300,
                  c=[color_map[event['eventType']]],
                  alpha=0.8,
                  edgecolors='black',
                  linewidth=1.5,
                  zorder=3)

        # Add event label
        ax.text(event['date'], y + 0.2,
               event['eventType'].replace('_', '\n'),
               ha='center', va='bottom',
               fontsize=7, fontweight='bold')

    # Draw evolution connections
    event_date_map = dict(zip(events_df['eventType'], events_df['date']))

    for link in links:
        if link['fromEvent'] in event_date_map and link['toEvent'] in event_date_map:
            x1 = event_date_map[link['fromEvent']]
            y1 = y_positions[link['fromEvent']]
            x2 = event_date_map[link['toEvent']]
            y2 = y_positions[link['toEvent']]

            ax.annotate('',
                       xy=(x2, y2),
                       xytext=(x1, y1),
                       arrowprops=dict(arrowstyle='->',
                                     color='red',
                                     lw=link['overallScore'] * 2,
                                     alpha=0.3))

    ax.set_xlabel('Date', fontsize=12, fontweight='bold')
    ax.set_ylabel('Event Type', fontsize=12, fontweight='bold')
    ax.set_title('Event Evolution Network: Crisis Timeline',
                fontsize=14, fontweight='bold', pad=20)
    ax.set_yticks(list(y_positions.values()))
    ax.set_yticklabels([et.replace('_', ' ').title() for et in y_positions.keys()],
                       fontsize=9)

    # Format x-axis
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
    ax.xaxis.set_major_locator(mdates.MonthLocator())
    plt.xticks(rotation=45)

    ax.grid(True, alpha=0.2, axis='x')

    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"Saved to {save_path}")

    return fig


def plot_component_breakdown(save_path: Optional[str] = None):
    """
    Plot breakdown of evolution score components

    Args:
        save_path: Optional path to save figure
    """
    analyzer = RiskAnalyzer()

    # Get evolution statistics
    stats = analyzer.get_evolution_statistics()
    analyzer.close()

    if not stats or stats.get('totalLinks', 0) == 0:
        print("No evolution statistics found")
        return None

    # Extract component scores
    components = {
        'Temporal': stats['avgTemporal'],
        'Entity\nOverlap': stats['avgEntityOverlap'],
        'Semantic': stats['avgSemantic'],
        'Topic': stats['avgTopic'],
        'Causality': stats['avgCausality'],
        'Emotional': stats['avgEmotional']
    }

    # Create figure with two subplots
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

    # Bar chart
    colors_bar = ['#3498db', '#e74c3c', '#2ecc71', '#f39c12', '#9b59b6', '#1abc9c']
    bars = ax1.bar(components.keys(), components.values(), color=colors_bar, alpha=0.8)
    ax1.set_ylabel('Average Score', fontsize=11, fontweight='bold')
    ax1.set_title('Evolution Score Components: Average Values',
                 fontsize=12, fontweight='bold')
    ax1.set_ylim(0, 1)
    ax1.grid(True, alpha=0.3, axis='y')

    # Add value labels on bars
    for bar in bars:
        height = bar.get_height()
        ax1.text(bar.get_x() + bar.get_width()/2., height,
                f'{height:.3f}',
                ha='center', va='bottom', fontweight='bold')

    # Pie chart
    ax2.pie(components.values(),
           labels=components.keys(),
           colors=colors_bar,
           autopct='%1.1f%%',
           startangle=90)
    ax2.set_title('Relative Contribution of Components',
                 fontsize=12, fontweight='bold')

    fig.suptitle(f'Evolution Analysis: {stats["totalLinks"]} Links',
                fontsize=14, fontweight='bold')

    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"Saved to {save_path}")

    return fig


def plot_risk_distribution(save_path: Optional[str] = None):
    """
    Plot risk distribution by severity and score

    Args:
        save_path: Optional path to save figure
    """
    analyzer = RiskAnalyzer()

    # Get risk distribution
    distribution = analyzer.get_risk_distribution()
    analyzer.close()

    if not distribution:
        print("No risk distribution data found")
        return None

    # Convert to DataFrame
    df = pd.DataFrame(distribution)

    # Create figure
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

    # Stacked bar chart by severity
    pivot = df.pivot_table(values='count',
                           index='severity',
                           columns='scoreBand',
                           fill_value=0)

    pivot.plot(kind='bar', stacked=True, ax=ax1, colormap='YlOrRd')
    ax1.set_xlabel('Severity Level', fontsize=11, fontweight='bold')
    ax1.set_ylabel('Number of Risks', fontsize=11, fontweight='bold')
    ax1.set_title('Risk Distribution by Severity and Score',
                 fontsize=12, fontweight='bold')
    ax1.legend(title='Score Band', bbox_to_anchor=(1.05, 1), loc='upper left')
    ax1.set_xticklabels(ax1.get_xticklabels(), rotation=0)

    # Pie chart of total by severity
    severity_totals = df.groupby('severity')['count'].sum()
    colors = ['#f39c12', '#e74c3c', '#c0392b'][:len(severity_totals)]

    ax2.pie(severity_totals.values,
           labels=[s.title() for s in severity_totals.index],
           colors=colors,
           autopct='%1.1f%%',
           startangle=90)
    ax2.set_title('Risk Distribution by Severity',
                 fontsize=12, fontweight='bold')

    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"Saved to {save_path}")

    return fig


if __name__ == "__main__":
    # Test plotting functions
    print("Creating plots...")

    print("\n1. Risk timeline...")
    plot_risk_timeline(save_path='results/risk_timeline.png')

    print("\n2. Evolution heatmap...")
    plot_evolution_heatmap(save_path='results/evolution_heatmap.png')

    print("\n3. Event network...")
    plot_event_network(save_path='results/event_network_timeline.png')

    print("\n4. Component breakdown...")
    plot_component_breakdown(save_path='results/component_breakdown.png')

    print("\n5. Risk distribution...")
    plot_risk_distribution(save_path='results/risk_distribution.png')

    print("\n✅ All plots created!")
    plt.show()
