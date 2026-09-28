import os
import sys

import pytest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from shared.config.settings import Settings  # noqa: E402


@pytest.fixture
def settings():
    return Settings(ag_url="https://ag.example.test", ag_user="u", ag_pass="p",
                    ag_catalog="cat", ag_repo="REPO", cache_ttl=60, api_max_limit=1000)
