import pytest

from api.app import create_app
from feekg_core.query.optimized_graph_queries import GraphQueryError
from feekg_core.query.sparql import InvalidQueryParameter


class FakeBackend:
    def __init__(self, fail=False):
        self.fail = fail
        self.calls = []

    def _check(self, name, **kw):
        self.calls.append((name, kw))
        if self.fail:
            raise GraphQueryError("down")

    def ping(self):
        self._check("ping")
        return True

    def get_graph_stats_cached(self):
        self._check("stats_cached")
        return {"total_events": 2, "total_entities": 1, "total_links": 1,
                "date_range": {"start": "2008-01-01", "end": "2008-12-31"},
                "event_type_distribution": {"t": 2}, "timestamp": 0}

    def get_graph_stats(self):
        self._check("stats")
        return {"totalEvents": 2}

    def get_all_entities(self):
        self._check("entities")
        return [{"id": "ent_a", "name": "A", "type": "bank"}]

    def get_entity_by_id(self, entity_id):
        self._check("entity", entity_id=entity_id)
        return {"id": "ent_a", "name": "A", "type": "bank"} if entity_id == "ent_a" else None

    def get_events_paginated(self, offset, limit):
        self._check("paginated", offset=offset, limit=limit)
        return {"events": [], "total": 0, "offset": offset, "limit": limit, "has_more": False}

    def get_events_by_timewindow(self, start, end, entity_filter=None, limit=500):
        self._check("window", start=start, end=end, entity=entity_filter, limit=limit)
        return []

    def get_event_by_id(self, event_id):
        self._check("event", event_id=event_id)
        return None

    def get_high_impact_events(self, min_degree, limit):
        self._check("hubs")
        return []

    def get_event_neighborhood(self, event_id, max_hops, min_score):
        if event_id.startswith("bad"):
            raise InvalidQueryParameter("Invalid event_id")
        return {"center": event_id, "neighbors": [], "links": []}

    def get_evolution_links(self, limit, min_score, event_id=None):
        self._check("links", limit=limit, min_score=min_score, event_id=event_id)
        return [{"from": "evt_1", "to": "evt_2", "score": 0.8, "causality": 0.4}]

    def get_evolution_statistics(self):
        self._check("evo_stats")
        return {"total_links": 1}

    def get_graph_data_for_viz(self, limit_events, min_evolution_score, start_date=None, end_date=None):
        self._check("viz", limit=limit_events, start=start_date, end=end_date)
        return {
            "nodes": {"entities": [{"id": "ent_a", "name": "A", "type": "bank"}],
                      "events": [{"eventId": "evt_1", "label": "Lehman files", "type": "bankruptcy",
                                  "date": "2008-09-15"}]},
            "edges": {"evolution": [{"from": "evt_1", "to": "evt_2", "score": 0.8, "causality": 0.4}],
                      "event_entity": [{"event": "evt_1", "entity": "ent_a", "type": "involves"}]},
            "stats": {"total_entities": 1, "total_events": 1, "evolution_links": 1, "event_entity_links": 1},
        }


@pytest.fixture
def backend():
    return FakeBackend()


@pytest.fixture
def client(settings, backend):
    return create_app(settings=settings, backend=backend).test_client()


def test_health_does_not_touch_db(client, backend):
    r = client.get("/health")
    assert r.status_code == 200 and r.json["status"] == "healthy"
    assert backend.calls == []
    assert r.headers["X-Content-Type-Options"] == "nosniff"
    assert r.headers["X-Request-ID"]


def test_ready(settings):
    assert create_app(settings=settings, backend=FakeBackend()).test_client().get("/ready").status_code == 200
    assert create_app(settings=settings, backend=FakeBackend(fail=True)).test_client().get("/ready").status_code == 503


def test_db_failure_is_503_without_leaking(settings):
    r = create_app(settings=settings, backend=FakeBackend(fail=True)).test_client().get("/api/entities")
    assert r.status_code == 503
    assert r.json["message"] == "Graph database unavailable"


def test_info(client):
    r = client.get("/api/info")
    assert r.status_code == 200
    assert r.json["data"]["total_events"] == 2 and "timestamp" not in r.json["data"]


def test_entity_found_and_missing(client):
    assert client.get("/api/entities/ent_a").json["data"]["name"] == "A"
    assert client.get("/api/entities/ent_zzz").status_code == 404


def test_events_pagination_and_bounds(client, backend):
    r = client.get("/api/events?offset=10&limit=5")
    assert r.status_code == 200 and r.json["offset"] == 10
    assert client.get("/api/events?limit=abc").status_code == 400
    assert client.get("/api/events?limit=0").status_code == 400
    assert client.get("/api/events?limit=100000").status_code == 400
    assert client.get("/api/events?offset=-1").status_code == 400


def test_events_time_window(client, backend):
    r = client.get("/api/events?start_date=2008-09-01&end_date=2008-09-30&entity=ent_a")
    assert r.status_code == 200
    assert backend.calls[-1] == ("window", {"start": "2008-09-01", "end": "2008-09-30",
                                            "entity": "ent_a", "limit": 100})
    assert client.get("/api/events?start_date=not-a-date").status_code == 400


def test_invalid_id_is_400(client):
    assert client.get("/api/events/bad!id/neighborhood").status_code == 400


def test_evolution_links(client, backend):
    r = client.get("/api/evolution/links?min_score=0.5&event_id=evt_1")
    assert r.status_code == 200 and r.json["count"] == 1
    assert backend.calls[-1][1]["event_id"] == "evt_1"
    assert client.get("/api/evolution/links?min_score=2").status_code == 400
    assert client.get("/api/evolution/links?min_score=nan").status_code == 400


def test_graph_data(client):
    r = client.get("/api/graph/data?limit=10")
    assert r.status_code == 200
    assert {n["id"] for n in r.json["nodes"]} == {"ent_a", "evt_1"}
    assert len(r.json["edges"]) == 2
    assert client.get("/api/graph/data?start_date=2008-01-01").status_code == 400


def test_timeline_requires_end_date(client, backend):
    assert client.get("/api/graph/timeline").status_code == 400
    r = client.get("/api/graph/timeline?end_date=2008-09-30")
    assert r.status_code == 200
    assert r.json["stats"]["evolution_links"] == 1
    assert backend.calls[-1][1]["end"] == "2008-09-30"


@pytest.mark.parametrize("path", ["/api/risks", "/api/risks/systemic", "/api/evolution/chains",
                                  "/api/visualizations/three-layer", "/api/entities/ent_a/risks"])
def test_cypher_only_endpoints_return_501(client, path):
    assert client.get(path).status_code == 501


@pytest.mark.parametrize("path", ["/data/../.env", "/.env", "/docs/..%2F..%2F.env", "/api/../CLAUDE.md"])
def test_no_arbitrary_file_serving(client, path):
    assert client.get(path).status_code == 404


def test_unknown_route_json_404(client):
    r = client.get("/nope")
    assert r.status_code == 404 and r.json["status"] == "error"


def test_cors_disabled_by_default(client):
    r = client.get("/health", headers={"Origin": "https://evil.test"})
    assert "Access-Control-Allow-Origin" not in r.headers


def test_cors_allow_list(settings, backend):
    from dataclasses import replace
    app = create_app(settings=replace(settings, cors_origins=("https://ok.test",)), backend=backend)
    c = app.test_client()
    assert c.get("/health", headers={"Origin": "https://ok.test"}).headers.get(
        "Access-Control-Allow-Origin") == "https://ok.test"
    assert "Access-Control-Allow-Origin" not in c.get("/health", headers={"Origin": "https://evil.test"}).headers
