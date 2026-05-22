"""Tool 2: get_opponents — Gegner eines Teams in der Gruppenphase + ELO-Stärke."""

from __future__ import annotations

import difflib

from data_loader import get_elo_data, get_fixtures, resolve_team


def _find_fixture_name(team: str, fixtures: dict) -> str | None:
    """
    Sucht den exakten Fixture-Namen (wie in fixtures.json) für ein Team.
    Unterstützt deutsche Namen, englische Namen und fuzzy matching.
    """
    all_fixture_names = [
        t for g in fixtures["groups"].values() for t in g["teams"]
    ]

    # 1. Direkte Übereinstimmung (case-insensitive)
    for fn in all_fixture_names:
        if fn.lower() == team.lower():
            return fn

    # 2. Über ELO-Resolver: resolve_team gibt uns den ELO-Eintrag,
    #    dann vergleichen wir Code mit Fixture-Namen via Fuzzy
    elo_entry = resolve_team(team)
    if elo_entry:
        # Suche Fixture-Name der zum ELO-Code passt
        for fn in all_fixture_names:
            fn_elo = resolve_team(fn)
            if fn_elo and fn_elo["code"] == elo_entry["code"]:
                return fn

    # 3. Fuzzy-Match direkt auf Fixture-Namen
    matches = difflib.get_close_matches(team.lower(), [f.lower() for f in all_fixture_names], n=1, cutoff=0.6)
    if matches:
        for fn in all_fixture_names:
            if fn.lower() == matches[0]:
                return fn

    return None


def _find_group(fixture_name: str, fixtures: dict) -> tuple[str, dict] | tuple[None, None]:
    for group_name, info in fixtures["groups"].items():
        if fixture_name in info["teams"]:
            return group_name, info
    return None, None


def _difficulty_label(avg_opponent_elo: float) -> str:
    if avg_opponent_elo >= 1900:
        return "sehr schwer (Top-Gruppe)"
    if avg_opponent_elo >= 1750:
        return "schwer"
    if avg_opponent_elo >= 1600:
        return "mittel"
    return "leicht (schwache Gruppe)"


def run(team: str) -> dict:
    """
    Gibt die Gegner eines Teams in der Gruppenphase zurück,
    inklusive ELO-Rating jedes Gegners und einer Gesamtbewertung der Gruppe.
    """
    fixtures = get_fixtures()
    fixture_name = _find_fixture_name(team, fixtures)
    if not fixture_name:
        return {"error": f"Team '{team}' nicht in der WM-2026-Gruppenphase gefunden."}

    group_name, group_info = _find_group(fixture_name, fixtures)
    if not group_name:
        return {"error": f"Keine Gruppe für '{fixture_name}' gefunden."}

    all_teams = group_info["teams"]
    opponents_data: list[dict] = []

    for opp_name in all_teams:
        if opp_name == fixture_name:
            continue
        opp_elo = resolve_team(opp_name)
        match_date = None
        for m in group_info["matches"]:
            if fixture_name in (m["team1"], m["team2"]) and opp_name in (m["team1"], m["team2"]):
                match_date = m["date"]
                break
        opponents_data.append({
            "name": opp_name,
            "elo": opp_elo["elo"] if opp_elo else None,
            "elo_rank": opp_elo["rank"] if opp_elo else None,
            "match_date": match_date,
        })

    opponents_data.sort(key=lambda x: x["elo"] or 0, reverse=True)
    elos = [o["elo"] for o in opponents_data if o["elo"]]
    avg_elo = round(sum(elos) / len(elos)) if elos else 0
    strongest = opponents_data[0] if opponents_data else None
    my_elo = resolve_team(fixture_name)
    my_elo_val = my_elo["elo"] if my_elo else 0

    summary = (
        f"{fixture_name} spielt in {group_name} gegen: "
        + ", ".join(f"{o['name']} (ELO {o['elo']})" for o in opponents_data)
        + (f". Stärkster Gegner: {strongest['name']} (ELO {strongest['elo']})." if strongest else "")
        + f" Gruppen-Schwierigkeit: {_difficulty_label(avg_elo)}."
    )

    return {
        "team": fixture_name,
        "group": group_name,
        "opponents": opponents_data,
        "avg_opponent_elo": avg_elo,
        "group_difficulty": _difficulty_label(avg_elo),
        "strongest_opponent": strongest,
        "my_elo": my_elo_val,
        "summary": summary,
    }

