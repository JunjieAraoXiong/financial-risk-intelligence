# FE-EKG REST API

Flask service exposing the AllegroGraph-backed FE-EKG knowledge graph
(Capital IQ Lehman-crisis dataset) as JSON.

## Running

### Development

```bash
pip install -r requirements-dev.txt
cp .env.example .env          # fill in AG_USER / AG_PASS
FLASK_DEBUG=1 python -m api.app   # http://127.0.0.1:5001
```

`python -m api.app` binds to `127.0.0.1` and never enables the Werkzeug
debugger unless `FLASK_DEBUG=1` is set explicitly. Do not use it in production.

### Production

```bash
gunicorn -c gunicorn.conf.py api.wsgi:app
# or
docker build -t feekg-api .
docker run -p 5001:5001 --env-file .env feekg-api
```

The Docker image contains only the API code and `requirements-api.txt`
dependencies, and runs as a non-root user.

### Configuration

All settings come from environment variables (see `.env.example`):

| Variable | Default | Purpose |
|----------|---------|---------|
| `AG_URL` | `https://qa-agraph.nelumbium.ai` | AllegroGraph server |
| `AG_USER`, `AG_PASS` | — (required) | AllegroGraph credentials; no in-code defaults |
| `AG_CATALOG` / `AG_REPO` | `mycatalog` / `FEEKG` | Repository |
| `AG_TIMEOUT` / `AG_RETRIES` | `30` / `2` | Per-query timeout (s), retries on 502/503/504 |
| `CORS_ORIGINS` | empty (CORS off) | Comma-separated browser origins allowed |
| `API_MAX_LIMIT` | `5000` | Upper bound for any `limit` parameter |
| `CACHE_TTL` | `300` | Seconds aggregate statistics are cached |
| `LOG_LEVEL` | `INFO` | Logging level |
| `PORT`, `WEB_CONCURRENCY`, `GUNICORN_THREADS` | `5001`, `2`, `4` | Gunicorn |

## Conventions

- Success: `{"status": "success", ...}`; errors: `{"status": "error", "message": ..., "request_id": ...}`.
- Every response carries an `X-Request-ID` header (echoed from the request if supplied) that also appears in logs.
- Status codes: `400` invalid parameter, `404` unknown id/route, `501` endpoint not available on the RDF backend,
  `503` graph database unreachable, `500` unexpected error (details are logged, never returned).
- Ids are the local names used in the graph (`evt_…`, `ent_…`); dates are `YYYY-MM-DD`; scores are in `[0, 1]`.

## Endpoints

### Operations

| Endpoint | Description |
|----------|-------------|
| `GET /health` | Liveness. Does not touch the database. |
| `GET /ready` | Readiness. `200` if AllegroGraph answers, else `503`. |

### Data

| Endpoint | Parameters | Description |
|----------|------------|-------------|
| `GET /api/info` | | Totals, date range, event-type distribution |
| `GET /api/stats` | | Node/edge totals, top 10 entities by degree |
| `GET /api/entities` | | All entities |
| `GET /api/entities/<id>` | | One entity with its event count |
| `GET /api/events` | `offset`, `limit` (default 100) | Paginated events (`total`, `has_more`) |
| `GET /api/events` | `start_date`, `end_date`, `entity`, `limit` | Events in a date window, optionally involving an entity |
| `GET /api/events/high-impact` | `min_degree` (5), `limit` (100) | Events with the most evolution links |
| `GET /api/events/<id>` | | One event |
| `GET /api/events/<id>/neighborhood` | `min_score` (0.3) | 1-hop evolution neighbours |
| `GET /api/evolution/links` | `min_score` (0), `limit` (1000), `event_id` | Evolution links, strongest first, with the six component scores |
| `GET /api/evolution/stats` | | Count / min / avg / max score, strong (≥ 0.5) links |
| `GET /api/graph/data` | `limit` (500), `min_score` (0.3), `start_date`+`end_date` | Nodes/edges (`source`/`target`) for D3 / Cytoscape |
| `GET /api/graph/timeline` | `end_date` (required), `start_date`, `min_score`, `limit` (1000) | Nodes/edges (`from`/`to`) for vis.js |

### Not yet available (`501`)

These were implemented with Neo4j Cypher. Neo4j is retired and the Risk layer
is not yet loaded into AllegroGraph:

`/api/entities/<id>/risks`, `/api/evolution/chains`, `/api/risks`,
`/api/risks/systemic`, `/api/risks/distribution`, `/api/visualizations/*`.

## Example

```bash
curl "http://localhost:5001/api/evolution/links?min_score=0.5&limit=20"
```

```json
{
  "status": "success",
  "count": 20,
  "data": [
    {"from": "evt_123", "to": "evt_456", "score": 0.71, "type": "enhanced",
     "temporal": 0.9, "entity_overlap": 1.0, "semantic": 0.3,
     "topic": 0.5, "causality": 0.6, "emotional": 0.8}
  ]
}
```

## Testing

```bash
pytest            # API, SPARQL safety, backend, evolution methods
ruff check .
```

API tests inject a fake backend (`create_app(settings=..., backend=...)`), so no database is needed.
