#!/usr/bin/env python3
"""
scrape_news.py
==============
Scrapt offizielle Nachrichten und Ankündigungen zur FIFA Fussball-Weltmeisterschaft 2026™
von der offiziellen Website (fifa.com) über DuckDuckGo-Suchanfragen.

Speichert die Ergebnisse als JSON in data-pipeline/data/official_news.json.
"""

from __future__ import annotations
import warnings

# Suppress the package renaming warning from duckduckgo_search
warnings.filterwarnings("ignore", category=RuntimeWarning)

import argparse
import json
import os
import sys
from pathlib import Path
import yaml

from rich.console import Console
from rich.table import Table

console = Console()
DATA_DIR = Path(__file__).parent / "data"

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


def scrape_fifa_news(max_results: int = 50) -> list[dict]:
    """
    Sucht aktuelle Nachrichten und Ankündigungen auf fifa.com und bekannten deutschen
    Fußballportalen über DuckDuckGo.
    Kombiniert offizielle FIFA-Meldungen und deutsche Fußball-News.
    """
    try:
        from ddgs import DDGS
    except ImportError:
        console.print("[bold red]Fehler: ddgs ist nicht installiert.[/bold red]")
        console.print("Bitte installieren mit: uv pip install ddgs")
        sys.exit(1)

    news_items = {}

    # 1. Deutsche FIFA-Suche (nutzt backend="lite")
    de_query = 'FIFA WM 2026 Spielplan'
    console.print(f"Suche offizielle FIFA-News auf Deutsch: [cyan]{de_query}[/cyan]")
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
        console.print(f"[yellow]Warnung: Deutsche Websuche fehlgeschlagen: {e}[/yellow]")

    # 2. Deutsche Fußball-News (geladen aus soccer_domains.yaml)
    yaml_path = DATA_DIR / "soccer_domains.yaml"
    soccer_domains = {}
    if yaml_path.exists():
        try:
            with open(yaml_path, encoding="utf-8") as f:
                config = yaml.safe_load(f) or {}
                soccer_domains = config.get("soccer_domains", {})
        except Exception as e:
            console.print(f"[yellow]Warnung: soccer_domains.yaml konnte nicht geladen werden: {e}[/yellow]")
    
    if not soccer_domains:
        # Fallback falls Laden fehlschlägt
        soccer_domains = {
            "kicker.de": "Kicker (DE)",
            "transfermarkt.de": "Transfermarkt (DE)",
            "spox.com": "Spox (DE)",
            "sport1.de": "Sport1 (DE)",
            "weltfussball.de": "Weltfussball (DE)",
        }
    
    site_conditions = " OR ".join(f"site:{domain}" for domain in soccer_domains.keys())
    soccer_query = f"WM 2026 ({site_conditions})"
    console.print(f"Suche deutsche Fußballportale: [cyan]{soccer_query}[/cyan]")
    try:
        with DDGS() as ddgs:
            raw_soccer = list(ddgs.text(soccer_query, max_results=max_results, region="de-de", backend="lite"))
            for r in raw_soccer:
                url = r.get("href", "")
                if url:
                    matched_domain = None
                    for domain in soccer_domains:
                        if domain in url:
                            matched_domain = domain
                            break
                    if matched_domain:
                        news_items[url] = {
                            "title": r.get("title", "").strip(),
                            "url": url,
                            "snippet": r.get("body", "").strip(),
                            "source": soccer_domains[matched_domain],
                        }
    except Exception as e:
        console.print(f"[yellow]Warnung: Suche deutsche Fußballportale fehlgeschlagen: {e}[/yellow]")

    # 3. Englische FIFA-Suche
    en_query = 'World Cup 2026'
    console.print(f"Suche offizielle FIFA-News auf Englisch: [cyan]{en_query}[/cyan]")
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
        console.print(f"[yellow]Warnung: Englische Websuche fehlgeschlagen: {e}[/yellow]")

    results = list(news_items.values())[:max_results]
    
    # Fallback nutzen wenn keine Ergebnisse gefunden wurden (z.B. wegen Rate-Limits)
    if not results:
        console.print("[yellow]Keine Live-Ergebnisse von DuckDuckGo erhalten (eventuell Rate-Limit). Nutze offizielle Fallback-Ankündigungen.[/yellow]")
        results = FALLBACK_NEWS[:max_results]

    return results


def main() -> None:
    parser = argparse.ArgumentParser(description="Offizielle FIFA-WM-2026 News und Ankündigungen scrapen")
    try:
        default_max = int(os.environ.get("SCRAPE_MAX_RESULTS", "50"))
    except ValueError:
        default_max = 50
    parser.add_argument("--max-results", type=int, default=default_max, help="Maximale Anzahl der Ergebnisse")
    args = parser.parse_args()

    console.rule("[bold blue]FIFA World Cup 2026 News Scraper")

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    out_path = DATA_DIR / "official_news.json"

    news = scrape_fifa_news(args.max_results)

    # Speichern
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(news, f, ensure_ascii=False, indent=2)

    console.print(f"\n[green]✅ {len(news)} Nachrichten erfolgreich gescrapet und gespeichert in [bold]{out_path}[/bold][/green]\n")

    # Anzeigen als Tabelle
    t = Table(title="Gescrapete offizielle WM-2026 Nachrichten", show_header=True, header_style="bold cyan")
    t.add_column("Quelle", style="dim", width=15)
    t.add_column("Titel", style="bold", width=35)
    t.add_column("Snippet")

    for item in news:
        snippet_short = item["snippet"]
        if len(snippet_short) > 100:
            snippet_short = snippet_short[:97] + "..."
        t.add_row(item["source"], item["title"], snippet_short)

    console.print(t)


if __name__ == "__main__":
    main()

# Trigger release-please to update kustomization.yaml

