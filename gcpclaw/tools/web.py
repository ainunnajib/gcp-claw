"""Web search and URL fetching tools."""

import ipaddress
import os
import socket
from typing import cast
from urllib.parse import urlparse

import requests
import urllib3
from bs4 import BeautifulSoup

BLOCKED_HOSTS = {
    "localhost",
    "metadata.google.internal",
    "169.254.169.254",
}


def _is_blocked_ip(ip: str) -> bool:
    ip_obj = ipaddress.ip_address(ip)
    return any(
        [
            ip_obj.is_private,
            ip_obj.is_loopback,
            ip_obj.is_link_local,
            ip_obj.is_multicast,
            ip_obj.is_reserved,
            ip_obj.is_unspecified,
        ]
    )


def _validate_public_http_url(url: str) -> tuple[bool, str, str | None]:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"}:
        return False, "Only http/https URLs are allowed", None
    if not parsed.hostname:
        return False, "URL must include a valid hostname", None
    host = parsed.hostname.lower()
    if host in BLOCKED_HOSTS:
        return False, f"Blocked host: {host}", None

    try:
        infos = socket.getaddrinfo(host, parsed.port, proto=socket.IPPROTO_TCP)
    except socket.gaierror:
        return False, "Hostname could not be resolved", None

    resolved_ip: str | None = None
    for info in infos:
        ip = cast(str, info[4][0])
        if resolved_ip is None:
            resolved_ip = ip
        if _is_blocked_ip(ip):
            return False, f"Blocked private/internal address: {ip}", None
    return True, "OK", resolved_ip


def search_web(query: str, num_results: int = 5) -> dict:
    """Search the web for information.

    Supports Google Custom Search Engine (CSE) or SerpAPI.
    Set the appropriate API keys in .env.

    Args:
        query: The search query.
        num_results: Number of results to return (default 5, max 10).

    Returns:
        dict with 'results' list or 'error'.
    """
    num_results = min(num_results, 10)

    # Try Google Custom Search first
    cse_key = os.getenv("GOOGLE_CSE_API_KEY")
    cse_id = os.getenv("GOOGLE_CSE_ID")
    if cse_key and cse_id:
        return _search_google_cse(query, num_results, cse_key, cse_id)

    # Try SerpAPI
    serpapi_key = os.getenv("SERPAPI_API_KEY")
    if serpapi_key:
        return _search_serpapi(query, num_results, serpapi_key)

    return {
        "error": (
            "No search API configured. Set GOOGLE_CSE_API_KEY+GOOGLE_CSE_ID "
            "or SERPAPI_API_KEY in .env"
        )
    }


def _search_google_cse(query: str, num: int, api_key: str, cse_id: str) -> dict:
    try:
        params: dict[str, str | int] = {
            "key": api_key,
            "cx": cse_id,
            "q": query,
            "num": num,
        }
        resp = requests.get(
            "https://www.googleapis.com/customsearch/v1",
            params=params,
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()
        results = [
            {"title": item["title"], "url": item["link"], "snippet": item.get("snippet", "")}
            for item in data.get("items", [])
        ]
        return {"query": query, "results": results}
    except (requests.RequestException, KeyError, ValueError) as e:
        return {"error": f"Google CSE search failed: {e}"}


def _search_serpapi(query: str, num: int, api_key: str) -> dict:
    try:
        params: dict[str, str | int] = {
            "api_key": api_key,
            "q": query,
            "num": num,
            "engine": "google",
        }
        resp = requests.get(
            "https://serpapi.com/search",
            params=params,
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()
        results = [
            {"title": r["title"], "url": r["link"], "snippet": r.get("snippet", "")}
            for r in data.get("organic_results", [])
        ]
        return {"query": query, "results": results}
    except (requests.RequestException, KeyError, ValueError) as e:
        return {"error": f"SerpAPI search failed: {e}"}


def fetch_url(url: str) -> dict:
    """Fetch a web page and extract its readable text content.

    Converts HTML to clean text, stripping scripts, styles, and navigation.

    Args:
        url: The URL to fetch.

    Returns:
        dict with 'title', 'content' (text), and 'url', or 'error'.
    """
    is_valid, reason, resolved_ip = _validate_public_http_url(url)
    if not is_valid:
        return {"error": reason}
    if not resolved_ip:
        return {"error": "URL validation failed to resolve host"}

    try:
        parsed = urlparse(url)
        if not parsed.hostname:
            return {"error": "URL must include a valid hostname"}
        port = parsed.port or (443 if parsed.scheme == "https" else 80)
        path_and_query = parsed.path or "/"
        if parsed.query:
            path_and_query = f"{path_and_query}?{parsed.query}"
        headers = {
            "User-Agent": "GCPClaw/1.0 (personal AI assistant)",
            "Host": parsed.hostname,
        }

        pool: urllib3.HTTPConnectionPool | urllib3.HTTPSConnectionPool
        if parsed.scheme == "https":
            pool = urllib3.HTTPSConnectionPool(
                host=resolved_ip,
                port=port,
                assert_hostname=parsed.hostname,
                server_hostname=parsed.hostname,
                cert_reqs="CERT_REQUIRED",
            )
        else:
            pool = urllib3.HTTPConnectionPool(host=resolved_ip, port=port)

        resp = pool.urlopen(
            method="GET",
            url=path_and_query,
            headers=headers,
            timeout=urllib3.Timeout(connect=5.0, read=15.0),
            redirect=False,
            retries=False,
            assert_same_host=False,
        )
        if 300 <= resp.status < 400:
            return {"error": "Redirects are blocked for security reasons"}
        if resp.status >= 400:
            return {"error": f"Failed to fetch {url}: HTTP {resp.status}"}

        html = resp.data.decode("utf-8", errors="replace")
        soup = BeautifulSoup(html, "html.parser")

        # Remove non-content elements
        for tag in soup(["script", "style", "nav", "header", "footer", "iframe"]):
            tag.decompose()

        title = soup.title.string.strip() if soup.title and soup.title.string else ""
        text = soup.get_text(separator="\n", strip=True)

        # Truncate very long pages
        max_chars = 30_000
        if len(text) > max_chars:
            text = text[:max_chars] + f"\n\n... (truncated, total {len(text)} chars)"

        return {"url": url, "title": title, "content": text}
    except (urllib3.exceptions.HTTPError, ValueError) as e:
        return {"error": f"Failed to fetch {url}: {e}"}
