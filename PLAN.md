# Implementation Plan: KI-Trainer 2026 soccer-agent Workshop

This plan covers the implementation of the infrastructure, educational notebooks, Langflow integrations, and Kubernetes deployment manifests for the high school student workshop "KI-Trainer 2026: Bau deinen eigenen WM-Experten".

Students will work in JupyterLab and Langflow, using the provided MCP server tools and LiteLLM server to build RAG systems and soccer agents. All student-facing notebook materials will be written in German.

---

## Proposed Components & Changes

### 1. JupyterLab Notebooks (`notebooks/`)

We will create four step-by-step Jupyter Notebooks in **German**:

#### [NEW] [01_mcp_client.ipynb](file:///home/cgawron/git/soccer-agent/notebooks/01_mcp_client.ipynb)
- **Titel**: *01_mcp_client.ipynb — Verbindung zum MCP-Server & Tool-Aufrufe*
- **Ziel**: Einführung in das Model Context Protocol (MCP) und die Nutzung strukturierter Tools.
- **Inhalt**:
  - Konzept des Model Context Protocols (Client ↔ Server).
  - Abrufen der verfügbaren Tools des laufenden MCP-Servers (`get_team_elo`, `get_matches`, `simulate_tournament`, `search_news`).
  - Tool-Aufrufe über Python (`httpx` / API-Requests) programmieren und die Ergebnisse formatieren.

#### [NEW] [02_monte_carlo.ipynb](file:///home/cgawron/git/soccer-agent/notebooks/02_monte_carlo.ipynb)
- **Titel**: *02_monte_carlo.ipynb — Simulation der WM 2026 mit Monte-Carlo*
- **Ziel**: Mathematische und konzeptionelle Grundlagen der Monte-Carlo-Simulation verstehen.
- **Inhalt**:
  - Warum können wir Fußballspiele nicht exakt vorhersagen? (Zufall und Wahrscheinlichkeiten).
  - Funktionsweise der ELO-basierten Siegwahrscheinlichkeit.
  - Implementierung einer einfachen Simulation eines einzelnen Spiels.
  - Durchführung einer Monte-Carlo-Simulation für das gesamte Turnier (Gruppen- und K.o.-Phase) und Visualisierung der Wahrscheinlichkeiten (z.B. mittels `matplotlib` oder ASCII-Balken).
  - Einfluss von Parametern wie dem "Heimvorteil" (Home Boost) analysieren.

#### [NEW] [03_rag_intro.ipynb](file:///home/cgawron/git/soccer-agent/notebooks/03_rag_intro.ipynb)
- **Titel**: *03_rag_intro.ipynb — Einführung in RAG (Retrieval-Augmented Generation)*
- **Ziel**: Eigene WM-Daten (ELO, Spielpläne, Fun-Facts) in eine Vektordatenbank einspeichern und abfragen.
- **Inhalt**:
  - Das RAG-Konzept (Wissenserweiterung ohne Fine-Tuning).
  - Einlesen der vorbereiteten Daten-Chunks (`chunks.json`).
  - Erstellen von Text-Embeddings über das LiteLLM-Gateway.
  - Anlegen einer ChromaDB-Collection, Ingestion und semantische Suche (Vektor-Ähnlichkeitssuche).

#### [NEW] [04_soccer_agent.ipynb](file:///home/cgawron/git/soccer-agent/notebooks/04_soccer_agent.ipynb)
- **Titel**: *04_soccer_agent.ipynb — Bau deines Fußball-Experten-Agenten*
- **Ziel**: Kombination von RAG und MCP-Tools zu einem intelligenten Agenten.
- **Inhalt**:
  - Implementierung eines ReAct-artigen (Reasoning & Action) Agenten-Loops in Python.
  - System-Prompts, die dem LLM erklären, wann es die Vektordatenbank (für statisches Wissen/Trivia) und wann die MCP-Tools (für Berechnungen/Simulationen/aktuelle News) nutzen soll.
  - Testen des Agenten mit komplexen Fragen wie: *"Wer hat laut ELO-Rating die schwersten Gruppengegner und wie hoch ist die Wahrscheinlichkeit, dass dieses Team die K.o.-Runde erreicht?"*

---

### 2. Langflow Integration

To help students build agents visually, we will configure custom Langflow integrations:

#### [NEW] [mcp_tool_caller.py](file:///home/cgawron/git/soccer-agent/langflow-components/mcp_tool_caller.py)
- A custom Langflow Python component.
- Automatically connects to the MCP server `/tools` and `/call` endpoints.
- Displays tools dynamically in the Langflow UI, enabling drag-and-drop tool invocation.

#### [NEW] [wm_agent_flow.json](file:///home/cgawron/git/soccer-agent/langflow-flows/wm_agent_flow.json)
- A pre-configured Langflow JSON flow representing a RAG-enabled agent.
- Features: Chat input -> ChromaDB Retriever -> Prompt Template -> OpenAIChatModel (configured for LiteLLM) -> Chat Output.

---

### 3. Kubernetes Manifests (`k8s/`)

We will create standard declarative Kubernetes manifests to deploy the entire workshop ecosystem in a unified namespace.

#### [NEW] [kustomization.yaml](file:///home/cgawron/git/soccer-agent/k8s/kustomization.yaml)
- Orchestrates deployment of all resources in a single namespace.

#### [NEW] [litellm-configmap.yaml](file:///home/cgawron/git/soccer-agent/k8s/litellm-configmap.yaml)
- Configures LiteLLM proxy mapping generic model names to active API keys (e.g., Gemini API keys).

#### [NEW] [litellm-deployment.yaml](file:///home/cgawron/git/soccer-agent/k8s/litellm-deployment.yaml)
- LiteLLM server deployment and service.

#### [NEW] [chromadb-deployment.yaml](file:///home/cgawron/git/soccer-agent/k8s/chromadb-deployment.yaml)
- Deployment of a persistent ChromaDB container running in client-server mode, accessible by both the pipeline and students.

#### [NEW] [mcp-server-deployment.yaml](file:///home/cgawron/git/soccer-agent/k8s/mcp-server-deployment.yaml)
- Deployment for the FastAPI MCP server, mounting the data-pipeline data.

#### [NEW] [jupyterlab-deployment.yaml](file:///home/cgawron/git/soccer-agent/k8s/jupyterlab-deployment.yaml)
- JupyterLab server. Uses a custom Docker image, mounting the workshop repository.

#### [NEW] [langflow-deployment.yaml](file:///home/cgawron/git/soccer-agent/k8s/langflow-deployment.yaml)
- Langflow container deployment and service.

#### [NEW] [ingress.yaml](file:///home/cgawron/git/soccer-agent/k8s/ingress.yaml)
- Maps routing prefixes under a single Ingress (e.g., `/jupyter`, `/langflow`, `/mcp`, `/llm`) to simplify access for students.

---

## Verification Plan

### Automated/Local Tests
- Run each Jupyter notebook locally to verify imports, connections to LiteLLM, ChromaDB operations, and tool calls.
- Run `kubectl lint` or validate the K8s manifests using a dry-run against a local cluster (e.g., KinD or Minikube) if available.

### Manual Verification
- Verify that the MCP server starts correctly and `/tools` returns the correct JSON schema.
- Open JupyterLab and verify that the notebooks are rendered correctly and execute without syntax or dependency errors.
