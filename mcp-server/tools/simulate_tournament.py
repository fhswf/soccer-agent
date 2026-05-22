"""
Tool 8: simulate_tournament ⭐
Monte-Carlo-Simulation der WM 2026.

Simuliert das Turnier N-mal und gibt Wahrscheinlichkeiten zurück,
mit welcher Häufigkeit ein Team jede Runde erreicht.

Pädagogischer Kern des Workshops:
  - KI-Vorhersagen sind Wahrscheinlichkeiten, keine Gewissheiten
  - Das Ergebnis schwankt bei wenigen Simulationen stark (zeige 100 vs. 10.000!)
  - Heimvorteil als modellierbarer Parameter
"""

from __future__ import annotations

import random
from data_loader import get_elo_data, get_fixtures, resolve_team, resolve_team_fixture_name

# ELO-Ländercode → ELO-Wert (wird beim ersten Aufruf aufgebaut)
_ELO_MAP: dict[str, int] = {}
# Fixture-Name → ELO-Wert
_FIXTURE_ELO: dict[str, int] = {}

# Heimvorteil-Teams (USA, Kanada, Mexiko) — Code
_HOME_TEAMS = {"US", "CA", "MX"}


def _build_elo_map(home_boost: int = 50) -> None:
    """Erstellt Fixture-Name → ELO-Mapping."""
    global _FIXTURE_ELO
    fixtures = get_fixtures()

    for group_info in fixtures["groups"].values():
        for fixture_name in group_info["teams"]:
            if fixture_name in _FIXTURE_ELO:
                continue
            resolved = resolve_team(fixture_name)
            if resolved:
                elo_val = resolved.get("elo") or 1500
                code = resolved.get("code", "")
            else:
                elo_val = 1400
                code = ""
            if code in _HOME_TEAMS:
                elo_val += home_boost
            _FIXTURE_ELO[fixture_name] = elo_val


def _win_prob(elo_a: int, elo_b: int) -> float:
    """ELO-Siegwahrscheinlichkeit für A."""
    return 1.0 / (1.0 + 10 ** ((elo_b - elo_a) / 400))


def _simulate_match(t1: str, t2: str, knockout: bool = False) -> str:
    """Simuliert ein einzelnes Spiel. Gibt Sieger zurück."""
    elo1 = _FIXTURE_ELO.get(t1, 1500)
    elo2 = _FIXTURE_ELO.get(t2, 1500)
    p1 = _win_prob(elo1, elo2)

    r = random.random()
    if knockout:
        # K.o.: Unentschieden → Elfmeter (zufällig 50:50)
        draw_prob = max(0.05, 0.26 * (1 - abs(elo1 - elo2) / 800))
        if r < p1 * (1 - draw_prob):
            return t1
        elif r < (p1 + (1 - p1)) * (1 - draw_prob):
            return t2 if r > p1 * (1 - draw_prob) else t1
        else:
            return t1 if random.random() < 0.5 else t2
    else:
        # Gruppe: Unentschieden möglich
        draw_prob = max(0.05, 0.26 * (1 - abs(elo1 - elo2) / 800))
        if r < draw_prob:
            return "draw"
        return t1 if r < draw_prob + p1 * (1 - draw_prob) else t2


def _simulate_groups(fixtures: dict) -> dict[str, list[str]]:
    """
    Simuliert alle Gruppenspiele.
    Gibt pro Gruppe zurück: [1. Platz, 2. Platz, 3. Platz, 4. Platz]
    """
    results: dict[str, list[str]] = {}

    for group_name, info in fixtures["groups"].items():
        teams = info["teams"]
        points: dict[str, int] = {t: 0 for t in teams}
        gd: dict[str, int] = {t: 0 for t in teams}  # Tordifferenz (vereinfacht als ELO-Proxy)

        for match in info["matches"]:
            t1, t2 = match["team1"], match["team2"]
            winner = _simulate_match(t1, t2, knockout=False)
            if winner == t1:
                points[t1] += 3
                gd[t1] += 1
                gd[t2] -= 1
            elif winner == t2:
                points[t2] += 3
                gd[t1] -= 1
                gd[t2] += 1
            else:  # draw
                points[t1] += 1
                points[t2] += 1

        # Sortieren: Punkte → Tordifferenz → ELO (als Tiebreaker)
        _pts, _gd = points, gd
        standings = sorted(
            teams,
            key=lambda t, p=_pts, g=_gd: (p[t], g[t], _FIXTURE_ELO.get(t, 1500)),
            reverse=True,
        )
        results[group_name] = standings

    return results


def _get_best_thirds(group_standings: dict[str, list[str]]) -> list[str]:
    """Wählt die 8 besten Gruppendritten aus (WM-2026-Regel)."""
    thirds = [(group_standings[g][2], g) for g in group_standings if len(group_standings[g]) >= 3]
    # Sortiert nach ELO des Drittplatzierten
    thirds.sort(key=lambda x: _FIXTURE_ELO.get(x[0], 1500), reverse=True)
    return [t for t, _ in thirds[:8]]


def _simulate_knockout(
    group_standings: dict[str, list[str]]
) -> tuple[dict[str, list[str]], str, dict[str, dict[str, str]]]:
    """
    Simuliert die K.o.-Phase (Round of 32 → Finale).
    Gibt zurück: (champions, world_champion, opponents_map)
    """
    # Qualifikanten aufbauen
    # Gruppensieger (1.) und Zweite (2.) qualifizieren sich automatisch
    qualifiers: dict[str, str] = {}
    for g, standings in group_standings.items():
        letter = g.split()[-1]  # "Group E" → "E"
        qualifiers[f"1{letter}"] = standings[0]
        qualifiers[f"2{letter}"] = standings[1]

    best_thirds = _get_best_thirds(group_standings)
    for i, t in enumerate(best_thirds):
        qualifiers[f"3rd_{i}"] = t

    # Vereinfachte Round of 32: 32 Teams spielen 16 Spiele
    # Wir paaren die 12 Gruppensieger + 12 Gruppenzweiten + 8 Dritte
    round32_teams = (
        [group_standings[g][0] for g in group_standings]  # 12 Sieger
        + [group_standings[g][1] for g in group_standings]  # 12 Zweite
        + best_thirds  # 8 Dritte
    )
    random.shuffle(round32_teams)  # Vereinfachung: zufällige Paarungen ab Round of 32

    current_round = round32_teams
    round_names = ["Round of 32", "Round of 16", "Viertelfinale", "Halbfinale", "Finale"]
    champions: dict[str, list[str]] = {r: [] for r in round_names}
    opponents_map: dict[str, dict[str, str]] = {t: {} for t in round32_teams}

    for round_name in round_names:
        next_round: list[str] = []
        if len(current_round) < 2:
            break
        for i in range(0, len(current_round) - 1, 2):
            t1 = current_round[i]
            t2 = current_round[i + 1]
            opponents_map[t1][round_name] = t2
            opponents_map[t2][round_name] = t1
            winner = _simulate_match(t1, t2, knockout=True)
            next_round.append(winner)
            champions[round_name].append(winner)
        current_round = next_round

    world_champion = current_round[0] if current_round else ""
    return champions, world_champion, opponents_map


def _make_bar(prob: float, width: int = 20) -> str:
    """Erstellt einen ASCII-Fortschrittsbalken."""
    filled = round(prob * width)
    return "█" * filled + "░" * (width - filled)


ROUNDS_ORDER = [
    "Gruppenphase bestehen",
    "Round of 32",
    "Round of 16",
    "Viertelfinale",
    "Halbfinale",
    "Finale",
    "Weltmeister",
]


def run(
    team: str | None = None,
    n_sims: int = 10_000,
    target_round: str = "Weltmeister",
    home_boost: int = 50,
    top_n: int = 10,
) -> dict:
    """
    Simuliert die WM 2026 n_sims-mal und gibt Wahrscheinlichkeiten zurück.

    Parameters
    ----------
    team       : Teamname für detaillierte Ausgabe (optional; ohne = Top-10 Weltmeister)
    n_sims     : Anzahl Simulationen (mehr = genauer, aber langsamer)
    round      : Runde für Einzel-Wahrscheinlichkeit
    home_boost : ELO-Bonus für Gastgeber USA/Kanada/Mexiko
    """
    fixtures = get_fixtures()
    _build_elo_map(home_boost=home_boost)

    # Zähler initialisieren
    all_teams = [t for g in fixtures["groups"].values() for t in g["teams"]]
    reach_count: dict[str, dict[str, int]] = {
        t: {r: 0 for r in ROUNDS_ORDER} for t in all_teams
    }

    # round_name -> team_name -> opponent -> count
    opponent_counts: dict[str, dict[str, dict[str, int]]] = {
        r: {t: {} for t in all_teams}
        for r in ["Round of 32", "Round of 16", "Viertelfinale", "Halbfinale", "Finale"]
    }

    # Simulationen
    for _ in range(n_sims):
        group_standings = _simulate_groups(fixtures)

        # Gruppenphase bestehen = nicht letzter in Gruppe
        for g, standings in group_standings.items():
            # Top 2 direkt durch, Dritte ggf. (vereinfacht: alle außer Vierten)
            for t in standings[:3]:
                reach_count[t]["Gruppenphase bestehen"] += 1

        # K.o.-Phase simulieren
        ko_results, champion, opponents_map = _simulate_knockout(group_standings)

        # Gegner erfassen
        for t, round_opps in opponents_map.items():
            for round_name, opp in round_opps.items():
                if round_name in opponent_counts:
                    opp_dict = opponent_counts[round_name][t]
                    opp_dict[opp] = opp_dict.get(opp, 0) + 1

        for round_name, winners in ko_results.items():
            for w in winners:
                if round_name in reach_count.get(w, {}):
                    reach_count[w][round_name] += 1

        if champion:
            reach_count[champion]["Weltmeister"] += 1

    # Wahrscheinlichkeiten berechnen
    probs: dict[str, dict[str, float]] = {
        t: {r: reach_count[t][r] / n_sims for r in ROUNDS_ORDER}
        for t in all_teams
    }

    if team:
        fixture_name = resolve_team_fixture_name(team)
        if not fixture_name or fixture_name not in probs:
            return {"error": f"Team '{team}' nicht bei der WM 2026 oder nicht gefunden."}

        p = probs[fixture_name]
        elo_entry = resolve_team(fixture_name)
        elo_val = elo_entry["elo"] if elo_entry else "?"

        # ASCII-Balkendiagramm
        bar_lines = []
        for r in reversed(ROUNDS_ORDER):
            prob = p[r]
            bar_lines.append(f"{r:<25} {_make_bar(prob)} {prob*100:5.1f}%")

        # Erwartete Runde (letzte Runde mit > 50% Wahrscheinlichkeit)
        expected_round = "Gruppenphase"
        for r in ROUNDS_ORDER:
            if p[r] >= 0.5:
                expected_round = r

        summary = (
            f"{fixture_name} (ELO {elo_val}) hat in {n_sims:,} Simulationen folgende Chancen: "
            f"Gruppenphase bestehen: {p['Gruppenphase bestehen']*100:.1f}%, "
            f"Viertelfinale: {p['Viertelfinale']*100:.1f}%, "
            f"Weltmeister: {p['Weltmeister']*100:.1f}%. "
            f"Erwartete Runde: {expected_round}."
        )

        # Wahrscheinlichste Gegner in jeder K.o.-Runde ermitteln
        most_probable_opponents = {}
        for r in ["Round of 32", "Round of 16", "Viertelfinale", "Halbfinale", "Finale"]:
            opp_dict = opponent_counts.get(r, {}).get(fixture_name, {})
            if opp_dict:
                sorted_opps = sorted(opp_dict.items(), key=lambda x: x[1], reverse=True)
                total_round_reached = sum(opp_dict.values())
                most_probable_opponents[r] = [
                    {
                        "team": opp,
                        "probability": round(count / total_round_reached, 4),
                        "percent": f"{(count / total_round_reached) * 100:.1f}%",
                    }
                    for opp, count in sorted_opps[:3]
                ]

        return {
            "team": fixture_name,
            "elo": elo_val,
            "n_simulations": n_sims,
            "probabilities": {r: round(v, 4) for r, v in p.items()},
            "expected_round": expected_round,
            "bar_chart": "\n".join(bar_lines),
            "summary": summary,
            "most_probable_opponents": most_probable_opponents,
        }

    else:
        # Alle Teams: Top-N nach Weltmeister-Wahrscheinlichkeit
        world_probs = sorted(
            [(t, probs[t]["Weltmeister"]) for t in all_teams],
            key=lambda x: x[1],
            reverse=True,
        )
        top_teams = world_probs[:top_n]
        bar_lines = [
            f"{i+1:2d}. {t:<22} {_make_bar(p, 25)} {p*100:5.1f}%"
            for i, (t, p) in enumerate(top_teams)
        ]
        return {
            "n_simulations": n_sims,
            "world_cup_winner_odds": [
                {"rank": i + 1, "team": t, "probability": round(p, 4), "percent": f"{p*100:.1f}%"}
                for i, (t, p) in enumerate(top_teams)
            ],
            "bar_chart": "\n".join(bar_lines),
            "note": f"Basierend auf {n_sims:,} Monte-Carlo-Simulationen mit ELO-Ratings von eloratings.net",
        }
