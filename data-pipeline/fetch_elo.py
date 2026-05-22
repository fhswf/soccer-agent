"""
fetch_elo.py
============
Lädt ELO-Ratings von https://eloratings.net/World.tsv und gibt eine
strukturierte Liste von Team-Dictionaries zurück.

Spaltenstruktur (keine Header-Zeile, Tab-getrennt):
  0  Rank
  1  PreviousRank
  2  Code (2-Buchstaben-Ländercode)
  3  Rating (aktuell)
  4  Rank_1y_ago
  5  Rating_1y_ago
  6  Rank_3y_ago
  7  Rating_3y_ago
  8  Rank_5y_ago
  9  Rating_5y_ago
  10 DeltaRank_1m   11 DeltaRating_1m
  12 DeltaRank_3m   13 DeltaRating_3m
  14 DeltaRank_6m   15 DeltaRating_6m
  16 DeltaRank_1y   17 DeltaRating_1y
  18 DeltaRank_2y   19 DeltaRating_2y
  20 DeltaRank_5y   21 DeltaRating_5y
  22 Games_Total  23 Wins  24 Draws  25 Losses
  26 Goals_For_Total  27 Goals_Against_Total  28 ...
"""

from __future__ import annotations

import csv
import urllib.request
from pathlib import Path

# ---------------------------------------------------------------------------
# Ländercodes → vollständige Namen (Auswahl der WM-2026-Teilnehmer + bekannte Teams)
# ---------------------------------------------------------------------------
CODE_TO_NAME: dict[str, str] = {
    "ES": "Spanien",
    "AR": "Argentinien",
    "FR": "Frankreich",
    "EN": "England",
    "BR": "Brasilien",
    "PT": "Portugal",
    "CO": "Kolumbien",
    "NL": "Niederlande",
    "EC": "Ecuador",
    "HR": "Kroatien",
    "DE": "Deutschland",
    "NO": "Norwegen",
    "JP": "Japan",
    "TR": "Türkei",
    "UY": "Uruguay",
    "CH": "Schweiz",
    "SN": "Senegal",
    "DK": "Dänemark",
    "BE": "Belgien",
    "MX": "Mexiko",
    "IT": "Italien",
    "PY": "Paraguay",
    "AT": "Österreich",
    "MA": "Marokko",
    "CA": "Kanada",
    "AU": "Australien",
    "RU": "Russland",
    "RS": "Serbien",
    "SQ": "Schottland",
    "UA": "Ukraine",
    "IR": "Iran",
    "KR": "Südkorea",
    "NG": "Nigeria",
    "GR": "Griechenland",
    "DZ": "Algerien",
    "PA": "Panama",
    "PL": "Polen",
    "UZ": "Usbekistan",
    "VE": "Venezuela",
    "CZ": "Tschechien",
    "US": "USA",
    "SE": "Schweden",
    "CL": "Chile",
    "HU": "Ungarn",
    "WA": "Wales",
    "PE": "Peru",
    "SI": "Slowenien",
    "IE": "Irland",
    "JO": "Jordanien",
    "EG": "Ägypten",
    "CI": "Elfenbeinküste",
    "SK": "Slowakei",
    "CD": "DR Kongo",
    "GE": "Georgien",
    "AL": "Albanien",
    "BO": "Bolivien",
    "TN": "Tunesien",
    "IL": "Israel",
    "RO": "Rumänien",
    "CR": "Costa Rica",
    "CM": "Kamerun",
    "IQ": "Irak",
    "EI": "Nordirland",
    "ML": "Mali",
    "BA": "Bosnien & Herzegowina",
    "NM": "Nordmazedonien",
    "NZ": "Neuseeland",
    "HN": "Honduras",
    "IS": "Island",
    "SA": "Saudi-Arabien",
    "CV": "Kap Verde",
    "AO": "Angola",
    "FI": "Finnland",
    "AE": "Vereinigte Arabische Emirate",
    "JM": "Jamaika",
    "HT": "Haiti",
    "BF": "Burkina Faso",
    "ZA": "Südafrika",
    "GT": "Guatemala",
    "BY": "Belarus",
    "GH": "Ghana",
    "SY": "Syrien",
    "OM": "Oman",
    "BG": "Bulgarien",
    "GN": "Guinea",
    "QA": "Katar",
    "CN": "China",
    "KW": "Kuwait",
    "CW": "Curaçao",
    "LU": "Luxemburg",
    "SR": "Suriname",
    "KZ": "Kasachstan",
    "EE": "Estland",
    "BJ": "Benin",
    "TT": "Trinidad & Tobago",
}

ELO_URL = "https://eloratings.net/World.tsv"
DATA_DIR = Path(__file__).parent / "data"


def _parse_int(val: str) -> int | None:
    """Parst einen Integer; gibt None zurück bei '−' (Minuszeichen als Dash)."""
    cleaned = val.strip().replace("\u2212", "-").replace("−", "-")
    try:
        return int(cleaned)
    except ValueError:
        return None


def fetch_elo(use_cached: bool = True) -> list[dict]:
    """
    Lädt die ELO-Tabelle und gibt eine Liste von Team-Dictionaries zurück.

    Parameters
    ----------
    use_cached : bool
        Wenn True und data/World.tsv existiert, wird die lokale Datei genutzt.
        Wenn False, wird die Datei von eloratings.net neu heruntergeladen.

    Returns
    -------
    list[dict]  Sortiert nach aktuellem ELO-Rang.
    """
    tsv_path = DATA_DIR / "World.tsv"

    if not use_cached or not tsv_path.exists():
        print(f"Lade ELO-Daten von {ELO_URL} …")
        urllib.request.urlretrieve(ELO_URL, tsv_path)
        print(f"  → gespeichert: {tsv_path}")
    else:
        print(f"Nutze gecachte ELO-Daten: {tsv_path}")

    teams: list[dict] = []
    seen_codes: set[str] = set()

    with open(tsv_path, encoding="utf-8") as f:
        reader = csv.reader(f, delimiter="\t")
        for row in reader:
            if len(row) < 10:
                continue
            code = row[2].strip()
            if code in seen_codes:
                # Bei gleichem Rang (z.B. Zeile 5 und 6 haben beide Rang 5)
                # nehmen wir nur den ersten Eintrag
                continue
            seen_codes.add(code)

            rank = _parse_int(row[0])
            rating = _parse_int(row[3])
            rating_1y = _parse_int(row[5]) if len(row) > 5 else None
            rating_3y = _parse_int(row[7]) if len(row) > 7 else None
            delta_rating_1y = _parse_int(row[17]) if len(row) > 17 else None
            wins = _parse_int(row[23]) if len(row) > 23 else None
            draws = _parse_int(row[24]) if len(row) > 24 else None
            losses = _parse_int(row[25]) if len(row) > 25 else None
            goals_for = _parse_int(row[26]) if len(row) > 26 else None
            goals_against = _parse_int(row[27]) if len(row) > 27 else None

            name = CODE_TO_NAME.get(code, code)

            teams.append({
                "rank": rank,
                "code": code,
                "name": name,
                "elo": rating,
                "elo_1y_ago": rating_1y,
                "elo_3y_ago": rating_3y,
                "elo_change_1y": delta_rating_1y,
                "wins": wins,
                "draws": draws,
                "losses": losses,
                "goals_for": goals_for,
                "goals_against": goals_against,
            })

    print(f"  → {len(teams)} Teams geladen.")
    return teams


if __name__ == "__main__":
    import json

    teams = fetch_elo(use_cached=True)
    out_path = DATA_DIR / "elo_ratings.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(teams, f, ensure_ascii=False, indent=2)
    print(f"\nTop 10 Teams:")
    for t in teams[:10]:
        print(f"  #{t['rank']:3d}  {t['name']:20s}  ELO: {t['elo']}")
    print(f"\nGespeichert: {out_path}")
