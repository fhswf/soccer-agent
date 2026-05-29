"""
clean.py
========
Wandelt strukturierte Daten (ELO, Fixtures, Fun Facts) in lesbare Textstücke
(Chunks) für die Vektordatenbank um.

Kernidee: Strukturierte Daten zuerst in natürlichsprachlichen Fließtext umwandeln,
dann in Chunks aufteilen. So kann die KI die Informationen besser verstehen
und beim Retrieval passende Antworten finden.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field, asdict
from pathlib import Path

import yaml

DATA_DIR = Path(__file__).parent / "data"

# ---------------------------------------------------------------------------
# Datenstruktur für einen einzelnen Chunk
# ---------------------------------------------------------------------------

@dataclass
class Chunk:
    """Ein einzelner Text-Chunk mit Metadaten für die Vektordatenbank."""
    text: str
    source: str               # Lesbare Quellenangabe (erscheint in der UI)
    source_url: str           # URL der Quelle
    data_type: str            # "elo" | "fixture" | "trivia" | "group"
    team: str = ""            # Betroffenes Team (leer = allgemein)
    tournament: str = "WM 2026"
    year: int = 2026
    chunk_id: str = ""        # wird beim Ingest gesetzt


# ---------------------------------------------------------------------------
# 1. ELO-Ratings → Texte
# ---------------------------------------------------------------------------

def elo_to_chunks(elo_data: list[dict]) -> list[Chunk]:
    """Wandelt ELO-Daten in lesbare Chunk-Texte um."""
    chunks: list[Chunk] = []

    # Chunk 1: Gesamtübersicht Top 20
    top20 = elo_data[:20]
    lines = ["Die aktuellen Top-20-Teams der Welt nach ELO-Rating (Stand: Mai 2026):\n"]
    for t in top20:
        change = ""
        if t.get("elo_change_1y") is not None:
            sign = "+" if t["elo_change_1y"] >= 0 else ""
            change = f" (Veränderung letztes Jahr: {sign}{t['elo_change_1y']})"
        lines.append(f"  #{t['rank']:2d}. {t['name']} (Code: {t['code']}) – ELO: {t['elo']}{change}")
    chunks.append(Chunk(
        text="\n".join(lines),
        source="eloratings.net – Weltrangliste Mai 2026",
        source_url="https://eloratings.net/World.tsv",
        data_type="elo",
        team="",
    ))

    # Chunk pro Team (für die WM-2026-Teilnehmer und Top-50-Teams)
    wm_teams_codes = {
        "MX", "ZA", "KR", "CZ", "CA", "BA", "QA", "CH", "BR", "MA", "HT", "SQ",
        "US", "PY", "AU", "TR", "DE", "CW", "CI", "EC", "NL", "JP", "SE", "TN",
        "BE", "EG", "IR", "NZ", "ES", "CV", "SA", "UY", "FR", "SN", "IQ", "NO",
        "AR", "DZ", "AT", "JO", "PT", "CD", "UZ", "CO", "EN", "HR", "GH", "PA",
    }

    for t in elo_data:
        if t["code"] not in wm_teams_codes and t["rank"] > 50:
            continue

        parts = [f"{t['name']} (Kürzel: {t['code']}) bei der WM 2026:\n"]
        parts.append(f"  Aktueller ELO-Wert: {t['elo']} (Weltrang: #{t['rank']})")

        if t.get("elo_1y_ago"):
            diff = (t["elo"] or 0) - t["elo_1y_ago"]
            sign = "+" if diff >= 0 else ""
            parts.append(f"  ELO vor einem Jahr: {t['elo_1y_ago']} (Entwicklung: {sign}{diff} Punkte)")

        if t.get("elo_3y_ago"):
            diff3 = (t["elo"] or 0) - t["elo_3y_ago"]
            sign = "+" if diff3 >= 0 else ""
            parts.append(f"  ELO vor drei Jahren: {t['elo_3y_ago']} (Entwicklung: {sign}{diff3} Punkte)")

        if all(t.get(k) is not None for k in ("wins", "draws", "losses")):
            total = t["wins"] + t["draws"] + t["losses"]
            parts.append(f"  Historische Bilanz: {total} Spiele – {t['wins']}S / {t['draws']}U / {t['losses']}N")

        if t.get("goals_for") is not None and t.get("goals_against") is not None:
            diff = t["goals_for"] - t["goals_against"]
            sign = "+" if diff >= 0 else ""
            parts.append(f"  Tore: {t['goals_for']} geschossen, {t['goals_against']} kassiert (Differenz: {sign}{diff})")

        chunks.append(Chunk(
            text="\n".join(parts),
            source=f"eloratings.net – {t['name']} Profil Mai 2026",
            source_url="https://eloratings.net/World.tsv",
            data_type="elo",
            team=t["name"],
        ))

    return chunks


# ---------------------------------------------------------------------------
# 2. Spielplan/Gruppen → Texte
# ---------------------------------------------------------------------------

def fixtures_to_chunks(fixtures: dict) -> list[Chunk]:
    """Wandelt Spielplan-Daten in lesbare Chunk-Texte um."""
    chunks: list[Chunk] = []

    # Turnier-Überblick
    overview = (
        f"Die {fixtures['tournament']} findet in {', '.join(fixtures['host_countries'])} statt. "
        f"48 Teams spielen in {fixtures['num_groups']} Gruppen à 4 Teams. "
        f"Das Finale ist am {fixtures['final_date']} in {fixtures['final_venue']}. "
        "Die besten 2 jeder Gruppe sowie die 8 besten Dritten (32 Teams total) kommen weiter."
    )
    chunks.append(Chunk(
        text=overview,
        source="openfootball/worldcup.json – Turnier-Überblick WM 2026",
        source_url="https://github.com/openfootball/worldcup.json",
        data_type="fixture",
        team="",
    ))

    # Alle Gruppen zusammen (ein Überblick-Chunk)
    group_lines = ["Gruppen-Einteilung der WM 2026:\n"]
    for group_name, info in fixtures["groups"].items():
        teams_str = " | ".join(info["teams"])
        group_lines.append(f"  {group_name}: {teams_str}")
    chunks.append(Chunk(
        text="\n".join(group_lines),
        source="openfootball/worldcup.json – Gruppenauslosung WM 2026",
        source_url="https://github.com/openfootball/worldcup.json",
        data_type="group",
        team="",
    ))

    # Pro Gruppe: Detailchunk mit Teams und Spielen
    for group_name, info in fixtures["groups"].items():
        teams = info["teams"]
        matches = info["matches"]
        lines = [f"{group_name} der WM 2026:\n  Teams: {', '.join(teams)}\n  Spiele:"]
        for m in matches:
            score = ""
            if m.get("score1") is not None and m.get("score2") is not None:
                score = f" → Ergebnis: {m['score1']}:{m['score2']}"
            lines.append(f"    {m['date']}: {m['team1']} vs. {m['team2']} ({m['venue']}){score}")
        # Auch pro Team in der Gruppe referenzieren
        for team in teams:
            opponent_matches = [
                f"{m['team1']} vs. {m['team2']} am {m['date']}"
                for m in matches if team in (m["team1"], m["team2"])
            ]
            lines.append(f"  {team} spielt gegen: {', '.join(opponent_matches)}")
        chunk = Chunk(
            text="\n".join(lines),
            source=f"openfootball/worldcup.json – {group_name} WM 2026",
            source_url="https://github.com/openfootball/worldcup.json",
            data_type="fixture",
            team=" | ".join(teams),
        )
        chunks.append(chunk)

    return chunks


# ---------------------------------------------------------------------------
# 3. Fun Facts → Texte
# ---------------------------------------------------------------------------

def fun_facts_to_chunks(facts: list[dict]) -> list[Chunk]:
    """Wandelt YAML-Fun-Facts in Chunks um."""
    chunks: list[Chunk] = []
    for fact in facts:
        text = fact.get("text", "").strip()
        text = re.sub(r"\s+", " ", text)  # YAML-Zeilenumbrüche bereinigen
        chunks.append(Chunk(
            text=text,
            source=f"WM-2026-Wissensbank – {fact.get('id', 'unbekannt')}",
            source_url="lokal",
            data_type="trivia",
            team=fact.get("team", ""),
        ))
    return chunks


# ---------------------------------------------------------------------------
# 4. Offizielle News → Texte
# ---------------------------------------------------------------------------

def official_news_to_chunks(news_list: list[dict]) -> list[Chunk]:
    """Wandelt gescrapete FIFA-News in Chunks um."""
    chunks: list[Chunk] = []
    for item in news_list:
        text = f"Offizielle Ankündigung/News zur WM 2026:\n{item['title']}\n\nDetails: {item['snippet']}"
        chunks.append(Chunk(
            text=text,
            source=f"{item['source']} – {item['title']}",
            source_url=item['url'],
            data_type="trivia",  # Passt gut in die bestehende Struktur
            team="",
        ))
    return chunks


# ---------------------------------------------------------------------------
# Haupt-Funktion: Alles zusammenführen
# ---------------------------------------------------------------------------

def build_chunks() -> list[dict]:
    """
    Liest alle Datenquellen aus data/ und gibt eine Liste von Chunk-Dicts zurück,
    bereit zum Einbetten und Einspeichern.
    """
    all_chunks: list[Chunk] = []

    # ELO
    elo_path = DATA_DIR / "elo_ratings.json"
    if elo_path.exists():
        with open(elo_path, encoding="utf-8") as f:
            elo_data = json.load(f)
        elo_chunks = elo_to_chunks(elo_data)
        all_chunks.extend(elo_chunks)
        print(f"ELO-Chunks: {len(elo_chunks)}")
    else:
        print("WARNUNG: elo_ratings.json nicht gefunden – erst fetch_elo.py ausführen!")

    # Fixtures
    fixtures_path = DATA_DIR / "fixtures.json"
    if fixtures_path.exists():
        with open(fixtures_path, encoding="utf-8") as f:
            fixtures = json.load(f)
        fix_chunks = fixtures_to_chunks(fixtures)
        all_chunks.extend(fix_chunks)
        print(f"Fixture-Chunks: {len(fix_chunks)}")
    else:
        print("WARNUNG: fixtures.json nicht gefunden – erst fetch_fixtures.py ausführen!")

    # Fun Facts
    facts_path = DATA_DIR / "fun_facts.yaml"
    if facts_path.exists():
        with open(facts_path, encoding="utf-8") as f:
            facts_data = yaml.safe_load(f)
        fact_chunks = fun_facts_to_chunks(facts_data.get("facts", []))
        all_chunks.extend(fact_chunks)
        print(f"Fun-Facts-Chunks: {len(fact_chunks)}")
    else:
        print("WARNUNG: fun_facts.yaml nicht gefunden!")

    # Official News
    news_path = DATA_DIR / "official_news.json"
    if news_path.exists():
        try:
            with open(news_path, encoding="utf-8") as f:
                news_data = json.load(f)
            news_chunks = official_news_to_chunks(news_data)
            all_chunks.extend(news_chunks)
            print(f"Official News Chunks: {len(news_chunks)}")
        except Exception as e:
            print(f"WARNUNG: Fehler beim Laden von official_news.json: {e}")
    else:
        print("Official News: official_news.json nicht gefunden – übersprungen.")


    # Chunk-IDs vergeben
    import hashlib
    chunk_dicts = []
    for chunk in all_chunks:
        d = asdict(chunk)
        content_to_hash = f"{chunk.text}||{chunk.source}||{chunk.source_url}"
        h = hashlib.sha256(content_to_hash.encode("utf-8")).hexdigest()
        d["chunk_id"] = f"wm2026_{h}"
        chunk_dicts.append(d)

    # Speichern für Debug/Inspektion
    out_path = DATA_DIR / "chunks.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(chunk_dicts, f, ensure_ascii=False, indent=2)

    print(f"\nGesamt: {len(chunk_dicts)} Chunks → {out_path}")
    return chunk_dicts


if __name__ == "__main__":
    chunks = build_chunks()
    # Beispiel-Chunk ausgeben
    print("\n--- Beispiel-Chunk #0 ---")
    print(chunks[0]["text"][:500])
    print("...")
    print(f"Quelle: {chunks[0]['source']}")
