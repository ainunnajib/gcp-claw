from types import SimpleNamespace

import gcpclaw.tools.web as web


def test_validate_public_http_url_blocks_localhost():
    valid, reason = web._validate_public_http_url("http://localhost/admin")
    assert not valid
    assert "Blocked host" in reason


def test_validate_public_http_url_blocks_private_ip():
    valid, reason = web._validate_public_http_url("http://127.0.0.1")
    assert not valid
    assert "Blocked private/internal address" in reason


def test_fetch_url_blocks_redirect(monkeypatch):
    def fake_get(*args, **kwargs):
        return SimpleNamespace(is_redirect=True)

    monkeypatch.setattr(web, "_validate_public_http_url", lambda _url: (True, "OK"))
    monkeypatch.setattr(web.requests, "get", fake_get)

    result = web.fetch_url("https://example.com")
    assert result["error"] == "Redirects are blocked for security reasons"
