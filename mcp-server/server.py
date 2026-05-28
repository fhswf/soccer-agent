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

# Tools statisch importieren für API-Endpoints
from tools import (
    get_matches,
    get_opponents,
    get_team_elo,
    compare_teams,
    get_elo_trend,
    simulate_tournament,
    search_news,
    scrape_official_news,
)

class SimulateTournamentRequest(BaseModel):
    team: str | None = None
    n_sims: int = 10000
    home_boost: int = 50
    top_n: int = 10

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
            "team":       {"type": "string",  "description": "Teamname für detaillierten Bericht. Ohne Angabe: Top-N Weltmeister-Odds."},
            "n_sims":     {"type": "integer", "description": "Anzahl Simulationen (Standard: 10000). Mehr = genauer, aber langsamer."},
            "home_boost": {"type": "integer", "description": "ELO-Bonus für Gastgeber USA/Kanada/Mexiko (Standard: 50)."},
            "top_n":      {"type": "integer", "description": "Anzahl der anzuzeigenden Favoriten (Standard: 10)."},
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
    "scrape_official_news": {
        "description": "Scrapt offizielle Nachrichten und Ankündigungen von fifa.com (über DuckDuckGo).",
        "parameters": {
            "max_results": {"type": "integer", "description": "Maximale Ergebnisse (Standard: 5)"},
        },
        "module": "tools.scrape_official_news",
    },
}


# ---------------------------------------------------------------------------
# Standard MCP Server (FastMCP)
# ---------------------------------------------------------------------------
from mcp.server.fastmcp import FastMCP

mcp_server = FastMCP("WM-2026-Server")
mcp_server.settings.transport_security.enable_dns_rebinding_protection = False

@mcp_server.tool(name="get_matches", description="Gibt alle Spiele eines Teams oder einer Gruppe zurück.")
def tool_get_matches(
    team: str | None = None,
    group: str | None = None,
    round_filter: str | None = None,
) -> dict:
    return get_matches.run(team=team, group=group, round_filter=round_filter)

@mcp_server.tool(name="get_opponents", description="Gibt die Gruppenphase-Gegner eines Teams mit ELO-Stärke zurück.")
def tool_get_opponents(
    team: str,
) -> dict:
    return get_opponents.run(team=team)

@mcp_server.tool(name="get_team_elo", description="ELO-Rating, Weltrang, historische Entwicklung und Bilanz eines Teams.")
def tool_get_team_elo(
    team: str,
) -> dict:
    return get_team_elo.run(team=team)

@mcp_server.tool(name="compare_teams", description="Vergleicht zwei Teams per ELO und berechnet Siegwahrscheinlichkeiten.")
def tool_compare_teams(
    team1: str,
    team2: str,
) -> dict:
    return compare_teams.run(team1=team1, team2=team2)

@mcp_server.tool(name="get_elo_trend", description="ELO-Entwicklung eines Teams über 1 und 3 Jahre mit Trendeinschätzung.")
def tool_get_elo_trend(
    team: str,
) -> dict:
    return get_elo_trend.run(team=team)

@mcp_server.tool(name="simulate_tournament", description="Monte-Carlo-Simulation der WM 2026.")
def tool_simulate_tournament(
    team: str | None = None,
    n_sims: int = 10000,
    home_boost: int = 50,
    top_n: int = 10,
) -> dict:
    return simulate_tournament.run(
        team=team,
        n_sims=n_sims,
        home_boost=home_boost,
        top_n=top_n,
    )

@mcp_server.tool(name="search_news", description="Sucht aktuelle WM-2026-Nachrichten über DuckDuckGo.")
def tool_search_news(
    query: str,
    max_results: int = 5,
) -> dict:
    return search_news.run(query=query, max_results=max_results)

@mcp_server.tool(name="scrape_official_news", description="Scrapt offizielle Nachrichten und Ankündigungen von fifa.com.")
def tool_scrape_official_news(
    max_results: int = 5,
) -> dict:
    return scrape_official_news.run(max_results=max_results)


# ---------------------------------------------------------------------------
# FastAPI App
# ---------------------------------------------------------------------------

from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Streamable HTTP App initialisieren, um den session_manager zu erstellen
    mcp_server.streamable_http_app()
    async with mcp_server.session_manager.run():
        yield

app = FastAPI(
    title="WM-2026 MCP-Server",
    description="Model Context Protocol Server für den KI-Trainer-2026-Workshop",
    version="0.1.0",
    lifespan=lifespan,
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


# ---------------------------------------------------------------------------
# Direct REST API Endpoints & Swagger UI
# ---------------------------------------------------------------------------

@app.get("/api/matches", tags=["Direct API Tools"], summary="Gibt alle Spiele eines Teams oder einer Gruppe zurück.")
def api_get_matches(
    team: str | None = None,
    group: str | None = None,
    round_filter: str | None = None,
) -> dict:
    try:
        return get_matches.run(team=team, group=group, round_filter=round_filter)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/opponents", tags=["Direct API Tools"], summary="Gibt die Gruppenphase-Gegner eines Teams mit ELO-Stärke zurück.")
def api_get_opponents(
    team: str,
) -> dict:
    try:
        return get_opponents.run(team=team)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/team_elo", tags=["Direct API Tools"], summary="ELO-Rating, Weltrang, historische Entwicklung und Bilanz eines Teams.")
def api_get_team_elo(
    team: str,
) -> dict:
    try:
        return get_team_elo.run(team=team)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/compare_teams", tags=["Direct API Tools"], summary="Vergleicht zwei Teams per ELO und berechnet Siegwahrscheinlichkeiten.")
def api_compare_teams(
    team1: str,
    team2: str,
) -> dict:
    try:
        return compare_teams.run(team1=team1, team2=team2)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/elo_trend", tags=["Direct API Tools"], summary="ELO-Entwicklung eines Teams über 1 und 3 Jahre mit Trendeinschätzung.")
def api_get_elo_trend(
    team: str,
) -> dict:
    try:
        return get_elo_trend.run(team=team)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/simulate_tournament", tags=["Direct API Tools"], summary="Monte-Carlo-Simulation der WM 2026.")
def api_simulate_tournament(
    req: SimulateTournamentRequest,
) -> dict:
    try:
        return simulate_tournament.run(
            team=req.team,
            n_sims=req.n_sims,
            home_boost=req.home_boost,
            top_n=req.top_n,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/search_news", tags=["Direct API Tools"], summary="Sucht aktuelle WM-2026-Nachrichten über DuckDuckGo.")
def api_search_news(
    query: str,
    max_results: int = 5,
) -> dict:
    try:
        return search_news.run(query=query, max_results=max_results)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/scrape_official_news", tags=["Direct API Tools"], summary="Scrapt offizielle Nachrichten und Ankündigungen von fifa.com.")
def api_scrape_official_news(
    max_results: int = 5,
) -> dict:
    try:
        return scrape_official_news.run(max_results=max_results)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ---------------------------------------------------------------------------
# Standard MCP Streamable HTTP App Mounten
# ---------------------------------------------------------------------------
app.mount("/", mcp_server.streamable_http_app())

# Trigger release-please to update kustomization.yaml

