"""
Point-in-time ontology graph: ownership hierarchy and exposure network.

``affected(entity, on_date, ...)`` answers: if ``entity`` is hit by an event on
``on_date``, which entities are affected, how strongly, and through which path?
Only relations active on ``on_date`` are used, so an acquisition that closes
later cannot leak into an earlier alert.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import date
from typing import Dict, Iterable, List, Tuple

from radar.domain import EXPOSED_TO, PEER, SUBSIDIARY_OF, Entity, Relation


@dataclass(frozen=True)
class Impact:
    entity_id: str
    weight: float
    path: Tuple[str, ...]


class OntologyGraph:
    def __init__(self, entities: Iterable[Entity], relations: Iterable[Relation] = ()):
        self.entities: Dict[str, Entity] = {e.id: e for e in entities}
        self._parents: Dict[str, List[Relation]] = defaultdict(list)     # child -> subsidiary_of relations
        self._impacted_by: Dict[str, List[Tuple[str, Relation]]] = defaultdict(list)  # shocked -> (hit, rel)

        for r in relations:
            for endpoint in (r.source, r.target):
                if endpoint not in self.entities:
                    raise ValueError(f"Relation references unknown entity {endpoint!r}")
            if r.kind == SUBSIDIARY_OF:
                self._parents[r.source].append(r)
            elif r.kind == EXPOSED_TO:
                # source is exposed to target: a shock at target reaches source.
                self._impacted_by[r.target].append((r.source, r))
            elif r.kind == PEER:
                self._impacted_by[r.target].append((r.source, r))
                self._impacted_by[r.source].append((r.target, r))

    def parents(self, entity_id: str, on_date: date) -> List[str]:
        return [r.target for r in self._parents.get(entity_id, ()) if r.active_on(on_date)]

    def roll_up(self, entity_id: str, on_date: date) -> List[Tuple[str, Tuple[str, ...]]]:
        """The entity and all its owners on ``on_date``, each with the ownership path."""
        out = [(entity_id, (entity_id,))]
        seen = {entity_id}
        frontier = out[:]
        while frontier:
            nxt = []
            for eid, path in frontier:
                for parent in self.parents(eid, on_date):
                    if parent not in seen:
                        seen.add(parent)
                        nxt.append((parent, path + (parent,)))
            out.extend(nxt)
            frontier = nxt
        return out

    def affected(
        self,
        entity_id: str,
        on_date: date,
        use_hierarchy: bool = True,
        max_hops: int = 1,
        decay: float = 0.5,
    ) -> List[Impact]:
        """Entities affected by a shock at ``entity_id``; strongest path wins per entity."""
        best: Dict[str, Impact] = {}

        def visit(eid: str, weight: float, path: Tuple[str, ...]):
            current = best.get(eid)
            if current is None or weight > current.weight:
                best[eid] = Impact(eid, weight, path)

        def expand(eid: str, weight: float, path: Tuple[str, ...]) -> List[Impact]:
            if not use_hierarchy:
                return [Impact(eid, weight, path)]
            return [Impact(p, weight, path + sub[1:]) for p, sub in self.roll_up(eid, on_date)]

        frontier = expand(entity_id, 1.0, (entity_id,))
        for imp in frontier:
            visit(imp.entity_id, imp.weight, imp.path)

        for _ in range(max_hops):
            nxt: List[Impact] = []
            for imp in frontier:
                for hit, rel in self._impacted_by.get(imp.entity_id, ()):
                    if not rel.active_on(on_date) or hit in imp.path:
                        continue
                    w = imp.weight * decay * rel.weight
                    for reached in expand(hit, w, imp.path + (hit,)):
                        if reached.entity_id in best and best[reached.entity_id].weight >= reached.weight:
                            continue
                        visit(reached.entity_id, reached.weight, reached.path)
                        nxt.append(reached)
            frontier = nxt

        return sorted(best.values(), key=lambda i: (-i.weight, i.entity_id))
