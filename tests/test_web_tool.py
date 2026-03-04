from types import SimpleNamespace

import gcpclaw.tools.web as web


def test_validate_public_http_url_blocks_localhost():
    valid, reason, ip = web._validate_public_http_url("http://localhost/admin")
    assert not valid
    assert "Blocked host" in reason
    assert ip is None


def test_validate_public_http_url_blocks_private_ip():
    valid, reason, ip = web._validate_public_http_url("http://127.0.0.1")
    assert not valid
    assert "Blocked private/internal address" in reason
    assert ip is None


def test_validate_returns_resolved_ip(monkeypatch):
    def fake_getaddrinfo(host, port, proto):
        return [(2, 1, 6, "", ("93.184.216.34", 443))]

    monkeypatch.setattr(web.socket, "getaddrinfo", fake_getaddrinfo)
    valid, reason, ip = web._validate_public_http_url("https://example.com")
    assert valid is True
    assert reason == "OK"
    assert ip == "93.184.216.34"


def test_fetch_url_blocks_redirect(monkeypatch):
    class FakePool:
        def urlopen(self, **kwargs):
            return SimpleNamespace(status=302, headers={}, data=b"")

    monkeypatch.setattr(
        web,
        "_validate_public_http_url",
        lambda _url: (True, "OK", "93.184.216.34"),
    )
    monkeypatch.setattr(web.urllib3, "HTTPSConnectionPool", lambda **kwargs: FakePool())

    result = web.fetch_url("https://example.com")
    assert result["error"] == "Redirects are blocked for security reasons"


def test_fetch_url_success(monkeypatch):
    html = b"<html><head><title>T</title></head><body>Hello</body></html>"

    class FakePool:
        def urlopen(self, **kwargs):
            return SimpleNamespace(status=200, headers={}, data=html)

    monkeypatch.setattr(
        web,
        "_validate_public_http_url",
        lambda _url: (True, "OK", "93.184.216.34"),
    )
    monkeypatch.setattr(web.urllib3, "HTTPSConnectionPool", lambda **kwargs: FakePool())

    result = web.fetch_url("https://example.com")
    assert result["title"] == "T"
    assert "Hello" in result["content"]


def test_search_web_no_api_configured(monkeypatch):
    monkeypatch.delenv("GOOGLE_CSE_API_KEY", raising=False)
    monkeypatch.delenv("GOOGLE_CSE_ID", raising=False)
    monkeypatch.delenv("SERPAPI_API_KEY", raising=False)
    result = web.search_web("test query")
    assert "error" in result
    assert "No search API configured" in result["error"]
