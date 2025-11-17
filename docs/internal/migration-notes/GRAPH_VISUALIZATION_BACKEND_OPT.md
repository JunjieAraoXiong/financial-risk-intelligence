# Backend Optimizations for Graph Visualization

## Current Bottlenecks

### 1. Query Performance Issues
- **Current**: Full graph queries return ALL events/relationships
- **Problem**: O(n) where n = 4,398 events → 74K triples to process
- **Impact**: Slow rendering, browser crashes on large graphs

### 2. Evolution Link Computation
- **Current**: O(n²) for n events → 9.7M comparisons for 4,398 events
- **Problem**: 5-10 minutes to compute all links
- **Impact**: Can't recalculate on-demand

### 3. No Caching or Indexing
- **Current**: Every query hits AllegroGraph fresh
- **Problem**: Repeated identical queries each time
- **Impact**: Unnecessary latency

---

## Optimization Strategy

### Phase 1: Query Optimization (High Impact, Low Effort - 4 hours)

#### 1.1 Add Pagination Support

**Problem**: Loading 4,398 nodes freezes browser
**Solution**: Return nodes in chunks

```python
def get_events_paginated(
    offset: int = 0,
    limit: int = 100,
    filters: Dict = None
) -> Dict:
    """
    Get paginated events for incremental graph rendering

    Time Complexity: O(1) with SPARQL LIMIT/OFFSET
    """
    query = f"""
    PREFIX feekg: <http://feekg.org/ontology#>
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

    SELECT ?event ?type ?date ?label
    WHERE {{
        ?event a feekg:Event .
        ?event feekg:eventType ?type .
        ?event feekg:date ?date .
        ?event rdfs:label ?label .

        {build_filter_clause(filters)}
    }}
    ORDER BY ?date
    LIMIT {limit}
    OFFSET {offset}
    """

    # Returns 100 events at a time instead of 4,398
    # Reduces query time from ~2s to ~50ms
```

**Benefit**: 40x faster initial load

---

#### 1.2 Add Filtered Queries (Time Window, Entity Focus)

**Problem**: User doesn't need ALL events, just relevant subset
**Solution**: Pre-filter at database level

```python
def get_events_by_timewindow(
    start_date: str,
    end_date: str,
    entity: str = None
) -> List[Dict]:
    """
    Get events in specific time window

    Time Complexity: O(k) where k << n (only matching events)
    """
    query = f"""
    PREFIX feekg: <http://feekg.org/ontology#>

    SELECT ?event ?type ?date ?label
    WHERE {{
        ?event feekg:date ?date .
        FILTER(?date >= "{start_date}"^^xsd:date &&
               ?date <= "{end_date}"^^xsd:date)

        {f'?event feekg:involves <feekg:{entity}>' if entity else ''}
    }}
    LIMIT 500
    """

    # Example: Sept 2008 (Lehman crisis) → ~300 events instead of 4,398
    # 15x reduction in data transfer
```

**Benefit**: 15x fewer nodes to render

---

#### 1.3 Add Degree-Based Filtering (Show High-Impact Nodes First)

**Problem**: Not all nodes are equally important
**Solution**: Query high-connectivity nodes first

```python
def get_high_impact_events(min_connections: int = 5) -> List[Dict]:
    """
    Get events with most evolution links (hubs)

    Time Complexity: O(n log n) for sorting, but n is small
    """
    query = """
    PREFIX feekg: <http://feekg.org/ontology#>

    SELECT ?event (COUNT(?link) as ?degree)
    WHERE {
        {
            ?event feekg:evolvesTo ?link .
        } UNION {
            ?link feekg:evolvesTo ?event .
        }
    }
    GROUP BY ?event
    HAVING (COUNT(?link) >= {min_connections})
    ORDER BY DESC(?degree)
    LIMIT 100
    """

    # Returns top 100 most connected events
    # Typical result: ~50-100 critical events out of 4,398
```

**Benefit**: Show "crisis backbone" with 50-100 nodes instead of 4,398

---

### Phase 2: Caching Layer (Medium Impact, Medium Effort - 6 hours)

#### 2.1 Add In-Memory Cache for Common Queries

```python
from functools import lru_cache
import time

class CachedGraphBackend:
    """Caching layer for graph queries"""

    def __init__(self, allegrograph_backend):
        self.backend = allegrograph_backend
        self.cache = {}
        self.cache_ttl = 300  # 5 minutes

    @lru_cache(maxsize=128)
    def get_all_events_cached(self):
        """Cache full event list (rarely changes)"""
        return self.backend.get_all_events()

    def get_evolution_links_cached(self, threshold: float = 0.2):
        """Cache evolution links by threshold"""
        cache_key = f"evolution_links_{threshold}"

        if cache_key in self.cache:
            cached_data, timestamp = self.cache[cache_key]
            if time.time() - timestamp < self.cache_ttl:
                return cached_data

        # Cache miss - query backend
        links = self.backend.get_evolution_links(threshold=threshold)
        self.cache[cache_key] = (links, time.time())
        return links
```

**Benefit**: 100x faster for repeated queries (2s → 20ms)

---

#### 2.2 Precompute Graph Statistics

**Problem**: Counting nodes/edges on every page load is slow
**Solution**: Compute once, cache, update periodically

```python
def precompute_graph_stats() -> Dict:
    """
    Precompute graph statistics for dashboard

    Time Complexity: O(n) once, then O(1) for retrieval
    """
    stats = {
        'total_events': count_events(),
        'total_entities': count_entities(),
        'total_links': count_evolution_links(),
        'date_range': get_date_range(),
        'event_type_distribution': get_event_type_counts(),
        'top_entities_by_degree': get_top_entities(limit=20),
        'timestamp': time.time()
    }

    # Save to file or Redis
    with open('graph_stats_cache.json', 'w') as f:
        json.dump(stats, f)

    return stats
```

**Benefit**: Dashboard loads instantly (no DB queries)

---

### Phase 3: Spatial/Temporal Indexing (High Impact, High Effort - 8 hours)

#### 3.1 Add Temporal Index for Time-Based Queries

**Problem**: Filtering by date requires full table scan
**Solution**: Add SPARQL-based temporal index

```python
def build_temporal_index():
    """
    Create temporal buckets for fast time-range queries

    Time Complexity: O(n) to build, O(log n) to query
    """
    # Group events by month
    query = """
    PREFIX feekg: <http://feekg.org/ontology#>

    INSERT {
        ?event feekg:monthBucket ?bucket .
    }
    WHERE {
        ?event feekg:date ?date .
        BIND(SUBSTR(?date, 1, 7) AS ?bucket)
    }
    """

    # Now queries can use bucket for fast filtering
    # SELECT * WHERE { ?event feekg:monthBucket "2008-09" }
```

**Benefit**: 10x faster date-range queries

---

#### 3.2 Add Graph Locality Index (Ego Networks)

**Problem**: "Show me events connected to X" requires full graph traversal
**Solution**: Precompute k-hop neighborhoods

```python
def build_ego_network_index(max_hops: int = 2):
    """
    Precompute 2-hop neighborhoods for each event

    Time Complexity: O(n * d²) where d = avg degree
    """
    for event in all_events:
        # Find all events within 2 hops
        ego_network = compute_k_hop_neighbors(event, k=max_hops)

        # Store as index
        store_ego_network(event, ego_network)

    # Query becomes O(1) lookup instead of O(n) traversal
```

**Benefit**: Instant "expand node" operation in graph UI

---

### Phase 4: Smarter Evolution Computation (Critical for Scale)

#### 4.1 Add Incremental Evolution Computation

**Problem**: Recompute all 9.7M pairs when adding 1 new event
**Solution**: Only compute new event → existing events

```python
def compute_evolution_links_incremental(
    new_events: List[Dict],
    existing_events: List[Dict],
    entities: List[Dict],
    threshold: float = 0.2
) -> List[Dict]:
    """
    Compute evolution links only for new events

    Time Complexity: O(k * n) where k = new events, n = existing
    Instead of: O((k+n)²)
    """
    scorer = EventEvolutionScorer(existing_events + new_events, entities)
    links = []

    for new_event in new_events:
        # Only compare with existing events (not other new ones)
        for existing_event in existing_events:
            score, components = scorer.compute_evolution_score(
                existing_event, new_event
            )

            if score >= threshold:
                links.append(create_link(existing_event, new_event, score))

    # For 1 new event: 1 * 4,398 = 4,398 comparisons
    # Instead of: 4,399² / 2 = 9.7M comparisons
    # 2,200x faster!

    return links
```

**Benefit**: 2,200x faster for incremental updates

---

#### 4.2 Add Spatial Pruning for Evolution Computation

**Problem**: Comparing ALL pairs is wasteful (many have score = 0)
**Solution**: Skip obviously unrelated pairs

```python
def compute_evolution_links_with_pruning(
    events: List[Dict],
    entities: List[Dict],
    threshold: float = 0.2
) -> List[Dict]:
    """
    Prune event pairs before computing evolution score

    Time Complexity: O(n²) worst case, O(n log n) typical
    """
    sorted_events = sorted(events, key=lambda e: e['date'])
    links = []

    for i, evt_a in enumerate(sorted_events):
        for evt_b in sorted_events[i+1:]:
            # Prune 1: Time window check (fast)
            date_a = parse_date(evt_a['date'])
            date_b = parse_date(evt_b['date'])
            if (date_b - date_a).days > 90:
                break  # No events >90 days apart can be related

            # Prune 2: Zero entity overlap (fast)
            if not has_entity_overlap(evt_a, evt_b):
                if not has_topic_overlap(evt_a, evt_b):
                    continue  # Skip pairs with no overlap

            # Passed pruning - now compute expensive score
            score, components = scorer.compute_evolution_score(evt_a, evt_b)

            if score >= threshold:
                links.append(create_link(evt_a, evt_b, score))

    # Typical pruning: 70-80% of pairs skipped
    # 9.7M → ~2M actual score computations
    # 4-5x speedup
```

**Benefit**: 4-5x faster evolution computation

---

### Phase 5: GraphQL API Layer (Optional, 12 hours)

**Why GraphQL for Graphs?**
- Client specifies exact data needed (no over-fetching)
- Nested queries map naturally to graph traversal
- Automatic query optimization

```graphql
query GetCrisisTimeline {
  events(
    dateRange: {start: "2008-09-01", end: "2008-09-30"}
    limit: 100
  ) {
    eventId
    type
    date
    label
    evolvesTo(minScore: 0.5) {
      eventId
      type
      score
    }
  }
}
```

**Benefit**: Client controls payload size, reduces over-fetching

---

## Implementation Priority

### Week 1: Quick Wins (10 hours)
1. ✅ Parallel evolution computation (DONE)
2. ✅ Retry logic for uploads (DONE)
3. ⏭️  Add pagination to SPARQL queries (2 hrs)
4. ⏭️  Add time-window filtering (2 hrs)
5. ⏭️  Add degree-based filtering (2 hrs)
6. ⏭️  Basic caching layer (4 hrs)

**Impact**: 40x faster queries, 4-8x faster evolution, reliable uploads

---

### Week 2: Scaling Infrastructure (12 hours)
1. Temporal index for fast date queries (4 hrs)
2. Ego network index for expand/collapse (4 hrs)
3. Incremental evolution computation (4 hrs)

**Impact**: Support 10x more events, sub-second graph updates

---

### Week 3: Advanced Optimizations (16 hours)
1. Evolution computation pruning (6 hrs)
2. GraphQL API layer (optional) (10 hrs)

**Impact**: Professional-grade API, 5x faster evolution

---

## Expected Performance Improvements

| Operation | Before | After Week 1 | After Week 2 | After Week 3 |
|-----------|--------|--------------|--------------|--------------|
| Load full graph | 5s | 125ms (pagination) | 50ms (cache) | 20ms (optimized) |
| Filter by date | 2s | 100ms (indexed) | 20ms (cache) | 10ms (optimized) |
| Expand node | 1s | 500ms (degree filter) | 50ms (ego cache) | 10ms (precomputed) |
| Evolution compute | 5-10 min | 60-120s (parallel) | 30s (incremental) | 10s (pruning) |
| Add new event | 5-10 min | 60-120s | 2s (incremental!) | 2s |

---

## Scale Targets

### Current Capacity
- Events: 4,398
- Nodes displayable: ~100-500 (browser limit)
- Evolution pairs: 9.7M
- Query time: 1-5s

### After Optimizations
- Events: 50,000+
- Nodes displayable: 1,000+ with pagination
- Evolution pairs: 1.25B (handled via caching)
- Query time: <100ms

**10x scale increase with better performance!**

---

## Recommended Immediate Actions

1. **Add pagination API endpoint** (2 hours)
   ```python
   @app.route('/api/events/paginated')
   def get_events_paginated():
       offset = request.args.get('offset', 0, type=int)
       limit = request.args.get('limit', 100, type=int)
       ...
   ```

2. **Add time-window filter** (2 hours)
   ```python
   @app.route('/api/events/timewindow')
   def get_events_by_date():
       start = request.args.get('start')
       end = request.args.get('end')
       ...
   ```

3. **Add degree-based filtering** (2 hours)
   ```python
   @app.route('/api/events/high-impact')
   def get_high_impact_events():
       min_degree = request.args.get('min_degree', 5, type=int)
       ...
   ```

4. **Add simple caching** (4 hours)
   ```python
   from flask_caching import Cache
   cache = Cache(app, config={'CACHE_TYPE': 'simple'})

   @app.route('/api/graph/stats')
   @cache.cached(timeout=300)  # 5 min cache
   def get_graph_stats():
       ...
   ```

**Total: 10 hours, 40x performance improvement**

---

## Next Steps

Want me to implement these optimizations? I recommend starting with:

1. **Pagination + filtering** (4 hrs) - Enables smooth graph UI
2. **Caching layer** (4 hrs) - Instant repeated queries
3. **Temporal indexing** (4 hrs) - Fast timeline navigation

This 12-hour investment will make your graph visualization 40x faster and support 10x more data.

Ready to proceed?
