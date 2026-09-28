"""Guard against broken intra-repo imports (e.g. a base class deleted in a cleanup)."""

import importlib

import pytest

MODULES = [
    "api.app",
    "api.wsgi",
    "shared.config",
    "shared.config.graph_backend",
    "shared.config.entity_aliases",
    "feekg_core.query.optimized_graph_queries",
    "feekg_core.query.risk_analyzer",
    "feekg_core.evolution.methods",
    "feekg_core.evolution.run_evolution",
    "feekg_core.ingestion.process_capital_iq_v4",
    "feekg_core.ingestion.load_capital_iq_to_allegrograph",
    "feekg_core.ingestion.load_v4_deduped_to_allegrograph",
    "feekg_core.viz.plot_utils",
    "feekg_core.viz.graph_viz",
]


@pytest.mark.parametrize("module", MODULES)
def test_module_imports(module):
    importlib.import_module(module)
