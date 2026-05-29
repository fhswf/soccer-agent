"""
cli.py — KI-Trainer 2026 Kommandozeilen-Werkzeug
=================================================
Ersetzt das Makefile. Nutze: uv run wm <befehl>

Befehle:
  uv run wm fetch       Rohdaten herunterladen (ELO + Spielplan)
  uv run wm clean       Daten bereinigen und Chunks erstellen
  uv run wm ingest      Chunks in Vektordatenbanken einspeichern
  uv run wm pipeline    fetch + clean + ingest (alles auf einmal)
  uv run wm mcp         MCP-Server starten
  uv run wm simulate    Monte-Carlo-Simulation der WM 2026 starten
  uv run wm info        Zeigt Info zu den geladenen Daten
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table
from rich import print as rprint

app = typer.Typer(
    name="wm",
    help="🏆 KI-Trainer 2026 — WM-Experten-Agent Werkzeugkasten",
    no_args_is_help=True,
)
console = Console()

ROOT = Path(__file__).parent
DATA_DIR = ROOT / "data-pipeline" / "data"


# ---------------------------------------------------------------------------
# Datenpipeline
# ---------------------------------------------------------------------------

@app.command()
def fetch(
    no_cache: bool = typer.Option(False, "--no-cache", help="Daten neu herunterladen (ignoriert Cache)"),
) -> None:
    """📥 Rohdaten herunterladen: ELO-Ratings und WM-Spielplan."""
    console.rule("[bold blue]Schritt 1: Rohdaten herunterladen")

    env_flag = "--no-cache" if no_cache else ""

    with console.status("Lade ELO-Ratings von eloratings.net …"):
        _run_script("data-pipeline/fetch_elo.py", extra_args=[] if not no_cache else ["--no-cache"])

    with console.status("Lade WM-Spielplan von openfootball/worldcup.json …"):
        _run_script("data-pipeline/fetch_fixtures.py", extra_args=[] if not no_cache else ["--no-cache"])

    rprint("[green]✅ Rohdaten heruntergeladen![/green]")


@app.command()
def scrape(
    max_results: int = typer.Option(50, "--max-results", "-n", help="Maximale Anzahl an News"),
) -> None:
    """🌐 Offizielle WM-2026-Nachrichten von FIFA.com scrapen."""
    if not isinstance(max_results, int):
        max_results = 50
    console.rule("[bold blue]Schritt 2: Offizielle FIFA-News scrapen")
    with console.status("Scrape offizielle Ankündigungen von FIFA.com …"):
        _run_script("data-pipeline/scrape_news.py", extra_args=["--max-results", str(max_results)])
    rprint("[green]✅ Offizielle FIFA-News erfolgreich gescrapet![/green]")


@app.command()
def clean() -> None:
    """🔧 Daten bereinigen und in Chunks aufteilen."""
    console.rule("[bold blue]Schritt 3: Daten bereinigen")
    with console.status("Erstelle Text-Chunks aus ELO, Spielplan, News und Fun-Facts …"):
        _run_script("data-pipeline/clean.py")
    rprint("[green]✅ Chunks erstellt![/green]")


@app.command()
def ingest(
    skip_embed: bool = typer.Option(False, "--skip-embed", help="Gespeicherte Embeddings nutzen"),
) -> None:
    """🗄️ Chunks in ChromaDB einspeichern."""
    console.rule("[bold blue]Schritt 4: Vektordatenbank befüllen")
    args: list[str] = []
    if skip_embed:
        args.append("--skip-embed")
    _run_script("data-pipeline/ingest.py", extra_args=args)
    rprint("[green]✅ Vektordatenbank befüllt![/green]")


@app.command()
def pipeline(
    no_cache: bool = typer.Option(False, "--no-cache", help="Daten neu herunterladen"),
) -> None:
    """🚀 Komplette Pipeline: fetch → scrape → clean → ingest."""
    console.rule("[bold yellow]Komplette Datenpipeline starten")
    fetch(no_cache=no_cache)
    try:
        scrape(max_results=50)
    except Exception as e:
        rprint(f"[bold red]⚠️  Scraping fehlgeschlagen, fahre mit restlicher Pipeline fort: {e}[/bold red]")
    clean()
    ingest()
    rprint("[bold green]✅ Datenpipeline abgeschlossen![/bold green]")


# ---------------------------------------------------------------------------
# Services
# ---------------------------------------------------------------------------

@app.command()
def mcp(
    host: str = typer.Option("0.0.0.0", help="Host-Adresse"),
    port: int = typer.Option(9000, help="Port"),
    reload: bool = typer.Option(True, "--reload/--no-reload", help="Auto-Reload bei Änderungen"),
) -> None:
    """🔧 MCP-Server starten."""
    console.rule("[bold blue]MCP-Server starten")
    rprint(f"[cyan]Server läuft auf http://{host}:{port}[/cyan]")
    reload_flag = ["--reload"] if reload else []
    subprocess.run(
        ["uvicorn", "server:app", f"--host={host}", f"--port={port}", *reload_flag],
        cwd=ROOT / "mcp-server",
        check=True,
    )


@app.command()
def simulate(
    team: str = typer.Option(None, "--team", "-t", help="Teamname für Detailbericht (z. B. Deutschland)"),
    n_sims: int = typer.Option(1000, "--sims", "-n", help="Anzahl der Simulationen"),
    home_boost: int = typer.Option(50, "--boost", "-b", help="ELO-Heimvorteil-Boost für Gastgeber"),
    top_n: int = typer.Option(10, "--top", "-k", help="Anzahl der anzuzeigenden Favoriten"),
) -> None:
    """🎲 Monte-Carlo-Simulation der WM 2026 starten."""
    console.rule("[bold blue]Monte-Carlo-Turniersimulation")
    
    import sys
    sys.path.append(str(ROOT / "mcp-server"))
    from tools import simulate_tournament
    
    with console.status(f"Simuliere Turnier {n_sims:,} Mal..."):
        res = simulate_tournament.run(team=team, n_sims=n_sims, home_boost=home_boost, top_n=top_n)
        
    if team:
        rprint(f"\n[bold green]Prognose für {res['team']} (ELO {res['elo']}):[/bold green]")
        rprint(res['summary'])
        rprint("\n[bold cyan]Wahrscheinlichkeiten pro Runde:[/bold cyan]")
        rprint(res['bar_chart'])
        
        if "most_probable_opponents" in res and res["most_probable_opponents"]:
            rprint("\n[bold cyan]Wahrscheinlichste Gegner in der K.o.-Phase (falls erreicht):[/bold cyan]")
            for r, opps in res["most_probable_opponents"].items():
                opps_str = ", ".join([f"{o['team']} ({o['percent']})" for o in opps])
                rprint(f"  {r:<15}: {opps_str}")
    else:
        rprint(f"\n[bold green]Top-{top_n} Weltmeister-Chancen:[/bold green]")
        rprint(res['bar_chart'])
        rprint(f"\n[dim]{res['note']}[/dim]")


# ---------------------------------------------------------------------------
# Info / Diagnose
# ---------------------------------------------------------------------------

@app.command()
def info() -> None:
    """📊 Zeigt Infos zu den geladenen Daten (ELO, Chunks, Fixtures)."""
    import json

    console.rule("[bold yellow]KI-Trainer 2026 — Daten-Übersicht")

    # ELO
    elo_path = DATA_DIR / "elo_ratings.json"
    if elo_path.exists():
        elo = json.loads(elo_path.read_text())
        t = Table(title="Top 10 Teams nach ELO", show_header=True, header_style="bold cyan")
        t.add_column("Rang", style="dim")
        t.add_column("Team")
        t.add_column("ELO", justify="right")
        t.add_column("Trend 1J", justify="right")
        for team in elo[:10]:
            change = team.get("elo_change_1y", 0) or 0
            trend = f"[green]+{change}[/green]" if change >= 0 else f"[red]{change}[/red]"
            t.add_row(f"#{team['rank']}", team["name"], str(team["elo"]), trend)
        console.print(t)
    else:
        rprint("[yellow]⚠️  ELO-Daten fehlen — 'uv run wm fetch' ausführen[/yellow]")

    # Fixtures
    fix_path = DATA_DIR / "fixtures.json"
    if fix_path.exists():
        fix = json.loads(fix_path.read_text())
        grp_count = len(fix.get("groups", {}))
        match_count = sum(len(g["matches"]) for g in fix.get("groups", {}).values())
        ko_count = len(fix.get("knockout", []))
        rprint(f"\n📅 Spielplan: {grp_count} Gruppen, {match_count} Gruppenspiele, {ko_count} K.o.-Spiele")
        rprint(f"   Finale: {fix.get('final_date')} in {fix.get('final_venue')}")
    else:
        rprint("[yellow]⚠️  Spielplan fehlt — 'uv run wm fetch' ausführen[/yellow]")

    # Chunks
    chunks_path = DATA_DIR / "chunks.json"
    if chunks_path.exists():
        chunks = json.loads(chunks_path.read_text())
        by_type: dict[str, int] = {}
        for c in chunks:
            by_type[c["data_type"]] = by_type.get(c["data_type"], 0) + 1
        rprint(f"\n🧩 Chunks gesamt: {len(chunks)}")
        for dtype, count in by_type.items():
            rprint(f"   {dtype}: {count}")
    else:
        rprint("[yellow]⚠️  Chunks fehlen — 'uv run wm clean' ausführen[/yellow]")


# ---------------------------------------------------------------------------
# Hilfsfunktionen
# ---------------------------------------------------------------------------

def _run_script(relative_path: str, extra_args: list[str] | None = None) -> None:
    """Führt ein Python-Skript mit dem aktuellen Interpreter aus."""
    import os
    args = extra_args or []
    env = os.environ.copy()
    env["PYTHONWARNINGS"] = "ignore"
    result = subprocess.run(
        [sys.executable, str(ROOT / relative_path), *args],
        check=True,
        capture_output=False,
        env=env,
    )


if __name__ == "__main__":
    app()
