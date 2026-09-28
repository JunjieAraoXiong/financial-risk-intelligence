"""
SPARQL safety helpers.

Every value that reaches a SPARQL string built by this package must pass
through one of these functions, so request parameters can never alter the
structure of a query.
"""

from __future__ import annotations

import math
import re
from datetime import date
from typing import Iterable, List

FEEKG_NS = "http://feekg.org/ontology#"

PREFIXES = """PREFIX feekg: <http://feekg.org/ontology#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
"""

# Local names produced by the ingestion pipeline (e.g. ``evt_123``,
# ``ent_lehman_brothers``). Deliberately excludes characters that are
# meaningful in SPARQL/IRIs (<, >, ", {, }, whitespace, etc.).
_LOCAL_NAME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.\-]{0,199}$")


class InvalidQueryParameter(ValueError):
    """Raised when a user-supplied value is not safe/valid for a query."""


def local_name(value: str, field: str = "id") -> str:
    """Validate an identifier used as the local part of a ``feekg:`` IRI."""
    if not isinstance(value, str) or not _LOCAL_NAME_RE.match(value):
        raise InvalidQueryParameter(f"Invalid {field}: must match {_LOCAL_NAME_RE.pattern}")
    return value


def iri(value: str, field: str = "id") -> str:
    """Full ``<http://feekg.org/ontology#value>`` IRI for a validated id."""
    return f"<{FEEKG_NS}{local_name(value, field)}>"


def iri_list(values: Iterable[str], field: str = "id") -> str:
    """Comma-separated IRIs, suitable for ``FILTER(?x IN (...))``."""
    return ", ".join(iri(v, field) for v in values)


def iso_date(value: str, field: str = "date") -> str:
    """Validate a ``YYYY-MM-DD`` date and return it normalized."""
    try:
        return date.fromisoformat(value).isoformat()
    except (TypeError, ValueError):
        raise InvalidQueryParameter(f"Invalid {field}: expected YYYY-MM-DD") from None


def number(value, field: str = "value") -> str:
    """Render a finite float for inclusion in a query."""
    try:
        f = float(value)
    except (TypeError, ValueError):
        raise InvalidQueryParameter(f"Invalid {field}: expected a number") from None
    if not math.isfinite(f):
        raise InvalidQueryParameter(f"Invalid {field}: must be finite")
    return repr(f)


def integer(value, field: str = "value", minimum: int = 0) -> int:
    """Validate a non-negative (by default) integer."""
    try:
        i = int(value)
    except (TypeError, ValueError):
        raise InvalidQueryParameter(f"Invalid {field}: expected an integer") from None
    if i < minimum:
        raise InvalidQueryParameter(f"Invalid {field}: must be >= {minimum}")
    return i


def choice(value: str, allowed: Iterable[str], field: str = "value") -> str:
    allowed_list: List[str] = list(allowed)
    if value not in allowed_list:
        raise InvalidQueryParameter(f"Invalid {field}: must be one of {', '.join(allowed_list)}")
    return value


def local_id_from_uri(uri: str) -> str:
    """Extract the local name from a ``...#name`` or ``.../name`` URI."""
    return uri.rsplit("#", 1)[-1] if "#" in uri else uri.rsplit("/", 1)[-1]
