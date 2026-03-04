"""Web search and URL fetching tools."""

import os

import requests
from bs4 import BeautifulSoup


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

    return {"error": "No search API configured. Set GOOGLE_CSE_API_KEY+GOOGLE_CSE_ID or SERPAPI_API_KEY in .env"}


def _search_google_cse(query: str, num: int, api_key: str, cse_id: str) -> dict:
    try:
        resp = requests.get(
            "https://www.googleapis.com/customsearch/v1",
            params={"key": api_key, "cx": cse_id, "q": query, "num": num},
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()
        results = [
            {"title": item["title"], "url": item["link"], "snippet": item.get("snippet", "")}
            for item in data.get("items", [])
        ]
        return {"query": query, "results": results}
    except Exception as e:
        return {"error": f"Google CSE search failed: {e}"}


def _search_serpapi(query: str, num: int, api_key: str) -> dict:
    try:
        resp = requests.get(
            "https://serpapi.com/search",
            params={"api_key": api_key, "q": query, "num": num, "engine": "google"},
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()
        results = [
            {"title": r["title"], "url": r["link"], "snippet": r.get("snippet", "")}
            for r in data.get("organic_results", [])
        ]
        return {"query": query, "results": results}
    except Exception as e:
        return {"error": f"SerpAPI search failed: {e}"}


def fetch_url(url: str) -> dict:
    """Fetch a web page and extract its readable text content.

    Converts HTML to clean text, stripping scripts, styles, and navigation.

    Args:
        url: The URL to fetch.

    Returns:
        dict with 'title', 'content' (text), and 'url', or 'error'.
    """
    try:
        headers = {"User-Agent": "GCPClaw/1.0 (personal AI assistant)"}
        resp = requests.get(url, headers=headers, timeout=15)
        resp.raise_for_status()

        soup = BeautifulSoup(resp.text, "html.parser")

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
    except Exception as e:
        return {"error": f"Failed to fetch {url}: {e}"}
