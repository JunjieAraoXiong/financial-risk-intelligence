"""
Risk taxonomy: maps event types to a risk category and a severity in [0, 1].

This is the "risk layer" of the ontology in its simplest form. Severities are
set *before* looking at backtest results and must not be tuned on the
evaluation period; change them only with a documented reason.
"""

from __future__ import annotations

from typing import Dict, Tuple

CREDIT = "credit"
LIQUIDITY = "liquidity"
MARKET = "market"
GOVERNANCE = "governance"
LEGAL = "legal_regulatory"
STRATEGIC = "strategic"
NONE = "none"

RISK_CATEGORIES = (CREDIT, LIQUIDITY, MARKET, GOVERNANCE, LEGAL, STRATEGIC, NONE)

# FE-EKG event type -> (risk category, severity)
EVENT_RISK: Dict[str, Tuple[str, float]] = {
    "bankruptcy": (CREDIT, 1.0),
    "credit_downgrade": (CREDIT, 0.8),
    "government_intervention": (LIQUIDITY, 0.8),
    "earnings_loss": (CREDIT, 0.6),
    "restructuring": (STRATEGIC, 0.5),
    "legal_issue": (LEGAL, 0.5),
    "capital_raising": (LIQUIDITY, 0.4),
    "management_change": (GOVERNANCE, 0.3),
    "stock_movement": (MARKET, 0.3),
    "merger_acquisition": (STRATEGIC, 0.2),
    "unknown": (NONE, 0.1),
    "earnings_announcement": (NONE, 0.05),
    "business_operations": (NONE, 0.05),
    "strategic_partnership": (NONE, 0.05),
}

# SEC Form 8-K item -> FE-EKG event type (for the EDGAR event feed).
EDGAR_8K_ITEMS: Dict[str, str] = {
    "1.01": "business_operations",      # Entry into a material definitive agreement
    "1.02": "business_operations",      # Termination of a material definitive agreement
    "1.03": "bankruptcy",               # Bankruptcy or receivership
    "2.01": "merger_acquisition",       # Completion of acquisition or disposition of assets
    "2.02": "earnings_announcement",    # Results of operations and financial condition
    "2.03": "capital_raising",          # Creation of a direct financial obligation
    "2.04": "credit_downgrade",         # Triggering events that accelerate a financial obligation
    "2.05": "restructuring",            # Costs associated with exit or disposal activities
    "2.06": "earnings_loss",            # Material impairments
    "3.01": "stock_movement",           # Notice of delisting / failure to meet listing standards
    "4.01": "management_change",        # Changes in registrant's certifying accountant
    "4.02": "legal_issue",              # Non-reliance on previously issued financial statements
    "5.02": "management_change",        # Departure/appointment of directors or officers
}


def classify(event_type: str) -> Tuple[str, float]:
    """Risk category and severity for an event type (unknown types are low-severity)."""
    return EVENT_RISK.get(event_type, EVENT_RISK["unknown"])
