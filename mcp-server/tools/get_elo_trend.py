"""Tool 9: get_elo_trend — ELO-Entwicklung eines Teams über Zeit."""

from __future__ import annotations
from data_loader import resolve_team


def _trend_label(change: int) -> str:
    if change >= 100:
        return "stark steigend ⬆️⬆️"
    if change >= 30:
        return "steigend ⬆️"
    if change >= -30:
        return "stabil →"
    if change >= -100:
        return "sinkend ⬇️"
    return "stark sinkend ⬇️⬇️"


def _mini_bar(elo: int, max_elo: int = 2200, width: int = 20) -> str:
    filled = round((elo / max_elo) * width)
    return "█" * min(filled, width) + "░" * max(0, width - filled)


def run(team: str) -> dict:
    entry = resolve_team(team)
    if not entry:
        return {"error": f"Team '{team}' nicht gefunden."}

    elo = entry["elo"] or 0
    elo_1y = entry.get("elo_1y_ago")
    elo_3y = entry.get("elo_3y_ago")
    change_1y = (elo - elo_1y) if elo_1y else None
    change_3y = (elo - elo_3y) if elo_3y else None

    bar_lines = []
    if elo_3y:
        bar_lines.append(f"vor 3J ({elo_3y:4d}): {_mini_bar(elo_3y)}")
    if elo_1y:
        bar_lines.append(f"vor 1J ({elo_1y:4d}): {_mini_bar(elo_1y)}")
    bar_lines.append(f"heute  ({elo:4d}): {_mini_bar(elo)}")

    assessment_parts = []
    if change_3y is not None:
        sign = "+" if change_3y >= 0 else ""
        assessment_parts.append(
            f"In den letzten 3 Jahren: {sign}{change_3y} Punkte ({_trend_label(change_3y)})"
        )
    if change_1y is not None:
        sign = "+" if change_1y >= 0 else ""
        assessment_parts.append(
            f"In den letzten 12 Monaten: {sign}{change_1y} Punkte ({_trend_label(change_1y)})"
        )

    return {
        "team": entry["name"],
        "code": entry["code"],
        "current_elo": elo,
        "current_rank": entry["rank"],
        "elo_1y_ago": elo_1y,
        "elo_3y_ago": elo_3y,
        "change_1y": change_1y,
        "change_3y": change_3y,
        "trend_1y": _trend_label(change_1y) if change_1y is not None else "unbekannt",
        "trend_3y": _trend_label(change_3y) if change_3y is not None else "unbekannt",
        "bar_chart": "\n".join(bar_lines),
        "assessment": " ".join(assessment_parts),
    }
