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
    _FIXTURE_ELO.clear()
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
    """Simuliert ein Match basierend auf Elo-Werten."""
    elo1 = _FIXTURE_ELO.get(t1, 1500)
    elo2 = _FIXTURE_ELO.get(t2, 1500)
    
    # 1. Standard-Elo-Erwartungswert für Team 1
    # (Beinhaltet Sieg + 0.5 * Unentschieden)
    exp_1 = 1 / (10 ** (-(elo1 - elo2) / 400) + 1)
    
    # 2. Dynamische Remisbreite bestimmen (sinkt bei großer Elo-Differenz)
    draw_prob = max(0.05, 0.26 * (1 - abs(elo1 - elo2) / 800))
    
    # 3. Echte Drei-Weg-Wahrscheinlichkeiten ableiten
    # Wir ziehen die halbe Remis-Chance fair von beiden Seiten ab
    win_prob_1 = max(0.0, exp_1 - (draw_prob / 2))
    win_prob_2 = max(0.0, (1 - exp_1) - (draw_prob / 2))
    
    # Normalisieren, falls durch Rundung/Grenzen minimale Abweichungen entstehen
    total = win_prob_1 + win_prob_2 + draw_prob
    p_t1 = win_prob_1 / total
    p_draw = draw_prob / total

    # 4. Würfeln
    r = random.random()
    
    if knockout:
        # K.o.-Spiel: Bei Remis entscheidet das Elfmeterschießen (50:50)
        if r < p_t1:
            return t1
        elif r < p_t1 + p_draw:
            return t1 if random.random() < 0.5 else t2
        else:
            return t2
    else:
        # Gruppenspiel: Unentschieden ist ein gültiges Ergebnis
        if r < p_t1:
            return t1
        elif r < p_t1 + p_draw:
            return "draw"
        else:
            return t2


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


def _resolve_team_placeholder(
    placeholder: str,
    qualifiers: dict[str, str],
    match_results: dict[str, dict[str, str]],
) -> str:
    """Löst Platzhalter wie '1A', '2B', 'W73' oder 'L101' in Teamnamen auf."""
    if not placeholder:
        return ""
    if placeholder.startswith("W"):
        match_num = placeholder[1:]
        return match_results.get(match_num, {}).get("winner", "")
    elif placeholder.startswith("L"):
        match_num = placeholder[1:]
        return match_results.get(match_num, {}).get("loser", "")
    else:
        return qualifiers.get(placeholder, "")


def _simulate_knockout(
    group_standings: dict[str, list[str]]
) -> tuple[dict[str, list[str]], str, dict[str, dict[str, str]]]:
    """
    Simuliert die K.o.-Phase (Round of 32 → Finale) basierend auf den Spielpaarungen in fixtures.json.
    Gibt zurück: (champions, world_champion, opponents_map)
    """
    qualifiers: dict[str, str] = {}

    # 1. Gruppensieger und Zweite qualifizieren sich automatisch
    for g, standings in group_standings.items():
        letter = g.split()[-1]  # "Group E" → "E"
        qualifiers[f"1{letter}"] = standings[0]
        qualifiers[f"2{letter}"] = standings[1]

    # 2. Gruppendritte zuweisen
    team_group: dict[str, str] = {}
    for g, standings in group_standings.items():
        group_letter = g.split()[-1]
        for t in standings:
            team_group[t] = group_letter

    best_thirds = _get_best_thirds(group_standings)
    assigned_thirds: set[str] = set()

    third_place_placeholders = [
        "3A/B/C/D/F",
        "3C/D/F/G/H",
        "3C/E/F/H/I",
        "3E/H/I/J/K",
        "3B/E/F/I/J",
        "3A/E/H/I/J",
        "3E/F/G/I/J",
        "3D/E/I/J/L",
    ]

    for ph in third_place_placeholders:
        allowed_letters = ph[1:].split("/")
        assigned_team = None
        for t in best_thirds:
            if t not in assigned_thirds:
                g_letter = team_group.get(t)
                if g_letter in allowed_letters:
                    assigned_team = t
                    break

        if not assigned_team:
            for t in best_thirds:
                if t not in assigned_thirds:
                    assigned_team = t
                    break

        if assigned_team:
            qualifiers[ph] = assigned_team
            assigned_thirds.add(assigned_team)

    # 3. Vorbereitung der Ergebnisse
    round32_teams = list(qualifiers.values())
    opponents_map: dict[str, dict[str, str]] = {t: {} for t in round32_teams}

    round_mapping = {
        "Round of 32": "Sechzehntelfinale",
        "Round of 16": "Achtelfinale",
        "Quarter-final": "Viertelfinale",
        "Semi-final": "Halbfinale",
        "Final": "Finale",
    }

    champions: dict[str, list[str]] = {
        "Sechzehntelfinale": [],
        "Achtelfinale": [],
        "Viertelfinale": [],
        "Halbfinale": [],
        "Finale": [],
    }

    fixtures = get_fixtures()
    knockout_matches = fixtures.get("knockout", [])
    match_results: dict[str, dict[str, str]] = {}
    world_champion = ""

    for m in knockout_matches:
        round_name = m["round"]
        if round_name == "Match for third place":
            continue

        t1_placeholder = m["team1"]
        t2_placeholder = m["team2"]

        t1 = _resolve_team_placeholder(t1_placeholder, qualifiers, match_results)
        t2 = _resolve_team_placeholder(t2_placeholder, qualifiers, match_results)

        if not t1 or not t2:
            continue

        if t1 not in opponents_map:
            opponents_map[t1] = {}
        if t2 not in opponents_map:
            opponents_map[t2] = {}

        mapped_round = round_mapping.get(round_name)
        if mapped_round:
            opponents_map[t1][mapped_round] = t2
            opponents_map[t2][mapped_round] = t1

        winner = _simulate_match(t1, t2, knockout=True)
        loser = t2 if winner == t1 else t1

        num = m.get("num")
        if num is not None:
            match_results[str(num)] = {"winner": winner, "loser": loser}

        if mapped_round:
            champions[mapped_round].append(winner)

        if round_name == "Final":
            world_champion = winner
    return champions, world_champion, opponents_map


def _make_bar(prob: float, width: int = 20) -> str:
    """Erstellt einen ASCII-Fortschrittsbalken."""
    filled = round(prob * width)
    return "█" * filled + "░" * (width - filled)


ROUNDS_ORDER = [
    "Gruppenphase bestehen",
    "Achtelfinale",
    "Viertelfinale",
    "Halbfinale",
    "Finale",
    "Weltmeister",
]


def _get_polymarket_odds() -> dict[str, float]:
    """
    Fragt die Polymarket Gamma API nach den aktuellen Siegwahrscheinlichkeiten der WM 2026 ab.
    Gibt ein Mapping von Teamname -> Wahrscheinlichkeit zurück.
    """
    import httpx
    import json
    try:
        url = "https://gamma-api.polymarket.com/public-search"
        params = {"q": "2026 FIFA World Cup Winner", "keep_closed_markets": 1}
        response = httpx.get(url, params=params, timeout=3.0)
        if response.status_code != 200:
            return {}
            
        data = response.json()
        events = data.get("events", [])
        if not events:
            return {}
            
        target_event = None
        for e in events:
            if "2026 FIFA World Cup Winner" in e.get("title", ""):
                target_event = e
                break
        if not target_event:
            target_event = events[0]
            
        odds: dict[str, float] = {}
        for m in target_event.get("markets", []):
            question = m.get("question", "")
            prices = m.get("outcomePrices")
            if "Will " in question and " win the" in question:
                start_idx = question.find("Will ") + 5
                end_idx = question.find(" win the")
                raw_team = question[start_idx:end_idx].strip()
                
                if isinstance(prices, str):
                    prices = json.loads(prices)
                    
                if prices and len(prices) >= 2:
                    prob = float(prices[0])
                    resolved = resolve_team_fixture_name(raw_team)
                    if resolved:
                        odds[resolved] = prob
        return odds
    except Exception:
        return {}


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
        for r in ["Sechzehntelfinale", "Achtelfinale", "Viertelfinale", "Halbfinale", "Finale"]
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

        # Zählen der erreichten Runden
        for w in ko_results["Sechzehntelfinale"]:
            reach_count[w]["Achtelfinale"] += 1
        for w in ko_results["Achtelfinale"]:
            reach_count[w]["Viertelfinale"] += 1
        for w in ko_results["Viertelfinale"]:
            reach_count[w]["Halbfinale"] += 1
        for w in ko_results["Halbfinale"]:
            reach_count[w]["Finale"] += 1

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

        # Polymarket-Quoten abrufen
        polymarket_odds = _get_polymarket_odds()
        poly_p = polymarket_odds.get(fixture_name)
        poly_str = f", Weltmeister (Polymarket): {poly_p*100:.1f}%" if poly_p is not None else ""

        summary = (
            f"{fixture_name} (ELO {elo_val}) hat in {n_sims:,} Simulationen folgende Chancen: "
            f"Gruppenphase bestehen: {p['Gruppenphase bestehen']*100:.1f}%, "
            f"Viertelfinale: {p['Viertelfinale']*100:.1f}%, "
            f"Weltmeister (ELO-Sim): {p['Weltmeister']*100:.1f}%{poly_str}. "
            f"Erwartete Runde: {expected_round}."
        )

        # Wahrscheinlichste Gegner in jeder K.o.-Runde ermitteln
        most_probable_opponents = {}
        for r in ["Sechzehntelfinale", "Achtelfinale", "Viertelfinale", "Halbfinale", "Finale"]:
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
            "polymarket_probability": round(poly_p, 4) if poly_p is not None else None,
            "polymarket_percent": f"{poly_p*100:.1f}%" if poly_p is not None else "N/A",
            "most_probable_opponents": most_probable_opponents,
        }

    else:
        # Polymarket-Quoten abrufen
        polymarket_odds = _get_polymarket_odds()

        # Alle Teams: Top-N nach Weltmeister-Wahrscheinlichkeit
        world_probs = sorted(
            [(t, probs[t]["Weltmeister"]) for t in all_teams],
            key=lambda x: x[1],
            reverse=True,
        )
        top_teams = world_probs[:top_n]
        
        bar_lines = []
        for i, (t, p) in enumerate(top_teams):
            poly_p = polymarket_odds.get(t)
            poly_str = f" | Polymarket: {poly_p*100:5.1f}%" if poly_p is not None else ""
            bar_lines.append(
                f"{i+1:2d}. {t:<22} {_make_bar(p, 20)} ELO-Sim: {p*100:5.1f}%{poly_str}"
            )
            
        return {
            "n_simulations": n_sims,
            "world_cup_winner_odds": [
                {
                    "rank": i + 1,
                    "team": t,
                    "probability": round(p, 4),
                    "percent": f"{p*100:.1f}%",
                    "polymarket_probability": round(poly_p, 4) if poly_p is not None else None,
                    "polymarket_percent": f"{poly_p*100:.1f}%" if poly_p is not None else "N/A"
                }
                for i, (t, p) in enumerate(top_teams)
            ],
            "bar_chart": "\n".join(bar_lines),
            "note": f"Basierend auf {n_sims:,} Monte-Carlo-Simulationen mit ELO-Ratings und Live-Odds von Polymarket",
        }
