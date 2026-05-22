import json
from pathlib import Path

def make_notebook(cells):
    return {
        "cells": cells,
        "metadata": {
            "kernelspec": {
                "display_name": "Python 3 (ipykernel)",
                "language": "python",
                "name": "python3"
            },
            "language_info": {
                "name": "python"
            }
        },
        "nbformat": 4,
        "nbformat_minor": 2
    }

def markdown_cell(source):
    return {
        "cell_type": "markdown",
        "metadata": {},
        "source": [line + "\n" for line in source]
    }

def code_cell(source):
    return {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": [line + "\n" for line in source]
    }

# ---------------------------------------------------------------------------
# Notebook 1: 01_mcp_client.ipynb
# ---------------------------------------------------------------------------
cells_01 = [
    markdown_cell([
        "# 🏆 Workshop: Bau deinen eigenen WM-Experten 2026",
        "## Notebook 1: Verbindung zum MCP-Server & Tool-Aufrufe",
        "",
        "In diesem Notebook lernen wir das **Model Context Protocol (MCP)** kennen. MCP ist ein offenes Protokoll, das es KIs (wie ChatGPT, Claude oder euren eigenen Agenten) ermöglicht, auf externe Datenquellen und Tools zuzugreifen.",
        "",
        "Unser WM-Experten-Agent benötigt Zugriff auf aktuelle Spieldaten, ELO-Ratings und Simulations-Algorithmen. Diese werden von unserem maßgeschneiderten **MCP-Server** bereitgestellt.",
        "",
        "### Lernziele:",
        "1. Verstehen, wie ein MCP-Client mit einem MCP-Server über HTTP kommuniziert.",
        "2. Abfragen der verfügbaren Tools des MCP-Servers.",
        "3. Ausführen von Tools wie ELO-Abfragen und der Turnier-Simulation über Python."
    ]),
    markdown_cell([
        "### Schritt 1: Verbindung testen und Tools auflisten",
        "Unser MCP-Server läuft als FastAPI-Anwendung und stellt eine REST-API bereit. Der standardmäßige Endpunkt `/tools` listet alle Funktionen auf, die die KI aufrufen kann. Wir nutzen die Python-Bibliothek `httpx`, um diesen aufzurufen."
    ]),
    code_cell([
        "import httpx",
        "import json",
        "",
        "# Die URL des MCP-Servers (Standard: localhost:9000)",
        "MCP_URL = \"http://localhost:9000\"",
        "",
        "try:",
        "    response = httpx.get(f\"{MCP_URL}/tools\")",
        "    response.raise_for_status()",
        "    data = response.json()",
        "    tools = data.get(\"tools\", [])",
        "    ",
        "    print(f" + 'f"✅ Erfolgreich verbunden! {len(tools)} Tools gefunden:\\n"' + ")",
        "    for tool in tools:",
        "        print(f" + 'f"🛠️  Tool-Name: {tool[\'name\']}"' + ")",
        "        print(f" + 'f"   Beschreibung: {tool[\'description\']}"' + ")",
        "        print(\"   Parameter:\")",
        "        print(json.dumps(tool[\"parameters\"], indent=4, ensure_ascii=False))",
        "        print(\"-\" * 60)",
        "except Exception as e:",
        "    print(f\"❌ Fehler bei der Verbindung zum MCP-Server: {e}\")",
        "    print(\"HINWEIS: Bitte stelle sicher, dass der MCP-Server läuft! Startbefehl im Terminal: uv run wm mcp\")"
    ]),
    markdown_cell([
        "### Schritt 2: ELO-Statistiken abfragen",
        "Wir rufen nun das Tool `get_team_elo` auf. Dazu senden wir einen `POST`-Request an den `/call`-Endpunkt des MCP-Servers mit dem gewünschten Tool-Namen und den Parametern."
    ]),
    code_cell([
        "def call_tool(name, parameters={}):",
        "    \"\"\"Hilfsfunktion, um ein MCP-Tool aufzurufen.\"\"\"",
        "    response = httpx.post(f\"{MCP_URL}/call\", json={\"tool\": name, \"parameters\": parameters})",
        "    response.raise_for_status()",
        "    return response.json().get(\"result\", {})",
        "",
        "# ELO-Daten für Deutschland abfragen",
        "deutschland_elo = call_tool(\"get_team_elo\", {\"team\": \"Deutschland\"})",
        "print(json.dumps(deutschland_elo, indent=2, ensure_ascii=False))"
    ]),
    markdown_cell([
        "### Schritt 3: Turniersimulation ausführen",
        "Der MCP-Server verfügt über eine Monte-Carlo-Simulation für das gesamte Turnier (`simulate_tournament`). Wir rufen das Tool auf und lassen die Chancen berechnen."
    ]),
    code_cell([
        "# Simulation starten",
        "sim_result = call_tool(\"simulate_tournament\", {\"team\": \"Deutschland\", \"n_sims\": 1000})",
        "",
        "print(\"=== WM 2026 Prognose für Deutschland ===\")",
        "print(sim_result.get(\"summary\"))",
        "print(\"\\nVisualisierung der Wahrscheinlichkeiten pro Runde:\")",
        "print(sim_result.get(\"bar_chart\"))"
    ]),
    markdown_cell([
        "### 🧠 Aufgabe für dich:",
        "Schreibe ein kleines Skript, das die Siegwahrscheinlichkeiten der Top-10-Teams abfragt und ausgibt. Nutze dazu das Tool `simulate_tournament` ohne Angabe eines Teams."
    ]),
    code_cell([
        "# DEINE LÖSUNG HIER:",
        "top10_result = call_tool(\"simulate_tournament\", {\"n_sims\": 1000})",
        "print(top10_result.get(\"bar_chart\"))"
    ])
]

# ---------------------------------------------------------------------------
# Notebook 2: 02_monte_carlo.ipynb
# ---------------------------------------------------------------------------
cells_02 = [
    markdown_cell([
        "# 🎲 Workshop: Bau deinen eigenen WM-Experten 2026",
        "## Notebook 2: Simulation der WM 2026 mit Monte-Carlo",
        "",
        "Warum können wir Fußballspiele nicht exakt vorhersagen? Weil der Sport voller Zufälle steckt! Ein Favorit kann durch eine rote Karte oder ein unglückliches Eigentor verlieren.",
        "",
        "Um dennoch fundierte Prognosen zu treffen, nutzen Profis **Monte-Carlo-Simulationen**. Statt das Turnier nur einmal im Kopf durchzuspielen, lassen wir den Computer das Turnier **10.000-mal** simulieren. Aus der Häufigkeit der Ergebnisse berechnen wir die Wahrscheinlichkeiten (z.B. \"In 15% aller Simulationen wird Frankreich Weltmeister\").",
        "",
        "### Lernziele:",
        "1. Die ELO-Formel für Siegwahrscheinlichkeiten verstehen und in Python implementieren.",
        "2. Ein einzelnes Fußballspiel simulieren.",
        "3. Verstehen, warum mehr Simulationen (Gesetz der großen Zahlen) zu stabileren Ergebnissen führen."
    ]),
    markdown_cell([
        "### Schritt 1: Die ELO-Siegwahrscheinlichkeit",
        "Die ELO-Zahl misst die Spielstärke eines Teams. Aus dem Unterschied zweier ELO-Zahlen ($R_A$ und $R_B$) lässt sich die mathematische Wahrscheinlichkeit berechnen, dass Team A gewinnt. Die Formel lautet:",
        "",
        "$$P_A = \\frac{1}{1 + 10^{\\frac{R_B - R_A}{400}}}$$"
    ]),
    code_cell([
        "def win_probability(elo_a: float, elo_b: float) -> float:",
        "    \"\"\"Berechnet die Wahrscheinlichkeit, dass Team A gegen Team B gewinnt.\"\"\"",
        "    return 1.0 / (1.0 + 10 ** ((elo_b - elo_a) / 400))",
        "",
        "# Beispiel: Deutschland (ELO 1900) gegen Ecuador (ELO 1750)",
        "p_de = win_probability(1900, 1750)",
        "print(f\"Siegwahrscheinlichkeit Deutschland: {p_de * 100:.1f}%\")",
        "print(f\"Siegwahrscheinlichkeit Ecuador: {(1 - p_de) * 100:.1f}%\")"
    ]),
    markdown_cell([
        "### Schritt 2: Ein einzelnes Spiel simulieren",
        "Wir nutzen eine Zufallszahl zwischen `0.0` und `1.0` (`random.random()`). Liegt die Zufallszahl unter der Siegwahrscheinlichkeit von Team A, gewinnt Team A. Andernfalls gewinnt Team B."
    ]),
    code_cell([
        "import random",
        "",
        "def simulate_match(elo_a: float, elo_b: float) -> str:",
        "    \"\"\"Simuliert ein Spiel und gibt 'Team A' oder 'Team B' zurück.\"\"\"",
        "    p_a = win_probability(elo_a, elo_b)",
        "    if random.random() < p_a:",
        "        return \"Team A\"",
        "    return \"Team B\"",
        "",
        "# Simuliere das Spiel 5-mal. Jedes Mal kann ein anderes Ergebnis herauskommen!",
        "for i in range(1, 6):",
        "    print(f\"Spiel {i} Sieger: {simulate_match(1900, 1750)}\")"
    ]),
    markdown_cell([
        "### Schritt 3: Gesetz der großen Zahlen (Varianz & Stabilität)",
        "Wenn wir ein Spiel nur 10-mal simulieren, ist das Ergebnis sehr instabil. Simulieren wir es jedoch 10.000-mal, nähert sich das Ergebnis der exakten mathematischen Wahrscheinlichkeit an.",
        "Wir probieren das interaktiv aus."
    ]),
    code_cell([
        "from ipywidgets import interact, IntSlider",
        "",
        "def run_simulation(elo_a, elo_b, n_sims):",
        "    results = [simulate_match(elo_a, elo_b) for _ in range(n_sims)]",
        "    wins_a = results.count(\"Team A\")",
        "    pct_a = (wins_a / n_sims) * 100",
        "    ",
        "    print(f\"Bei {n_sims} Simulationen:\")",
        "    print(f\"  Team A gewinnt: {wins_a} Mal ({pct_a:.2f}%)\")",
        "    print(f\"  Team B gewinnt: {n_sims - wins_a} Mal ({100 - pct_a:.2f}%)\")",
        "    print(f\"  Ziel-Wahrscheinlichkeit: {win_probability(elo_a, elo_b)*100:.2f}%\")",
        "",
        "# Ziehe den Schieberegler, um zu sehen, wie die Schwankung bei kleinen Zahlen riesig ist",
        "# und bei großen Zahlen verschwindet!",
        "interact(run_simulation, ",
        "         elo_a=widgets.IntSlider(min=1200, max=2200, step=50, value=1900, description=\"ELO A\"),",
        "         elo_b=widgets.IntSlider(min=1200, max=2200, step=50, value=1750, description=\"ELO B\"),",
        "         n_sims=widgets.IntSlider(min=10, max=10000, step=50, value=100, description=\"Sims\"));"
    ] if False else [ # wait, widgets is not defined in this scope yet, we need 'import ipywidgets as widgets'
        "import ipywidgets as widgets",
        "from ipywidgets import interact",
        "",
        "def run_simulation(elo_a, elo_b, n_sims):",
        "    results = [simulate_match(elo_a, elo_b) for _ in range(n_sims)]",
        "    wins_a = results.count(\"Team A\")",
        "    pct_a = (wins_a / n_sims) * 100",
        "    ",
        "    print(f\"Bei {n_sims} Simulationen:\")",
        "    print(f\"  Team A gewinnt: {wins_a} Mal ({pct_a:.2f}%)\")",
        "    print(f\"  Team B gewinnt: {n_sims - wins_a} Mal ({100 - pct_a:.2f}%)\")",
        "    print(f\"  Ziel-Wahrscheinlichkeit: {win_probability(elo_a, elo_b)*100:.2f}%\")",
        "",
        "interact(run_simulation, ",
        "         elo_a=widgets.IntSlider(min=1200, max=2200, step=50, value=1900, description=\"ELO A\"),",
        "         elo_b=widgets.IntSlider(min=1200, max=2200, step=50, value=1750, description=\"ELO B\"),",
        "         n_sims=widgets.IntSlider(min=10, max=10000, step=50, value=100, description=\"Sims\"));"
    ]),
    markdown_cell([
        "### Schritt 4: Turniersimulation auf dem Server",
        "Unser MCP-Server simuliert nicht nur ein Spiel, sondern den gesamten WM-Spielplan inklusive Gruppenphase, Tordifferenz-Tiebreakern, K.o.-Runden und dem Finale.",
        "Rufen wir das Tool erneut auf und testen, wie die Ergebnisse variieren."
    ]),
    code_cell([
        "import httpx",
        "MCP_URL = \"http://localhost:9000\"",
        "",
        "def get_simulation(n_sims):",
        "    response = httpx.post(f\"{MCP_URL}/call\", json={",
        "        \"tool\": \"simulate_tournament\",",
        "        \"parameters\": {\"team\": \"Deutschland\", \"n_sims\": n_sims}",
        "    })",
        "    return response.json().get(\"result\", {})",
        "",
        "print(\"=== 10 Simulationen ===\")",
        "print(get_simulation(10).get(\"summary\"))",
        "print(\"\\n=== 5000 Simulationen ===\")",
        "print(get_simulation(5000).get(\"summary\"))"
    ]),
    markdown_cell([
        "### 🧠 Aufgabe für dich:",
        "Welchen Einfluss hat der Heimvorteil? Simuliere das Turnier für die **USA** (Co-Gastgeber) einmal mit `home_boost=0` und einmal mit `home_boost=150` (jeweils 5000 Simulationen). Vergleiche die Titelchancen."
    ]),
    code_cell([
        "# DEINE LÖSUNG HIER:",
        "usa_no_boost = httpx.post(f\"{MCP_URL}/call\", json={",
        "    \"tool\": \"simulate_tournament\",",
        "    \"parameters\": {\"team\": \"USA\", \"n_sims\": 5000, \"home_boost\": 0}",
        "}).json().get(\"result\", {})",
        "",
        "usa_with_boost = httpx.post(f\"{MCP_URL}/call\", json={",
        "    \"tool\": \"simulate_tournament\",",
        "    \"parameters\": {\"team\": \"USA\", \"n_sims\": 5000, \"home_boost\": 150}",
        "}).json().get(\"result\", {})",
        "",
        "print(\"Ohne Heimvorteil:\", usa_no_boost.get(\"summary\"))",
        "print(\"Mit Heimvorteil (Boost +150 ELO):\", usa_with_boost.get(\"summary\"))"
    ])
]

# ---------------------------------------------------------------------------
# Notebook 3: 03_rag_intro.ipynb
# ---------------------------------------------------------------------------
cells_03 = [
    markdown_cell([
        "# 🗄️ Workshop: Bau deinen eigenen WM-Experten 2026",
        "## Notebook 3: Einführung in RAG (Retrieval-Augmented Generation)",
        "",
        "Große Sprachmodelle (LLMs) wie ChatGPT wissen nicht alles. Sie kennen keine Echtzeitdaten und keine internen Dokumente. Wenn wir sie nach der WM 2026 fragen, fangen sie an zu halluzinieren (sie erfinden Fakten).",
        "",
        "**RAG (Retrieval-Augmented Generation)** löst dieses Problem in drei Schritten:",
        "1. **Suchen (Retrieval):** Bei einer Benutzerfrage suchen wir in einer eigenen Datenbank nach relevanten Textabschnitten (Chunks).",
        "2. **Erweitern (Augment):** Wir fügen diese Textabschnitte in den Prompt für das LLM ein.",
        "3. **Generieren (Generation):** Das LLM antwortet basierend auf dem mitgelieferten Wissen.",
        "",
        "In diesem Notebook erstellen wir eine Vektordatenbank und füttern sie mit unseren WM-2026-Fakten.",
        "",
        "### Lernziele:",
        "1. Laden und Verstehen von Text-Chunks.",
        "2. Vektorisieren von Texten (Embeddings) über das LiteLLM-Gateway.",
        "3. Speichern und Abfragen von Vektoren in ChromaDB."
    ]),
    markdown_cell([
        "### Schritt 1: WM-Chunks laden",
        "Die Datenpipeline hat bereits aus Spielplänen, ELO-Tabellen und Trivia-Dateien natürlichsprachliche Textblöcke (Chunks) generiert und in `data-pipeline/data/chunks.json` gespeichert. Wir laden diese nun."
    ]),
    code_cell([
        "import json",
        "from pathlib import Path",
        "",
        "chunks_path = Path(\"../data-pipeline/data/chunks.json\")",
        "with open(chunks_path, encoding=\"utf-8\") as f:",
        "    chunks = json.load(f)",
        "",
        "print(f" + 'f"✅ {len(chunks)} Text-Chunks geladen."' + ")",
        "print(\"Beispiel-Chunk:\")",
        "print(json.dumps(chunks[5], indent=2, ensure_ascii=False))"
    ]),
    markdown_cell([
        "### Schritt 2: Embeddings erstellen",
        "Ein Embedding ist eine Liste von Zahlen (ein Vektor), die die semantische Bedeutung eines Textes beschreibt. Ähnliche Texte haben ähnliche Vektoren. Wir nutzen das LiteLLM-Gateway, um diese Vektoren zu erzeugen."
    ]),
    code_cell([
        "import os",
        "from openai import OpenAI",
        "from dotenv import load_dotenv",
        "",
        "load_dotenv()",
        "",
        "# LiteLLM Gateway einrichten (nutzt standardmäßig die Umgebungsvariablen)",
        "LITELLM_URL = os.environ.get(\"OPENAI_BASE_URL\", \"http://localhost:4000\")",
        "LITELLM_KEY = os.environ.get(\"OPENAI_API_KEY\", \"dummy\")",
        "",
        "client = OpenAI(base_url=LITELLM_URL, api_key=LITELLM_KEY)",
        "",
        "# Text in Vektor umwandeln",
        "response = client.embeddings.create(",
        "    model=\"text-embedding-3-small\",",
        "    input=[\"Deutschland spielt in Gruppe E gegen Japan.\"]",
        ")",
        "vector = response.data[0].embedding",
        "",
        "print(f\"Vektordimension: {len(vector)}\")",
        "print(f\"Erste 10 Werte: {vector[:10]}\")"
    ]),
    markdown_cell([
        "### Schritt 3: Ingestion in ChromaDB",
        "ChromaDB ist eine schnelle, leichtgewichtige Vektordatenbank. Wir erstellen eine Collection und fügen einige Chunks mitsamt ihren Embeddings und Metadaten ein."
    ]),
    code_cell([
        "import chromadb",
        "",
        "CHROMA_HOST = os.environ.get(\"CHROMA_HOST\", \"localhost\")",
        "CHROMA_PORT = int(os.environ.get(\"CHROMA_PORT\", 8000))",
        "",
        "try:",
        "    # Versuch, mit dem Docker-Chroma-Server zu verbinden",
        "    chroma_client = chromadb.HttpClient(host=CHROMA_HOST, port=CHROMA_PORT)",
        "    print(f\"ChromaDB: Verbunden mit {CHROMA_HOST}:{CHROMA_PORT}\")",
        "except Exception:",
        "    # Fallback auf lokale, dateibasierte ChromaDB",
        "    chroma_client = chromadb.PersistentClient(path=\"./chroma_db_local\")",
        "    print(\"ChromaDB: Nutze lokalen Speicherpfad (PersistentClient)\")",
        "",
        "collection_name = \"wm2026_student\"",
        "try:",
        "    chroma_client.delete_collection(collection_name)",
        "except Exception:",
        "    pass",
        "",
        "collection = chroma_client.create_collection(",
        "    name=collection_name,",
        "    metadata={\"hnsw:space\": \"cosine\"}",
        ")"
    ]),
    code_cell([
        "# Wir speichern die ersten 50 Chunks in unserer Datenbank",
        "subset_chunks = chunks[:50]",
        "",
        "texts = [c[\"text\"] for c in subset_chunks]",
        "ids = [c[\"chunk_id\"] for c in subset_chunks]",
        "metadatas = [{",
        "    \"source\": c[\"source\"],",
        "    \"data_type\": c[\"data_type\"],",
        "    \"team\": c[\"team\"]",
        "} for c in subset_chunks]",
        "",
        "print(\"Erzeuge Embeddings für Datenbank...\")",
        "emb_response = client.embeddings.create(",
        "    model=\"text-embedding-3-small\",",
        "    input=texts",
        ")",
        "embeddings = [item.embedding for item in emb_response.data]",
        "",
        "print(\"Speichere in ChromaDB...\")",
        "collection.add(",
        "    ids=ids,",
        "    documents=texts,",
        "    embeddings=embeddings,",
        "    metadatas=metadatas",
        ")",
        "print(\"Fertig!\")"
    ]),
    markdown_cell([
        "### Schritt 4: Semantische Suche (Retrieval)",
        "Wir können nun Fragen stellen. Die Datenbank vergleicht den Vektor der Frage mit allen Vektoren der Chunks und gibt uns die inhaltlich ähnlichsten Texte zurück."
    ]),
    code_cell([
        "frage = \"Wer sind die Gastgeber der Weltmeisterschaft 2026?\"",
        "",
        "# 1. Frage einbetten",
        "frage_emb = client.embeddings.create(",
        "    model=\"text-embedding-3-small\",",
        "    input=[frage]",
        ").data[0].embedding",
        "",
        "# 2. Vektorsuche in ChromaDB",
        "results = collection.query(",
        "    query_embeddings=[frage_emb],",
        "    n_results=2",
        ")",
        "",
        "print(\"Suchergebnisse für:\", frage)",
        "for doc, meta, distance in zip(results[\"documents\"][0], results[\"metadatas\"][0], results[\"distances\"][0]):",
        "    print(f\"\\n[Abstand: {distance:.4f} - Quelle: {meta[\'source\']}]\")",
        "    print(doc)"
    ]),
    markdown_cell([
        "### 🧠 Aufgabe für dich:",
        "Führe eine Suche nach der Frage: *\"In welchem Stadion wird das Finale ausgetragen?\"* durch. Gebe das beste Ergebnis aus."
    ]),
    code_cell([
        "# DEINE LÖSUNG HIER:",
        "frage_finale = \"In welchem Stadion wird das Finale ausgetragen?\"",
        "frage_finale_emb = client.embeddings.create(model=\"text-embedding-3-small\", input=[frage_finale]).data[0].embedding",
        "res_finale = collection.query(query_embeddings=[frage_finale_emb], n_results=1)",
        "print(res_finale[\"documents\"][0][0])"
    ])
]

# ---------------------------------------------------------------------------
# Notebook 4: 04_soccer_agent.ipynb
# ---------------------------------------------------------------------------
cells_04 = [
    markdown_cell([
        "# 🤖 Workshop: Bau deinen eigenen WM-Experten 2026",
        "## Notebook 4: Bau deines Fußball-Experten-Agenten",
        "",
        "Ein **KI-Agent** ist mehr als ein einfacher Chatbot. Er kann selbstständig entscheiden, welche Aktionen er ausführt. Er überlegt, welche Informationen er braucht, ruft die passenden Tools oder Datenbanken ab und formuliert daraus eine schlüssige Antwort.",
        "",
        "In diesem finalen Notebook bauen wir einen voll funktionsfähigen **ReAct-Agenten** (Reasoning & Action). Der Agent kann selbst entscheiden, ob er in unserer RAG-Datenbank nachliest (für Trivia und Spielpläne) oder den MCP-Server fragt (für ELO-Ratings und Wahrscheinlichkeiten).",
        "",
        "### Lernziele:",
        "1. Aufbau eines Agenten-Loops mit Funktions-Aufrufen (Function Calling).",
        "2. Verknüpfung von RAG (Wissensdatenbank) und Live-Tools (MCP).",
        "3. Testen des Agenten mit komplexen Fragestellungen."
    ]),
    markdown_cell([
        "### Schritt 1: Initialisierung",
        "Wir verbinden uns mit ChromaDB (wo die fertige Collection `wm2026` der Pipeline liegt) und stellen die Clients bereit."
    ]),
    code_cell([
        "import os",
        "import json",
        "import httpx",
        "import chromadb",
        "from openai import OpenAI",
        "from dotenv import load_dotenv",
        "",
        "load_dotenv()",
        "",
        "client = OpenAI(",
        "    base_url=os.environ.get(\"OPENAI_BASE_URL\", \"http://localhost:4000\"),",
        "    api_key=os.environ.get(\"OPENAI_API_KEY\", \"dummy\")",
        ")",
        "",
        "CHROMA_HOST = os.environ.get(\"CHROMA_HOST\", \"localhost\")",
        "CHROMA_PORT = int(os.environ.get(\"CHROMA_PORT\", 8000))",
        "MCP_URL = \"http://localhost:9000\"",
        "",
        "try:",
        "    chroma_client = chromadb.HttpClient(host=CHROMA_HOST, port=CHROMA_PORT)",
        "    # Wir nutzen die von der Pipeline befüllte Haupt-Collection",
        "    collection = chroma_client.get_collection(\"wm2026\")",
        "    print(\"✅ Erfolgreich mit globaler Vektordatenbank verbunden.\")",
        "except Exception as e:",
        "    print(\"❌ Verbindung zur globalen ChromaDB fehlgeschlagen. Nutze Fallback...\", e)",
        "    chroma_client = chromadb.PersistentClient(path=\"../data-pipeline/data/chroma\")",
        "    collection = chroma_client.get_collection(\"wm2026\")"
    ]),
    markdown_cell([
        "### Schritt 2: Hilfsfunktionen für Tools & RAG",
        "Wir definieren die Aktionen, die unser Agent ausführen kann."
    ]),
    code_cell([
        "def query_rag_database(query: str) -> str:",
        "    \"\"\"Sucht in der Vektordatenbank nach historischen Fakten.\"\"\"",
        "    query_emb = client.embeddings.create(",
        "        model=\"text-embedding-3-small\",",
        "        input=[query]",
        "    ).data[0].embedding",
        "    ",
        "    results = collection.query(query_embeddings=[query_emb], n_results=3)",
        "    docs = results[\"documents\"][0]",
        "    return \"\\n\\n\".join(docs)",
        "",
        "def call_mcp_tool(tool_name: str, parameters: dict) -> str:",
        "    \"\"\"Ruft das passende Tool vom MCP-Server ab.\"\"\"",
        "    response = httpx.post(f\"{MCP_URL}/call\", json={\"tool\": tool_name, \"parameters\": parameters})",
        "    if response.status_code != 200:",
        "        return f\"Fehler im Tool: {response.text}\"",
        "    result = response.json().get(\"result\", {})",
        "    return json.dumps(result, ensure_ascii=False)",
        "",
        "# Teste die RAG-Suche",
        "print(query_rag_database(\"Wer ist Rekordweltmeister?\"))"
    ]),
    markdown_cell([
        "### Schritt 3: Tool-Definitionen für das LLM",
        "Wir beschreiben dem LLM die verfügbaren Funktionen im OpenAI-Format. Das LLM entscheidet anhand der Beschreibungen, welches Tool es nutzen möchte."
    ]),
    code_cell([
        "tools_schema = [",
        "    {",
        "        \"type\": \"function\",",
        "        \"function\": {",
        "            \"name\": \"query_rag_database\",",
        "            \"description\": \"Sucht in der WM-Datenbank nach Fakten, Historie, Trivia und Spielort-Infos.\",",
        "            \"parameters\": {",
        "                \"type\": \"object\",",
        "                \"properties\": {",
        "                    \"query\": {\"type\": \"string\", \"description\": \"Suchanfrage\"}",
        "                },",
        "                \"required\": [\"query\"]",
        "            }",
        "        }",
        "    },",
        "    {",
        "        \"type\": \"function\",",
        "        \"function\": {",
        "            \"name\": \"get_team_elo\",",
        "            \"description\": \"Gibt ELO-Rating, Weltrang und historische Statistiken zu einem Team zurück.\",",
        "            \"parameters\": {",
        "                \"type\": \"object\",",
        "                \"properties\": {",
        "                    \"team\": {\"type\": \"string\", \"description\": \"Teamname (z.B. Deutschland)\"}",
        "                },",
        "                \"required\": [\"team\"]",
        "            }",
        "        }",
        "    },",
        "    {",
        "        \"type\": \"function\",",
        "        \"function\": {",
        "            \"name\": \"simulate_tournament\",",
        "            \"description\": \"Simuliert das WM-Turnier per Monte-Carlo. Gibt die Chancen für das Team an.\",",
        "            \"parameters\": {",
        "                \"type\": \"object\",",
        "                \"properties\": {",
        "                    \"team\": {\"type\": \"string\", \"description\": \"Teamname für Detailbericht\"},",
        "                    \"n_sims\": {\"type\": \"integer\", \"description\": \"Anzahl Simulationen (Standard: 1000)\"}",
        "                }",
        "            }",
        "        }",
        "    },",
        "    {",
        "        \"type\": \"function\",",
        "        \"function\": {",
        "            \"name\": \"search_news\",",
        "            \"description\": \"Sucht aktuelle Nachrichten zur WM 2026 über DuckDuckGo.\",",
        "            \"parameters\": {",
        "                \"type\": \"object\",",
        "                \"properties\": {",
        "                    \"query\": {\"type\": \"string\", \"description\": \"Suchanfrage\"}",
        "                },",
        "                \"required\": [\"query\"]",
        "            }",
        "        }",
        "    }",
        "]"
    ]),
    markdown_cell([
        "### Schritt 4: Der Agenten-Loop (ReAct)",
        "Wir implementieren den Loop. Wenn das Sprachmodell einen Tool-Aufruf anfordert, führen wir diesen aus, hängen das Ergebnis an den Verlauf an und rufen das Modell erneut auf."
    ]),
    code_cell([
        "def run_agent(question: str) -> str:",
        "    print(f\"Frage: {question}\")",
        "    messages = [",
        "        {",
        "            \"role\": \"system\",",
        "            \"content\": \"Du bist ein fußballbegeisterter WM-Experten-Agent. Beantworte alle Fragen präzise und faktenbasiert auf Deutsch. Nutze deine Tools! Wenn eine Frage historische Infos betrifft, nutze query_rag_database. Wenn es um ELO-Ratings oder Wahrscheinlichkeiten geht, nutze get_team_elo oder simulate_tournament.\"",
        "        },",
        "        {\"role\": \"user\", \"content\": question}",
        "    ]",
        "    ",
        "    # 1. Anfrage ans LLM",
        "    response = client.chat.completions.create(",
        "        model=\"gpt-4o\",  # LiteLLM leitet dies an das konfigurierte Modell weiter",
        "        messages=messages,",
        "        tools=tools_schema,",
        "        tool_choice=\"auto\"",
        "    )",
        "    ",
        "    response_message = response.choices[0].message",
        "    tool_calls = response_message.tool_calls",
        "    ",
        "    if tool_calls:",
        "        print(\"🤖 Agent überlegt und entscheidet sich für Tool-Nutzung...\")",
        "        messages.append(response_message)",
        "        ",
        "        for tool_call in tool_calls:",
        "            func_name = tool_call.function.name",
        "            func_args = json.loads(tool_call.function.arguments)",
        "            ",
        "            print(f\"  → Tool aufrufen: '{func_name}' mit Parameter {func_args}\")",
        "            ",
        "            if func_name == \"query_rag_database\":",
        "                result_str = query_rag_database(func_args[\"query\"])",
        "            else:",
        "                result_str = call_mcp_tool(func_name, func_args)",
        "                ",
        "            messages.append({",
        "                \"role\": \"tool\",",
        "                \"tool_call_id\": tool_call.id,",
        "                \"name\": func_name,",
        "                \"content\": result_str",
        "            })",
        "        ",
        "        # 2. Zweite Anfrage ans LLM mit den Tool-Ergebnissen",
        "        final_response = client.chat.completions.create(",
        "            model=\"gpt-4o\",",
        "            messages=messages",
        "        )",
        "        return final_response.choices[0].message.content",
        "    else:",
        "        return response_message.content"
    ]),
    markdown_cell([
        "### Schritt 5: Agenten testen!",
        "Stellen wir unserem Agenten nun eine komplexe Frage, die sowohl statisches Wissen als auch aktuelle Simulationen benötigt."
    ]),
    code_cell([
        "agenten_antwort = run_agent(",
        "    \"Wer spielt in Gruppe E und wie hoch ist die Wahrscheinlichkeit, dass der ELO-Favorit dieser Gruppe die WM gewinnt?\"",
        ")",
        "print(\"\\n=== Antwort des Agenten ===\")",
        "print(agenten_antwort)"
    ]),
    markdown_cell([
        "### 🏆 Herzlichen Glückwunsch!",
        "Du hast erfolgreich einen KI-Agenten gebaut, der RAG und Live-Tools kombiniert, um echte Fußball-Prognosen zu erstellen! Du kannst nun im Chat oder in JupyterLab weitere Fragen ausprobieren."
    ])
]

def main():
    notebooks_dir = Path("/home/cgawron/git/soccer-agent/notebooks")
    notebooks_dir.mkdir(exist_ok=True)

    # Notebook 1
    n1 = make_notebook(cells_01)
    with open(notebooks_dir / "01_mcp_client.ipynb", "w", encoding="utf-8") as f:
        json.dump(n1, f, ensure_ascii=False, indent=2)
    print("Notebook 1 generiert.")

    # Notebook 2
    n2 = make_notebook(cells_02)
    with open(notebooks_dir / "02_monte_carlo.ipynb", "w", encoding="utf-8") as f:
        json.dump(n2, f, ensure_ascii=False, indent=2)
    print("Notebook 2 generiert.")

    # Notebook 3
    n3 = make_notebook(cells_03)
    with open(notebooks_dir / "03_rag_intro.ipynb", "w", encoding="utf-8") as f:
        json.dump(n3, f, ensure_ascii=False, indent=2)
    print("Notebook 3 generiert.")

    # Notebook 4
    n4 = make_notebook(cells_04)
    with open(notebooks_dir / "04_soccer_agent.ipynb", "w", encoding="utf-8") as f:
        json.dump(n4, f, ensure_ascii=False, indent=2)
    print("Notebook 4 generiert.")

if __name__ == "__main__":
    main()
