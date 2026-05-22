"""Tool 5: compare_teams — ELO-Direktvergleich zweier Teams."""

from __future__ import annotations
from data_loader import resolve_team


def _elo_win_prob(elo_a: int, elo_b: int) -> float:
    """ELO-Siegwahrscheinlichkeit für Team A gegen Team B."""
    return 1.0 / (1.0 + 10 ** ((elo_b - elo_a) / 400))


def run(team1: str, team2: str) -> dict:
    """
    Vergleicht zwei Teams anhand ihrer ELO-Ratings.
    Berechnet Siegwahrscheinlichkeiten nach der Standard-ELO-Formel.
    """
    e1 = resolve_team(team1)
    e2 = resolve_team(team2)

    if not e1:
        return {"error": f"Team '{team1}' nicht gefunden."}
    if not e2:
        return {"error": f"Team '{team2}' nicht gefunden."}

    elo1 = e1["elo"] or 1500
    elo2 = e2["elo"] or 1500
    diff = elo1 - elo2

    p1_raw = _elo_win_prob(elo1, elo2)   # Sieg Team 1 (ohne Unentschieden)
    p2_raw = 1.0 - p1_raw

    # Unentschieden-Anteil schätzen (~26% Basiswahrscheinlichkeit,
    # geringer je größer der ELO-Unterschied)
    draw_base = 0.26
    draw_prob = round(draw_base * (1 - abs(diff) / 800), 3)
    draw_prob = max(0.05, draw_prob)

    remaining = 1.0 - draw_prob
    p1_adj = round(p1_raw * remaining, 3)
    p2_adj = round(p2_raw * remaining, 3)

    # Bewertung
    if abs(diff) < 20:
        assessment = "absolutes 50:50 — ELO-technisch kaum ein Unterschied"
    elif abs(diff) < 80:
        fav = e1["name"] if diff > 0 else e2["name"]
        assessment = f"{fav} ist leicht favorisiert"
    elif abs(diff) < 200:
        fav = e1["name"] if diff > 0 else e2["name"]
        assessment = f"{fav} ist klar favorisiert"
    else:
        fav = e1["name"] if diff > 0 else e2["name"]
        assessment = f"{fav} ist der große Favorit"

    summary = (
        f"{e1['name']} (ELO {elo1}, Rang #{e1['rank']}) vs. "
        f"{e2['name']} (ELO {elo2}, Rang #{e2['rank']}). "
        f"ELO-Differenz: {diff:+d}. "
        f"Laut ELO-Formel: {assessment}. "
        f"Siegchancen: {e1['name']} {p1_adj*100:.1f}% | "
        f"Unentschieden {draw_prob*100:.1f}% | "
        f"{e2['name']} {p2_adj*100:.1f}%."
    )

    return {
        "team1": {"name": e1["name"], "code": e1["code"], "elo": elo1, "rank": e1["rank"]},
        "team2": {"name": e2["name"], "code": e2["code"], "elo": elo2, "rank": e2["rank"]},
        "elo_diff": diff,
        "formula": "P(Sieg A) = 1 / (1 + 10^((ELO_B - ELO_A) / 400))",
        "win_prob_team1": round(p1_adj, 3),
        "draw_prob": round(draw_prob, 3),
        "win_prob_team2": round(p2_adj, 3),
        "assessment": assessment,
        "summary": summary,
    }
