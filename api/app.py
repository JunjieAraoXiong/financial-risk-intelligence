"""
FE-EKG REST API Application

Flask REST API serving the AllegroGraph-backed FE-EKG knowledge graph.

Run in development:   python -m api.app
Run in production:    gunicorn -c gunicorn.conf.py api.wsgi:app
"""

from __future__ import annotations

import logging
import os
import sys
import time
import uuid
from typing import Callable, Optional

if __package__ in (None, ""):  # executed as a script: python api/app.py
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask, g, jsonify, request
from flask_cors import CORS
from werkzeug.exceptions import HTTPException

from feekg_core.query.optimized_graph_queries import GraphQueryError, OptimizedGraphBackend
from feekg_core.query.sparql import InvalidQueryParameter, iso_date
from shared.config.settings import Settings, get_settings

API_VERSION = "2.1.0"
EARLIEST_DATE = "0001-01-01"

logger = logging.getLogger("feekg.api")


class BadRequest(ValueError):
    """Invalid client input (rendered as HTTP 400)."""


def configure_logging(level: str) -> None:
    root = logging.getLogger()
    if not root.handlers:
        logging.basicConfig(
            level=level,
            format="%(asctime)s %(levelname)s %(name)s %(message)s",
        )
    root.setLevel(level)


def _arg(name: str, cast: Callable, default, minimum=None, maximum=None):
    """Read a query parameter, cast it and enforce bounds (HTTP 400 on failure)."""
    raw = request.args.get(name)
    if raw is None or raw == "":
        return default
    try:
        value = cast(raw)
    except (TypeError, ValueError):
        raise BadRequest(f"Query parameter '{name}' must be of type {cast.__name__}") from None
    if cast is float and value != value:  # NaN
        raise BadRequest(f"Query parameter '{name}' must be a number")
    if minimum is not None and value < minimum:
        raise BadRequest(f"Query parameter '{name}' must be >= {minimum}")
    if maximum is not None and value > maximum:
        raise BadRequest(f"Query parameter '{name}' must be <= {maximum}")
    return value


def _date_arg(name: str, required: bool = False) -> Optional[str]:
    raw = request.args.get(name)
    if not raw:
        if required:
            raise BadRequest(f"Query parameter '{name}' is required (format: YYYY-MM-DD)")
        return None
    try:
        return iso_date(raw, name)
    except InvalidQueryParameter as exc:
        raise BadRequest(str(exc)) from None


def _ok(**payload):
    return jsonify({"status": "success", **payload})


def _error(message: str, status: int, **extra):
    body = {"status": "error", "message": message, **extra}
    if getattr(g, "request_id", None):
        body["request_id"] = g.request_id
    return jsonify(body), status


def create_app(settings: Optional[Settings] = None, backend: Optional[OptimizedGraphBackend] = None) -> Flask:
    """Create and configure the Flask application.

    ``settings`` and ``backend`` can be injected (tests); by default they are
    built from environment variables.
    """
    settings = settings or get_settings()
    configure_logging(settings.log_level)

    app = Flask(__name__)
    app.json.sort_keys = False
    app.config["SETTINGS"] = settings

    # CORS: explicit allow-list from CORS_ORIGINS. Empty means same-origin only.
    if settings.cors_origins:
        CORS(app, origins=list(settings.cors_origins))

    if settings.missing_credentials() and backend is None:
        logger.warning("AllegroGraph credentials not set (%s); data endpoints will fail",
                       ", ".join(settings.missing_credentials()))

    graph = backend or OptimizedGraphBackend(settings)
    app.extensions["feekg_backend"] = graph
    max_limit = settings.api_max_limit

    # ======================================================================
    # REQUEST LIFECYCLE
    # ======================================================================

    @app.before_request
    def _start_request():
        g.request_id = request.headers.get("X-Request-ID") or uuid.uuid4().hex
        g.start_time = time.perf_counter()

    @app.after_request
    def _finish_request(response):
        response.headers["X-Request-ID"] = g.get("request_id", "")
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("Referrer-Policy", "no-referrer")
        response.headers.setdefault("Cache-Control", "no-store")
        elapsed_ms = (time.perf_counter() - g.get("start_time", time.perf_counter())) * 1000
        logger.info("%s %s %s %.1fms request_id=%s", request.method, request.path,
                    response.status_code, elapsed_ms, g.get("request_id"))
        return response

    # ======================================================================
    # ERROR HANDLERS
    # ======================================================================

    @app.errorhandler(BadRequest)
    @app.errorhandler(InvalidQueryParameter)
    def _bad_request(exc):
        return _error(str(exc), 400)

    @app.errorhandler(GraphQueryError)
    def _graph_unavailable(exc):
        logger.error("Graph backend error: %s request_id=%s", exc, g.get("request_id"))
        return _error("Graph database unavailable", 503)

    @app.errorhandler(HTTPException)
    def _http_error(exc):
        return _error(exc.description or exc.name, exc.code or 500)

    @app.errorhandler(Exception)
    def _unhandled(exc):
        logger.exception("Unhandled error request_id=%s", g.get("request_id"))
        return _error("Internal server error", 500)

    # ======================================================================
    # HEALTH & INFO
    # ======================================================================

    @app.route("/health", methods=["GET"])
    def health():
        """Liveness probe: the process is up. Does not touch the database."""
        return jsonify({"status": "healthy", "service": "FE-EKG API", "version": API_VERSION})

    @app.route("/ready", methods=["GET"])
    def ready():
        """Readiness probe: the graph database is reachable."""
        try:
            graph.ping()
        except GraphQueryError:
            return jsonify({"status": "unavailable", "database": "unreachable"}), 503
        return jsonify({"status": "ready", "database": "reachable"})

    @app.route("/api/info", methods=["GET"])
    def info():
        """Dataset overview: totals, date range and event-type distribution."""
        stats = graph.get_graph_stats_cached()
        return _ok(data={
            "api_version": API_VERSION,
            "database": {"type": "allegrograph", "repository": settings.ag_repo},
            **{k: v for k, v in stats.items() if k != "timestamp"},
        })

    @app.route("/api/stats", methods=["GET"])
    def get_stats():
        return _ok(data=graph.get_graph_stats())

    # ======================================================================
    # ENTITIES
    # ======================================================================

    @app.route("/api/entities", methods=["GET"])
    def get_entities():
        entities = graph.get_all_entities()
        return _ok(count=len(entities), data=entities)

    @app.route("/api/entities/<entity_id>", methods=["GET"])
    def get_entity(entity_id):
        entity = graph.get_entity_by_id(entity_id)
        if not entity:
            return _error("Entity not found", 404)
        return _ok(data=entity)

    # ======================================================================
    # EVENTS
    # ======================================================================

    @app.route("/api/events", methods=["GET"])
    def get_events():
        start_date = _date_arg("start_date")
        end_date = _date_arg("end_date")
        limit = _arg("limit", int, 100, minimum=1, maximum=max_limit)

        if start_date or end_date:
            events = graph.get_events_by_timewindow(
                start_date or EARLIEST_DATE,
                end_date or "9999-12-31",
                entity_filter=request.args.get("entity") or None,
                limit=limit,
            )
            return _ok(count=len(events), data=events)

        offset = _arg("offset", int, 0, minimum=0)
        result = graph.get_events_paginated(offset=offset, limit=limit)
        return _ok(
            data=result["events"],
            total=result["total"],
            offset=result["offset"],
            limit=result["limit"],
            has_more=result["has_more"],
            count=len(result["events"]),
        )

    @app.route("/api/events/high-impact", methods=["GET"])
    def get_high_impact_events():
        min_degree = _arg("min_degree", int, 5, minimum=0)
        limit = _arg("limit", int, 100, minimum=1, maximum=max_limit)
        events = graph.get_high_impact_events(min_degree=min_degree, limit=limit)
        return _ok(count=len(events), data=events)

    @app.route("/api/events/<event_id>", methods=["GET"])
    def get_event(event_id):
        event = graph.get_event_by_id(event_id)
        if not event:
            return _error("Event not found", 404)
        return _ok(data=event)

    @app.route("/api/events/<event_id>/neighborhood", methods=["GET"])
    def get_event_neighborhood(event_id):
        min_score = _arg("min_score", float, 0.3, minimum=0.0, maximum=1.0)
        return _ok(data=graph.get_event_neighborhood(event_id, max_hops=1, min_score=min_score))

    # ======================================================================
    # EVOLUTION
    # ======================================================================

    @app.route("/api/evolution/links", methods=["GET"])
    def get_evolution_links():
        min_score = _arg("min_score", float, 0.0, minimum=0.0, maximum=1.0)
        limit = _arg("limit", int, 1000, minimum=1, maximum=max_limit)
        event_id = request.args.get("event_id") or None
        links = graph.get_evolution_links(limit=limit, min_score=min_score, event_id=event_id)
        return _ok(count=len(links), data=links)

    @app.route("/api/evolution/stats", methods=["GET"])
    def get_evolution_stats():
        return _ok(data=graph.get_evolution_statistics())

    # ======================================================================
    # GRAPH DATA (for D3.js / Cytoscape.js / vis.js frontends)
    # ======================================================================

    @app.route("/api/graph/data", methods=["GET"])
    def get_graph_data():
        limit_events = _arg("limit", int, 500, minimum=1, maximum=max_limit)
        min_score = _arg("min_score", float, 0.3, minimum=0.0, maximum=1.0)
        start_date = _date_arg("start_date")
        end_date = _date_arg("end_date")
        if bool(start_date) != bool(end_date):
            raise BadRequest("start_date and end_date must be provided together")

        data = graph.get_graph_data_for_viz(
            limit_events=limit_events,
            min_evolution_score=min_score,
            start_date=start_date,
            end_date=end_date,
        )

        nodes = [
            {"id": e["id"], "label": e["name"], "type": "entity", "group": "entity", "data": e}
            for e in data["nodes"]["entities"]
        ] + [
            {"id": e["eventId"], "label": e["label"], "type": e["type"], "group": "event", "data": e}
            for e in data["nodes"]["events"]
        ]
        edges = [
            {"id": f"{link['from']}-{link['to']}", "source": link["from"], "target": link["to"],
             "type": "evolves_to", "weight": link["score"], "data": link}
            for link in data["edges"]["evolution"]
        ] + [
            {"id": f"{r['event']}-{r['entity']}", "source": r["event"], "target": r["entity"],
             "type": r["type"], "data": r}
            for r in data["edges"]["event_entity"]
        ]
        return _ok(nodes=nodes, edges=edges, stats=data["stats"])

    @app.route("/api/graph/timeline", methods=["GET"])
    def get_timeline_graph():
        """Graph of all events up to ``end_date`` (vis.js node/edge format)."""
        end_date = _date_arg("end_date", required=True)
        start_date = _date_arg("start_date") or EARLIEST_DATE
        min_score = _arg("min_score", float, 0.3, minimum=0.0, maximum=1.0)
        limit_events = _arg("limit", int, 1000, minimum=1, maximum=max_limit)

        data = graph.get_graph_data_for_viz(
            limit_events=limit_events,
            min_evolution_score=min_score,
            start_date=start_date,
            end_date=end_date,
        )
        entities = data["nodes"]["entities"]
        events = data["nodes"]["events"]
        links = data["edges"]["evolution"]

        nodes = [
            {"id": e["id"], "label": e["name"], "type": "entity", "group": "entity",
             "title": f"{e['name']}<br>{e['type']}", "data": e}
            for e in entities
        ] + [
            {"id": e["eventId"], "label": e["type"], "type": "event", "group": "event",
             "title": f"{e['type']}<br>{e['date']}<br>{e['label'][:50]}", "data": e}
            for e in events
        ]
        edges = [
            {"from": r["event"], "to": r["entity"], "type": "involves", "arrows": "to", "dashes": False,
             "color": {"color": "#64748b", "opacity": 0.6}, "width": 1.5}
            for r in data["edges"]["event_entity"]
        ] + [
            {"from": link["from"], "to": link["to"], "type": "evolves_to", "arrows": "to",
             "width": max(1.5, link["score"] * 3),
             "color": {"color": "#8b5cf6", "opacity": 0.7 + link["score"] * 0.3},
             "title": f"Score: {link['score']:.3f}<br>Causality: {link['causality']:.3f}",
             "data": link}
            for link in links
        ]
        return _ok(
            endDate=end_date,
            nodes=nodes,
            edges=edges,
            stats={"entities": len(entities), "events": len(events), "risks": 0,
                   "evolution_links": len(links)},
        )

    # ======================================================================
    # NOT YET AVAILABLE ON THE RDF BACKEND
    # ======================================================================
    # These endpoints were implemented with Neo4j Cypher queries. Neo4j has
    # been retired and the AllegroGraph repository does not yet contain the
    # Risk layer, so they answer 501 instead of failing with a 500.

    def _not_implemented(*_args, **_kwargs):
        return _error(
            "Not available: this endpoint depends on the Risk layer, which is not yet "
            "loaded into the AllegroGraph backend",
            501,
        )

    for rule in (
        "/api/entities/<entity_id>/risks",
        "/api/evolution/chains",
        "/api/risks",
        "/api/risks/systemic",
        "/api/risks/distribution",
        "/api/visualizations/<name>",
    ):
        app.add_url_rule(rule, endpoint=f"not_implemented:{rule}", view_func=_not_implemented,
                         methods=["GET"])

    return app


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5001))
    debug = os.environ.get("FLASK_DEBUG", "").lower() in ("1", "true", "yes")
    host = os.environ.get("HOST", "127.0.0.1")
    create_app().run(debug=debug, host=host, port=port)
