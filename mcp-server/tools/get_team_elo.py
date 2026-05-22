"""Tool 4: get_team_elo — ELO-Rating und Statistiken eines Teams."""

from __future__ import annotations
from data_loader import resolve_team


def run(team: str) -> dict:
    """
    Gibt ELO-Rating, Weltrang, historische Entwicklung und
    eine lesbare Zusammenfassung für ein Team zurück.
    """
    entry = resolve_team(team)
    if not entry:
        return {"error": f"Team '{team}' nicht gefunden. Bitte einen anderen Namen versuchen."}

    elo = entry["elo"] or 0
    elo_1y = entry.get("elo_1y_ago")
    elo_3y = entry.get("elo_3y_ago")
    change_1y = entry.get("elo_change_1y")

    # Trend bestimmen
    if change_1y is None:
        trend_1y = "unbekannt"
    elif change_1y >= 50:
        trend_1y = "stark steigend ⬆️"
    elif change_1y >= 10:
        trend_1y = "steigend ↗️"
    elif change_1y >= -10:
        trend_1y = "stabil →"
    elif change_1y >= -50:
        trend_1y = "sinkend ↘️"
    else:
        trend_1y = "stark sinkend ⬇️"

    wins = entry.get("wins", 0) or 0
    draws = entry.get("draws", 0) or 0
    losses = entry.get("losses", 0) or 0
    total = wins + draws + losses
    goals_for = entry.get("goals_for", 0) or 0
    goals_against = entry.get("goals_against", 0) or 0

    win_rate = round(wins / total * 100, 1) if total > 0 else 0.0

    # Zusammenfassung auf Deutsch
    summary_parts = [
        f"{entry['name']} belegt aktuell Weltrang #{entry['rank']} "
        f"mit einem ELO-Wert von {elo}."
    ]
    if change_1y is not None:
        sign = "+" if change_1y >= 0 else ""
        summary_parts.append(
            f"In den letzten 12 Monaten hat sich das Rating um {sign}{change_1y} Punkte verändert ({trend_1y})."
        )
    if total > 0:
        summary_parts.append(
            f"Historische Bilanz: {total} Spiele, {wins} Siege ({win_rate}% Gewinnquote), "
            f"{draws} Unentschieden, {losses} Niederlagen."
        )

    result = {
        "name": entry["name"],
        "code": entry["code"],
        "elo": elo,
        "rank": entry["rank"],
        "elo_1y_ago": elo_1y,
        "elo_3y_ago": elo_3y,
        "elo_change_1y": change_1y,
        "trend_1y": trend_1y,
        "wins": wins,
        "draws": draws,
        "losses": losses,
        "total_games": total,
        "goals_for": goals_for,
        "goals_against": goals_against,
        "goals_diff": goals_for - goals_against,
        "win_rate_pct": win_rate,
        "summary": " ".join(summary_parts),
    }
    return result
