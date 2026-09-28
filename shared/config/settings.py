"""
Centralized runtime settings for FE-EKG.

All configuration is read from environment variables (optionally loaded from
a local ``.env`` file). Credentials have no in-code defaults: a missing
``AG_USER`` / ``AG_PASS`` is reported by :meth:`Settings.missing_credentials`
rather than silently falling back to a hardcoded account.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from functools import lru_cache
from typing import List, Optional, Tuple

from dotenv import load_dotenv

load_dotenv()


def _env_list(name: str, default: str = "") -> List[str]:
    raw = os.getenv(name, default)
    return [item.strip() for item in raw.split(",") if item.strip()]


def _env_int(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None or raw == "":
        return default
    try:
        return int(raw)
    except ValueError as exc:
        raise ValueError(f"Environment variable {name} must be an integer, got {raw!r}") from exc


def _env_float(name: str, default: float) -> float:
    raw = os.getenv(name)
    if raw is None or raw == "":
        return default
    try:
        return float(raw)
    except ValueError as exc:
        raise ValueError(f"Environment variable {name} must be a number, got {raw!r}") from exc


@dataclass(frozen=True)
class Settings:
    """Immutable settings snapshot."""

    # AllegroGraph
    ag_url: str = "https://qa-agraph.nelumbium.ai"
    ag_user: Optional[str] = None
    ag_pass: Optional[str] = field(default=None, repr=False)
    ag_catalog: str = "mycatalog"
    ag_repo: str = "FEEKG"
    ag_timeout: float = 30.0
    ag_retries: int = 2

    # API
    cors_origins: Tuple[str, ...] = ()
    log_level: str = "INFO"
    api_max_limit: int = 5000
    cache_ttl: int = 300

    @classmethod
    def from_env(cls) -> "Settings":
        return cls(
            ag_url=os.getenv("AG_URL", cls.ag_url).rstrip("/"),
            ag_user=os.getenv("AG_USER") or None,
            ag_pass=os.getenv("AG_PASS") or None,
            ag_catalog=os.getenv("AG_CATALOG", cls.ag_catalog),
            ag_repo=os.getenv("AG_REPO", cls.ag_repo),
            ag_timeout=_env_float("AG_TIMEOUT", cls.ag_timeout),
            ag_retries=_env_int("AG_RETRIES", cls.ag_retries),
            cors_origins=tuple(_env_list("CORS_ORIGINS")),
            log_level=os.getenv("LOG_LEVEL", cls.log_level).upper(),
            api_max_limit=_env_int("API_MAX_LIMIT", cls.api_max_limit),
            cache_ttl=_env_int("CACHE_TTL", cls.cache_ttl),
        )

    @property
    def ag_repo_url(self) -> str:
        """SPARQL endpoint for the configured repository."""
        base = self.ag_url.rstrip("/")
        if self.ag_catalog and self.ag_catalog != "root":
            return f"{base}/catalogs/{self.ag_catalog}/repositories/{self.ag_repo}"
        return f"{base}/repositories/{self.ag_repo}"

    @property
    def ag_auth(self) -> Optional[Tuple[str, str]]:
        if self.ag_user and self.ag_pass:
            return (self.ag_user, self.ag_pass)
        return None

    def missing_credentials(self) -> List[str]:
        return [name for name, value in (("AG_USER", self.ag_user), ("AG_PASS", self.ag_pass)) if not value]

    def masked(self) -> dict:
        """Settings safe to log (no secrets)."""
        return {
            "ag_url": self.ag_url,
            "ag_catalog": self.ag_catalog,
            "ag_repo": self.ag_repo,
            "ag_user": (self.ag_user[:2] + "***") if self.ag_user else None,
            "ag_pass": "***" if self.ag_pass else None,
            "cors_origins": list(self.cors_origins),
            "log_level": self.log_level,
        }


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Process-wide settings (read once)."""
    return Settings.from_env()
