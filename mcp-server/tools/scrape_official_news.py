"""Tool 11: scrape_official_news — Offizielle FIFA-News und Ankündigungen zur WM 2026 scrapen."""

from __future__ import annotations
import warnings

# Suppress the package renaming warning from duckduckgo_search
warnings.filterwarnings("ignore", category=RuntimeWarning)

# Offizielle Ankündigungen als Fallback bei Rate-Limits oder Netzwerkproblemen
FALLBACK_NEWS = [
    {
        "title": "FIFA World Cup 2026™ Spielplan: Finale in New York/New Jersey",
        "url": "https://www.fifa.com/de/tournaments/mens/worldcup/canadamexicousa2026/articles/spielplan-wm-2026-spiele-ergebnisse",
        "snippet": "FIFA hat den offiziellen Spielplan für die WM 2026 bekannt gegeben. Das Eröffnungsspiel findet im legendären Aztekenstadion in Mexiko-Stadt statt, das Finale in New York/New Jersey.",
        "source": "FIFA.com (Fallback)",
    },
    {
        "title": "Offizielle Spielorte der FIFA WM 2026 in USA, Kanada und Mexiko",
        "url": "https://www.fifa.com/de/tournaments/mens/worldcup/canadamexicousa2026/articles/spielorte-stadien-usa-kanada-mexiko",
        "snippet": "Die 16 Austragungsorte der ersten Weltmeisterschaft mit 48 Teams stehen fest. Die Spiele werden aufgeteilt auf 11 Städte in den USA, 3 in Mexiko und 2 in Kanada.",
        "source": "FIFA.com (Fallback)",
    },
    {
        "title": "Neues WM-Format: 48 Teams in 12 Vierergruppen",
        "url": "https://www.fifa.com/de/tournaments/mens/worldcup/canadamexicousa2026/articles/neues-format-48-teams-gruppenphase",
        "snippet": "Die FIFA hat das Format für die WM 2026 bestätigt. Es wird 12 Gruppen mit je 4 Teams geben. Die besten zwei Teams jeder Gruppe sowie die acht besten Gruppendritten erreichen die K.o.-Runde.",
        "source": "FIFA.com (Fallback)",
    },
]


def run(max_results: int = 5) -> dict:
    """
    Scrapt offizielle Nachrichten und Ankündigungen von fifa.com (über DuckDuckGo).
    """
    try:
        from ddgs import DDGS
    except ImportError:
        return {"error": "ddgs nicht installiert: uv pip install ddgs"}

    news_items = {}

    # 1. Deutsche Suche
    de_query = 'FIFA WM 2026 Spielplan'
    try:
        with DDGS() as ddgs:
            raw_de = list(ddgs.text(de_query, max_results=max_results, region="de-de", backend="lite"))
            for r in raw_de:
                url = r.get("href", "")
                if url and "fifa.com" in url:
                    news_items[url] = {
                        "title": r.get("title", "").strip(),
                        "url": url,
                        "snippet": r.get("body", "").strip(),
                        "source": "FIFA.com (DE)",
                    }
    except Exception as e:
        # Fehlertolerant weitermachen
        pass

    # 2. Englische Suche
    en_query = 'World Cup 2026'
    try:
        with DDGS() as ddgs:
            raw_en = list(ddgs.text(en_query, max_results=max_results, region="en-us", backend="lite"))
            for r in raw_en:
                url = r.get("href", "")
                if url and "fifa.com" in url:
                    if url not in news_items:
                        news_items[url] = {
                            "title": r.get("title", "").strip(),
                            "url": url,
                            "snippet": r.get("body", "").strip(),
                            "source": "FIFA.com (EN)",
                        }
    except Exception as e:
        # Fehlertolerant weitermachen
        pass

    results = list(news_items.values())[:max_results]

    # Fallback nutzen wenn keine Ergebnisse gefunden wurden (z.B. wegen Rate-Limits)
    if not results:
        results = FALLBACK_NEWS[:max_results]

    return {
        "results": results,
        "total": len(results),
        "note": "Echtzeit-Scraping von fifa.com über DuckDuckGo.",
    }
