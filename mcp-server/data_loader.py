"""
data_loader.py — Zentraler Datenlader für den MCP-Server
=========================================================
Lädt fixtures.json und elo_ratings.json einmalig beim Serverstart
und stellt sie als Singleton-Objekte bereit. Enthält außerdem
Hilfsfunktionen zur Team-Namensauflösung (fuzzy matching).
"""

from __future__ import annotations

import difflib
import json
from functools import lru_cache
from pathlib import Path

# Pfad zu den Datendateien (relativ zum Repo-Root oder via Env)
import os

_DATA_DIR = Path(os.environ.get("DATA_DIR", Path(__file__).parent.parent / "data-pipeline" / "data"))


# ---------------------------------------------------------------------------
# Laden der Rohdaten (einmalig beim Import, gecacht)
# ---------------------------------------------------------------------------

@lru_cache(maxsize=1)
def get_elo_data() -> list[dict]:
    """Gibt die ELO-Ratings aller Teams zurück (sortiert nach Rang)."""
    path = _DATA_DIR / "elo_ratings.json"
    if not path.exists():
        raise FileNotFoundError(
            f"elo_ratings.json nicht gefunden unter {path}. "
            "Bitte erst 'uv run wm fetch && uv run wm clean' ausführen."
        )
    return json.loads(path.read_text(encoding="utf-8"))


@lru_cache(maxsize=1)
def get_fixtures() -> dict:
    """Gibt den vollständigen Spielplan zurück."""
    path = _DATA_DIR / "fixtures.json"
    if not path.exists():
        raise FileNotFoundError(
            f"fixtures.json nicht gefunden unter {path}. "
            "Bitte erst 'uv run wm fetch' ausführen."
        )
    return json.loads(path.read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------
# Team-Index-Aufbau (deutsch ↔ englisch ↔ Code)
# ---------------------------------------------------------------------------

# Deutsch → Englisch (Klarnamen wie im Datensatz)
_DE_TO_EN: dict[str, str] = {
    "deutschland": "Germany",
    "spanien": "Spain",
    "frankreich": "France",
    "england": "England",
    "brasilien": "Brazil",
    "portugal": "Portugal",
    "kolumbien": "Colombia",
    "niederlande": "Netherlands",
    "ecuador": "Ecuador",
    "kroatien": "Croatia",
    "norwegen": "Norway",
    "japan": "Japan",
    "türkei": "Turkey",
    "tuerkei": "Turkey",
    "uruguay": "Uruguay",
    "schweiz": "Switzerland",
    "senegal": "Senegal",
    "dänemark": "Denmark",
    "daenemark": "Denmark",
    "belgien": "Belgium",
    "mexiko": "Mexico",
    "italien": "Italy",
    "paraguay": "Paraguay",
    "österreich": "Austria",
    "oesterreich": "Austria",
    "marokko": "Morocco",
    "kanada": "Canada",
    "australien": "Australia",
    "serbien": "Serbia",
    "ukraine": "Ukraine",
    "iran": "Iran",
    "südkorea": "South Korea",
    "suedkorea": "South Korea",
    "nigeria": "Nigeria",
    "griechenland": "Greece",
    "algerien": "Algeria",
    "panama": "Panama",
    "argentinien": "Argentina",
    "usa": "USA",
    "schweden": "Sweden",
    "chile": "Chile",
    "ungarn": "Hungary",
    "wales": "Wales",
    "peru": "Peru",
    "slowenien": "Slovenia",
    "irland": "Ireland",
    "jordanien": "Jordan",
    "ägypten": "Egypt",
    "aegypten": "Egypt",
    "elfenbeinküste": "Ivory Coast",
    "elfenbeinkueste": "Ivory Coast",
    "slowakei": "Slovakia",
    "dr kongo": "DR Congo",
    "georgien": "Georgia",
    "albanien": "Albania",
    "bolivien": "Bolivia",
    "tunesien": "Tunisia",
    "rumänien": "Romania",
    "rumaenien": "Romania",
    "costa rica": "Costa Rica",
    "kamerun": "Cameroon",
    "irak": "Iraq",
    "mali": "Mali",
    "bosnien": "Bosnia & Herzegovina",
    "bosnien & herzegowina": "Bosnia & Herzegovina",
    "neuseeland": "New Zealand",
    "honduras": "Honduras",
    "island": "Iceland",
    "saudi-arabien": "Saudi Arabia",
    "kap verde": "Cape Verde",
    "ghana": "Ghana",
    "katar": "Qatar",
    "china": "China",
    "haiti": "Haiti",
    "schottland": "Scotland",
    "südafrika": "South Africa",
    "suedafrika": "South Africa",
    "tschechien": "Czech Republic",
    "curaçao": "Curaçao",
    "curacao": "Curaçao",
    "usbekistan": "Uzbekistan",
}

# ELO-Code → Team-Name (wie im Datensatz)
_CODE_TO_NAME: dict[str, str] = {}

# Englischer Name (lower) → ELO-Dict
_NAME_TO_ELO: dict[str, dict] = {}

# Team-Name (wie in fixtures.json) → ELO-Dict
_FIXTURE_NAME_TO_ELO: dict[str, dict] = {}

# Fixtures: Englischer Name → Gruppe
_TEAM_TO_GROUP: dict[str, str] = {}


def _build_indexes() -> None:
    """Baut alle Lookup-Indizes auf (einmalig)."""
    global _CODE_TO_NAME, _NAME_TO_ELO, _FIXTURE_NAME_TO_ELO, _TEAM_TO_GROUP

    for team in get_elo_data():
        _CODE_TO_NAME[team["code"].upper()] = team["name"]
        # Deutschen Namen indexieren (wie er in elo_ratings.json steht)
        _NAME_TO_ELO[team["name"].lower()] = team
        # 2-Buchstaben-Code indexieren
        _NAME_TO_ELO[team["code"].lower()] = team

    # Aus _DE_TO_EN: englische Zielnamen → selben ELO-Eintrag
    # (damit "Germany" → findet den Eintrag mit name="Deutschland")
    for de_key, en_name in _DE_TO_EN.items():
        en_lower = en_name.lower()
        # Finde den ELO-Eintrag via deutschen Key
        if de_key in _NAME_TO_ELO:
            _NAME_TO_ELO[en_lower] = _NAME_TO_ELO[de_key]
        elif en_lower not in _NAME_TO_ELO:
            # Fuzzy-Fallback: suche über den deutschen Namen
            entry = _resolve_elo_by_fuzzy(de_key)
            if entry:
                _NAME_TO_ELO[en_lower] = entry

    fixtures = get_fixtures()
    for group_name, info in fixtures.get("groups", {}).items():
        for team_name in info.get("teams", []):
            _TEAM_TO_GROUP[team_name.lower()] = group_name
            elo = _resolve_elo_by_fuzzy(team_name)
            if elo:
                _FIXTURE_NAME_TO_ELO[team_name.lower()] = elo



def _resolve_elo_by_fuzzy(name: str) -> dict | None:
    """Fuzzy-Match eines Team-Namens auf die ELO-Daten."""
    if not _NAME_TO_ELO:
        # Direkt aus Daten aufbauen ohne Index
        for team in get_elo_data():
            _NAME_TO_ELO[team["name"].lower()] = team

    key = name.lower().strip()
    if key in _NAME_TO_ELO:
        return _NAME_TO_ELO[key]

    # difflib fuzzy match
    candidates = list(_NAME_TO_ELO.keys())
    matches = difflib.get_close_matches(key, candidates, n=1, cutoff=0.6)
    if matches:
        return _NAME_TO_ELO[matches[0]]
    return None


def resolve_team(name: str) -> dict | None:
    """
    Löst einen Teamnamen (DE, EN oder Code) in ein ELO-Dict auf.

    Unterstützt:
    - Deutsche Namen: "Deutschland", "Österreich"
    - Englische Namen: "Germany", "Ecuador"
    - 2-Buchstaben-Codes: "DE", "ES"
    - Teilnamen: "Kongo" → "DR Congo"
    - Fuzzy: "Deutschlan" → "Deutschland" → "Germany"
    """
    if not name:
        return None

    # Indizes sicherstellen
    if not _NAME_TO_ELO:
        _build_indexes()

    key = name.strip().lower()

    # 1. Direkter DE-Lookup
    if key in _DE_TO_EN:
        en = _DE_TO_EN[key].lower()
        if en in _NAME_TO_ELO:
            return _NAME_TO_ELO[en]

    # 2. Direkter EN-Lookup
    if key in _NAME_TO_ELO:
        return _NAME_TO_ELO[key]

    # 3. Code-Lookup (z.B. "DE", "ES")
    upper = name.strip().upper()
    if upper in _CODE_TO_NAME:
        en = _CODE_TO_NAME[upper].lower()
        return _NAME_TO_ELO.get(en)

    # 4. Fuzzy-Match über DE-Wörterbuch
    de_candidates = list(_DE_TO_EN.keys())
    de_matches = difflib.get_close_matches(key, de_candidates, n=1, cutoff=0.7)
    if de_matches:
        en = _DE_TO_EN[de_matches[0]].lower()
        if en in _NAME_TO_ELO:
            return _NAME_TO_ELO[en]

    # 5. Fuzzy-Match direkt auf ELO-Namen
    return _resolve_elo_by_fuzzy(name)


def resolve_team_fixture_name(name: str) -> str | None:
    """
    Gibt den exakten Namen zurück, wie er in fixtures.json steht
    (z.B. "Germany" → "Germany", "Deutschland" → "Germany").
    """
    team = resolve_team(name)
    if not team:
        return None

    # Suche fixture-Namen der zu diesem ELO-Eintrag passt
    fixtures = get_fixtures()
    elo_names_lower = {team["name"].lower(), team["code"].lower()}

    for group_info in fixtures.get("groups", {}).values():
        for t in group_info.get("teams", []):
            # Direkte Übereinstimmung oder fuzzy
            resolved = resolve_team(t)
            if resolved and resolved["code"] == team["code"]:
                return t
    return team["name"]  # Fallback


def get_team_group(team_fixture_name: str) -> str | None:
    """Gibt die Gruppe eines Teams zurück (nach fixture-Namen)."""
    if not _TEAM_TO_GROUP:
        _build_indexes()
    return _TEAM_TO_GROUP.get(team_fixture_name.lower())


# Indizes beim Import aufbauen (lazy — nur wenn Daten vorhanden)
try:
    _build_indexes()
except FileNotFoundError:
    pass  # Wird beim ersten API-Aufruf erneut versucht
