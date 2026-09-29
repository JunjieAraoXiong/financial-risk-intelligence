import json

from radar.ablation import run_ablation
from radar.backtest import main
from radar.data.capital_iq import load_capital_iq_events
from radar.data.io import load_ontology
from radar.data.synthetic import make_world
from radar.evaluate import EvalSpec
from radar.graph import OntologyGraph


def test_synthetic_ladder_improves_recall():
    """Plumbing check: in a world built so ontology features help, each rung must help."""
    world = make_world(seed=7)
    graph = OntologyGraph(world.entities, world.relations)
    result = run_ablation(graph, world.events, world.prices, world.portfolio, world.start, world.end,
                          eval_spec=EvalSpec(bootstrap=0))
    t = result.table.set_index("config")
    recall = t.loc[["1_direct_mentions", "2_+entity_resolution", "3_+ownership_hierarchy",
                    "4_+exposure_propagation"], "recall"].tolist()
    assert recall == sorted(recall) and recall[-1] > recall[0]
    assert t.loc["4_+exposure_propagation", "lift"] > 5 * t.loc["5_full_minus_taxonomy", "lift"]
    assert t.loc["4_+exposure_propagation", "lift"] > t.loc["baseline_volatility", "lift"]
    assert t.loc["1_direct_mentions", "unresolved_events"] > 0


def test_cli_synthetic_writes_outputs(tmp_path):
    assert main(["synthetic", "--out", str(tmp_path), "--bootstrap", "50"]) == 0
    for name in ("ablation.md", "ablation.csv", "alerts.csv", "manifest.json"):
        assert (tmp_path / name).exists()
    manifest = json.loads((tmp_path / "manifest.json").read_text())
    assert manifest["data"]["synthetic"] is True and len(manifest["configs"]) == 5


def test_capital_iq_loader_uses_raw_names(tmp_path):
    path = tmp_path / "v4.json"
    path.write_text(json.dumps({"events": [
        {"eventId": "evt_1", "date": "2008-09-15", "type": "bankruptcy", "actor": "Lehman Brothers",
         "headline": "Lehman files", "csvSource": {"companyName": "Lehman Brothers Holdings Inc.",
                                                   "originalEventType": "Bankruptcy - Filing"}},
        {"eventId": "evt_2", "date": None, "type": "unknown", "actor": "X"},
    ]}))
    [e] = load_capital_iq_events(path)
    assert e.mention == "Lehman Brothers Holdings Inc." and e.source_type == "Bankruptcy - Filing"
    assert load_capital_iq_events(path, use_raw_names=False)[0].mention == "Lehman Brothers"


def test_load_ontology(tmp_path):
    path = tmp_path / "o.json"
    path.write_text(json.dumps({
        "entities": [{"id": "a", "name": "A"}, {"id": "b", "name": "B", "aliases": ["Bee"]}],
        "relations": [{"source": "a", "target": "b", "kind": "subsidiary_of", "valid_from": "2008-07-01"}],
    }))
    entities, relations = load_ontology(path)
    assert entities[1].aliases == ("Bee",) and str(relations[0].valid_from) == "2008-07-01"


def test_seed_ontology_loads_and_is_point_in_time():
    from datetime import date
    from pathlib import Path

    from radar.resolver import OntologyResolver

    entities, relations = load_ontology(Path(__file__).parents[2] / "radar/ontology/lehman_2008.json")
    graph = OntologyGraph(entities, relations)
    resolver = OntologyResolver(entities)
    assert resolver.resolve("LEHMAN BROTHERS HOLDINGS INC") == "ent_lehman_brothers"
    assert resolver.resolve("Lehman Brothers Inc.") == "ent_lehman_brothers_inc"

    def owners(eid, d):
        return {i.entity_id for i in graph.affected(eid, d, max_hops=0)}

    assert "ent_jpmorgan" not in owners("ent_bear_stearns", date(2008, 5, 29))
    assert "ent_jpmorgan" in owners("ent_bear_stearns", date(2008, 5, 30))
    assert owners("ent_wamu_bank", date(2008, 10, 1)) == {"ent_wamu_bank", "ent_jpmorgan"}
