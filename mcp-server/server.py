"""
server.py — MCP-Server für den WM-2026-Agenten
===============================================
FastAPI-App, die alle Tools als MCP-kompatible Endpunkte bereitstellt.

Endpunkte:
  GET  /tools          Liste aller verfügbaren Tools (MCP tool-list)
  POST /call           Tool aufrufen (MCP tool-call)
  GET  /health         Healthcheck

Langflow bindet diesen Server als MCP-Client ein.
"""

from __future__ import annotations

import importlib
import os
import traceback
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Tools registrieren
TOOLS: dict[str, dict] = {
    "get_matches": {
        "description": "Gibt alle Spiele eines Teams oder einer Gruppe zurück.",
        "parameters": {
            "team":         {"type": "string", "description": "Teamname (z.B. 'Deutschland'). Optional wenn group angegeben."},
            "group":        {"type": "string", "description": "Gruppenname ('Group E' oder nur 'E'). Optional wenn team angegeben."},
            "round_filter": {"type": "string", "description": "Nur diese Runde (z.B. 'Matchday 1'). Optional."},
        },
        "module": "tools.get_matches",
    },
    "get_opponents": {
        "description": "Gibt die Gruppenphase-Gegner eines Teams mit ELO-Stärke zurück.",
        "parameters": {
            "team": {"type": "string", "description": "Teamname (z.B. 'Deutschland', 'DE')"},
        },
        "module": "tools.get_opponents",
    },
    "get_team_elo": {
        "description": "ELO-Rating, Weltrang, historische Entwicklung und Bilanz eines Teams.",
        "parameters": {
            "team": {"type": "string", "description": "Teamname oder 2-Buchstaben-Code (z.B. 'Germany', 'DE', 'Deutschland')"},
        },
        "module": "tools.get_team_elo",
    },
    "compare_teams": {
        "description": "Vergleicht zwei Teams per ELO und berechnet Siegwahrscheinlichkeiten.",
        "parameters": {
            "team1": {"type": "string", "description": "Erstes Team"},
            "team2": {"type": "string", "description": "Zweites Team"},
        },
        "module": "tools.compare_teams",
    },
    "get_elo_trend": {
        "description": "ELO-Entwicklung eines Teams über 1 und 3 Jahre mit Trendeinschätzung.",
        "parameters": {
            "team": {"type": "string", "description": "Teamname"},
        },
        "module": "tools.get_elo_trend",
    },
    "simulate_tournament": {
        "description": (
            "Monte-Carlo-Simulation der WM 2026. Berechnet die Wahrscheinlichkeit, "
            "mit der ein Team jede Runde erreicht (Gruppenphase → Weltmeister)."
        ),
        "parameters": {
            "team":       {"type": "string",  "description": "Teamname für detaillierten Bericht. Ohne Angabe: Top-10 Weltmeister-Odds."},
            "n_sims":     {"type": "integer", "description": "Anzahl Simulationen (Standard: 10000). Mehr = genauer, aber langsamer."},
            "home_boost": {"type": "integer", "description": "ELO-Bonus für Gastgeber USA/Kanada/Mexiko (Standard: 50)."},
        },
        "module": "tools.simulate_tournament",
    },
    "search_news": {
        "description": "Sucht aktuelle WM-2026-Nachrichten über DuckDuckGo (kein API-Key nötig).",
        "parameters": {
            "query":       {"type": "string",  "description": "Suchanfrage, z.B. 'Deutschland Aufstellung WM 2026'"},
            "max_results": {"type": "integer", "description": "Maximale Ergebnisse (Standard: 5)"},
        },
        "module": "tools.search_news",
    },
}


# ---------------------------------------------------------------------------
# FastAPI App
# ---------------------------------------------------------------------------

app = FastAPI(
    title="WM-2026 MCP-Server",
    description="Model Context Protocol Server für den KI-Trainer-2026-Workshop",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# MCP-Protokoll-Endpunkte
# ---------------------------------------------------------------------------

class ToolCallRequest(BaseModel):
    tool: str
    parameters: dict[str, Any] = {}


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "server": "WM-2026 MCP-Server", "tools": list(TOOLS.keys())}


@app.get("/logo.svg")
def get_logo() -> FileResponse:
    """Gibt das offizielle SVG-Logo des WM-2026 MCP-Servers zurück."""
    logo_path = os.path.join(os.path.dirname(__file__), "logo.svg")
    if not os.path.exists(logo_path):
        raise HTTPException(status_code=404, detail="Logo nicht gefunden")
    return FileResponse(logo_path, media_type="image/svg+xml")


@app.get("/tools")
def list_tools() -> dict:
    """Gibt die Liste aller verfügbaren Tools zurück (MCP tool-list)."""
    return {
        "tools": [
            {
                "name": name,
                "description": info["description"],
                "parameters": info["parameters"],
            }
            for name, info in TOOLS.items()
        ]
    }


@app.post("/call")
def call_tool(request: ToolCallRequest) -> dict:
    """Ruft ein Tool auf und gibt das Ergebnis zurück (MCP tool-call)."""
    if request.tool not in TOOLS:
        raise HTTPException(
            status_code=404,
            detail=f"Tool '{request.tool}' nicht gefunden. Verfügbar: {list(TOOLS.keys())}",
        )

    tool_info = TOOLS[request.tool]
    try:
        module = importlib.import_module(tool_info["module"])
        result = module.run(**request.parameters)
        return {"tool": request.tool, "result": result}
    except TypeError as e:
        raise HTTPException(status_code=422, detail=f"Ungültige Parameter: {e}")
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Tool-Fehler: {e}\n{traceback.format_exc()}",
        )
