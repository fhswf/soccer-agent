"""
fetch_fixtures.py
=================
Lädt den WM-2026-Spielplan von openfootball/worldcup.json (GitHub)
und speichert ihn strukturiert als JSON.

Quelle: https://raw.githubusercontent.com/openfootball/worldcup.json/master/2026/worldcup.json
Lizenz: Public Domain
"""

from __future__ import annotations

import json
import urllib.request
from collections import defaultdict
from pathlib import Path

FIXTURES_URL = (
    "https://raw.githubusercontent.com/openfootball/worldcup.json"
    "/master/2026/worldcup.json"
)
DATA_DIR = Path(__file__).parent / "data"

# Gruppen-Phase-Runden (alle anderen sind K.o.-Runden)
GROUP_ROUNDS = {f"Matchday {i}" for i in range(1, 18)}


def fetch_fixtures(use_cached: bool = True) -> dict:
    """
    Lädt den Spielplan und gibt ein strukturiertes Dictionary zurück:

    {
      "groups": {
        "Group A": {
          "teams": ["Mexico", "South Africa", "South Korea", "Czech Republic"],
          "matches": [{"date": "2026-06-11", "team1": "Mexico", "team2": ...}, ...]
        },
        ...
      },
      "knockout": [
        {"round": "Round of 32", "num": 73, "date": "2026-06-28", ...},
        ...
      ]
    }
    """
    raw_path = DATA_DIR / "worldcup2026_raw.json"
    out_path = DATA_DIR / "fixtures.json"

    if not use_cached or not raw_path.exists():
        print(f"Lade Spielplan von {FIXTURES_URL} …")
        urllib.request.urlretrieve(FIXTURES_URL, raw_path)
        print(f"  → gespeichert: {raw_path}")
    else:
        print(f"Nutze gecachten Spielplan: {raw_path}")

    with open(raw_path, encoding="utf-8") as f:
        raw = json.load(f)

    matches: list[dict] = raw.get("matches", [])

    groups: dict[str, dict] = defaultdict(lambda: {"teams": [], "matches": []})
    knockout: list[dict] = []

    for match in matches:
        round_name: str = match.get("round", "")
        group: str | None = match.get("group")

        entry = {
            "round": round_name,
            "date": match.get("date"),
            "time": match.get("time"),
            "team1": match.get("team1"),
            "team2": match.get("team2"),
            "venue": match.get("ground"),
            "score1": match.get("score1"),
            "score2": match.get("score2"),
        }

        if group:
            entry["group"] = group
            grp = groups[group]
            grp["matches"].append(entry)
            # Teams sammeln (Reihenfolge des ersten Auftretens)
            for team_key in ("team1", "team2"):
                team = match.get(team_key)
                if team and team not in grp["teams"]:
                    grp["teams"].append(team)
        else:
            if match.get("num"):
                entry["num"] = match["num"]
            knockout.append(entry)

    result = {
        "tournament": "FIFA Fußball-Weltmeisterschaft 2026",
        "host_countries": ["USA", "Kanada", "Mexiko"],
        "final_date": "2026-07-19",
        "final_venue": "New York/New Jersey (East Rutherford)",
        "num_teams": 48,
        "num_groups": len(groups),
        "groups": dict(groups),
        "knockout": knockout,
    }

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"  → {len(groups)} Gruppen, {sum(len(g['matches']) for g in groups.values())} Gruppenspiele")
    print(f"  → {len(knockout)} K.o.-Spiele")
    print(f"  → Gespeichert: {out_path}")

    return result


if __name__ == "__main__":
    data = fetch_fixtures(use_cached=True)
    print("\nGruppen-Übersicht:")
    for group_name, info in data["groups"].items():
        teams_str = ", ".join(info["teams"])
        print(f"  {group_name}: {teams_str}")
