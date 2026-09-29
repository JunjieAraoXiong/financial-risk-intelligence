"""
Entity resolution: map a company name as written in a source to an entity id.

``ExactResolver`` is the ablation baseline (literal name match).
``OntologyResolver`` adds normalization, aliases, tickers and legal-suffix
stripping, and refuses to guess when a normalized key is ambiguous.
"""

from __future__ import annotations

import re
import unicodedata
from typing import Dict, Iterable, Optional, Protocol, Set

from radar.domain import Entity

_LEGAL_SUFFIXES = {
    "inc", "incorporated", "corp", "corporation", "co", "company", "companies", "plc", "ag", "sa", "nv",
    "ltd", "limited", "llc", "lp", "na", "the", "holdings", "holding", "group",
}


def normalize(name: str) -> str:
    """Lower-case, strip accents/punctuation, collapse whitespace. '&' becomes 'and'."""
    text = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode()
    text = text.lower().replace("&", " and ")
    text = re.sub(r"[^a-z0-9 ]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def strip_suffixes(normalized: str) -> str:
    tokens = [t for t in normalized.split() if t not in _LEGAL_SUFFIXES]
    while tokens and tokens[-1] == "and":
        tokens.pop()
    return " ".join(tokens)


class Resolver(Protocol):
    def resolve(self, mention: str) -> Optional[str]: ...


class ExactResolver:
    """Literal, case-sensitive match on the entity's primary name."""

    def __init__(self, entities: Iterable[Entity]):
        self._index = {e.name: e.id for e in entities}

    def resolve(self, mention: str) -> Optional[str]:
        return self._index.get(mention)


class OntologyResolver:
    """Resolution using names, aliases and tickers, from most to least specific."""

    def __init__(self, entities: Iterable[Entity]):
        self._exact: Dict[str, str] = {}
        self._normalized: Dict[str, Set[str]] = {}
        self._stripped: Dict[str, Set[str]] = {}
        self._tickers: Dict[str, str] = {}

        for e in entities:
            self._exact[e.name] = e.id
            if e.ticker:
                self._tickers[e.ticker.upper()] = e.id
            for label in (e.name, *e.aliases):
                n = normalize(label)
                if not n:
                    continue
                self._normalized.setdefault(n, set()).add(e.id)
                s = strip_suffixes(n)
                if s:
                    self._stripped.setdefault(s, set()).add(e.id)

    @staticmethod
    def _unique(ids: Optional[Set[str]]) -> Optional[str]:
        return next(iter(ids)) if ids and len(ids) == 1 else None

    def resolve(self, mention: str) -> Optional[str]:
        if not mention:
            return None
        if mention in self._exact:
            return self._exact[mention]
        n = normalize(mention)
        hit = self._unique(self._normalized.get(n))
        if hit:
            return hit
        if mention.strip().upper() in self._tickers:
            return self._tickers[mention.strip().upper()]
        return self._unique(self._stripped.get(strip_suffixes(n)))


def build_resolver(kind: str, entities: Iterable[Entity]) -> Resolver:
    if kind == "exact":
        return ExactResolver(entities)
    if kind == "ontology":
        return OntologyResolver(entities)
    raise ValueError(f"Unknown resolver {kind!r}")
