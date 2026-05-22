"""Tool 1: get_matches — Spiele eines Teams oder einer Gruppe."""

from __future__ import annotations
from data_loader import get_fixtures, resolve_team_fixture_name


def run(
    team: str | None = None,
    group: str | None = None,
    round_filter: str | None = None,
) -> dict:
    """
    Gibt alle Spiele eines Teams oder einer Gruppe zurück.
    Mindestens team oder group muss angegeben sein.
    """
    if not team and not group:
        return {"error": "Bitte 'team' oder 'group' angeben."}

    fixtures = get_fixtures()

    # Gruppe normalisieren (z.B. "E" → "Group E")
    if group:
        g = group.strip()
        if len(g) == 1 and g.upper().isalpha():
            g = f"Group {g.upper()}"
        elif not g.startswith("Group"):
            g = f"Group {g}"
        group = g

    matches_found: list[dict] = []

    # Fixture-Name des Teams ermitteln
    fixture_name: str | None = None
    if team:
        fixture_name = resolve_team_fixture_name(team)
        if not fixture_name:
            return {"error": f"Team '{team}' nicht gefunden."}

    # Gruppenphase durchsuchen
    for group_name, info in fixtures.get("groups", {}).items():
        if group and group_name != group:
            continue
        for match in info.get("matches", []):
            if fixture_name and fixture_name not in (match["team1"], match["team2"]):
                continue
            if round_filter and match.get("round", "") != round_filter:
                continue
            matches_found.append(match)

    # K.o.-Phase
    if not group:
        for match in fixtures.get("knockout", []):
            if fixture_name:
                t1 = match.get("team1", "")
                t2 = match.get("team2", "")
                if fixture_name not in (t1, t2):
                    continue
            if round_filter and match.get("round", "") != round_filter:
                continue
            matches_found.append(match)

    label = fixture_name or group or "alle Teams"
    return {
        "query": label,
        "matches": matches_found,
        "total": len(matches_found),
    }
