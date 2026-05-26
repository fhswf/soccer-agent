"""Tool 10: search_news — Aktuelle WM-Nachrichten via DuckDuckGo."""

from __future__ import annotations
import re
import warnings


def run(query: str, max_results: int = 5) -> dict:
    """
    Sucht aktuelle WM-2026-Nachrichten über DuckDuckGo (kein API-Key nötig).
    """
    try:
        from ddgs import DDGS
    except ImportError:
        return {"error": "ddgs nicht installiert: uv pip install ddgs"}

    # Länderliste aus data_loader abrufen oder Fallback nutzen
    try:
        from data_loader import get_elo_data, _DE_TO_EN
        countries = set()
        for de_name in _DE_TO_EN.keys():
            countries.add(de_name.lower())
        for en_name in _DE_TO_EN.values():
            countries.add(en_name.lower())
        for team in get_elo_data():
            countries.add(team["name"].lower())
    except Exception:
        # Fallback-Länderliste
        countries = {
            "deutschland", "germany", "spanien", "spain", "frankreich", "france",
            "england", "brasilien", "brazil", "portugal", "niederlande", "netherlands",
            "kroatien", "croatia", "japan", "türkei", "turkey", "uruguay", "schweiz",
            "switzerland", "senegal", "dänemark", "denmark", "belgien", "belgium",
            "mexiko", "mexico", "italien", "italy", "österreich", "austria", "marokko",
            "morocco", "kanada", "canada", "australien", "australia", "serbien", "serbia",
            "ukraine", "iran", "südkorea", "south korea", "nigeria", "griechenland", "greece",
            "argentinien", "argentina", "usa", "schweden", "sweden", "chile", "peru",
            "ecuador", "polen", "poland", "saudi-arabien", "saudi arabia", "katar", "qatar"
        }

    # Überprüfen, ob ein Land im Query vorkommt
    query_lower = query.lower()
    country_mentioned = False
    for country in countries:
        if len(country) <= 2:
            # 2-Buchstaben-Codes nur für bekannte/häufige Länder-Kürzel prüfen (Vermeidung von False Positives)
            if country in {"us", "uk", "de", "fr", "es", "it", "nl", "br", "ar", "mx", "ca"}:
                pattern = rf"\b{re.escape(country)}\b"
                if re.search(pattern, query_lower):
                    country_mentioned = True
                    break
        else:
            pattern = rf"\b{re.escape(country)}\b"
            if re.search(pattern, query_lower):
                country_mentioned = True
                break

    # Fußball-spezifische Begriffe
    soccer_keywords = {
        "fussball", "fußball", "soccer", "football", "nationalmannschaft",
        "nationalteam", "kader", "aufstellung", "spiel", "spiele", "match",
        "tore", "trainer", "wm", "world cup"
    }

    # Wenn ein Land erwähnt wird, aber kein Fußballbezug da ist, "Fußball" anhängen
    if country_mentioned:
        has_soccer_keyword = any(kw in query_lower for kw in soccer_keywords)
        if not has_soccer_keyword:
            query = f"{query} Fußball"

    # WM-Kontext zum Query hinzufügen falls nicht enthalten
    enriched_query = query
    if "wm" not in query.lower() and "world cup" not in query.lower() and "2026" not in query:
        enriched_query = f"{query} WM 2026"

    try:
        with DDGS() as ddgs:
            # Versuche erst backend="lite", da der Standard-Endpunkt im Container/Sandbox oft blockiert/leer ist
            raw = list(ddgs.text(enriched_query, max_results=max_results, region="de-de", backend="lite"))
            if not raw:
                # Fallback auf Standard-Verhalten
                raw = list(ddgs.text(enriched_query, max_results=max_results, region="de-de"))
    except Exception as e:
        # Fallback auf Standard-Verhalten bei Fehlern
        try:
            with DDGS() as ddgs:
                raw = list(ddgs.text(enriched_query, max_results=max_results, region="de-de"))
        except Exception as e2:
            return {"error": f"Websuche fehlgeschlagen: {e2}"}

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

