"""Tool 10: search_news — Aktuelle WM-Nachrichten via DuckDuckGo."""

from __future__ import annotations


def run(query: str, max_results: int = 5) -> dict:
    """
    Sucht aktuelle WM-2026-Nachrichten über DuckDuckGo (kein API-Key nötig).
    """
    try:
        from duckduckgo_search import DDGS
    except ImportError:
        return {"error": "duckduckgo-search nicht installiert: uv pip install duckduckgo-search"}

    # WM-Kontext zum Query hinzufügen falls nicht enthalten
    enriched_query = query
    if "wm" not in query.lower() and "world cup" not in query.lower() and "2026" not in query:
        enriched_query = f"{query} WM 2026"

    try:
        with DDGS() as ddgs:
            raw = list(ddgs.text(enriched_query, max_results=max_results, region="de-de"))
    except Exception as e:
        return {"error": f"Websuche fehlgeschlagen: {e}"}

    results = [
        {
            "title": r.get("title", ""),
            "url": r.get("href", ""),
            "snippet": r.get("body", ""),
        }
        for r in raw
    ]

    return {
        "query": enriched_query,
        "results": results,
        "total": len(results),
        "note": "Websuche via DuckDuckGo – Ergebnisse können variieren.",
    }
