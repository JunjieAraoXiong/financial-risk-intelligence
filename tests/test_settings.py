from shared.config.settings import Settings


def test_from_env(monkeypatch):
    monkeypatch.setenv("AG_URL", "https://host.test/")
    monkeypatch.setenv("AG_USER", "alice")
    monkeypatch.setenv("AG_PASS", "secret")
    monkeypatch.setenv("AG_CATALOG", "cat")
    monkeypatch.setenv("AG_REPO", "R")
    monkeypatch.setenv("CORS_ORIGINS", "https://a.test, https://b.test")
    s = Settings.from_env()
    assert s.ag_repo_url == "https://host.test/catalogs/cat/repositories/R"
    assert s.ag_auth == ("alice", "secret")
    assert s.cors_origins == ("https://a.test", "https://b.test")
    assert s.missing_credentials() == []


def test_no_default_credentials(monkeypatch):
    monkeypatch.delenv("AG_USER", raising=False)
    monkeypatch.delenv("AG_PASS", raising=False)
    s = Settings.from_env()
    assert s.ag_auth is None
    assert s.missing_credentials() == ["AG_USER", "AG_PASS"]


def test_masked_and_repr_hide_password():
    s = Settings(ag_user="alice", ag_pass="topsecret")
    assert "topsecret" not in repr(s)
    assert "topsecret" not in str(s.masked())


def test_root_catalog_url():
    s = Settings(ag_url="https://h", ag_catalog="root", ag_repo="R")
    assert s.ag_repo_url == "https://h/repositories/R"
