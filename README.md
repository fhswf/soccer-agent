<a href="https://www.ki.fh-swf.de/jupyterhub/hub/user-redirect/git-pull?profile=nlp-environment&repo=https%3A%2F%2Fgithub.com%2Ffhswf%2Fsoccer-agent.git&urlpath=lab%2Ftree%2Fsoccer-agent.git%2Fnotebooks&branch=main&profile=nlp-environment" style=""><img src="https://www.ki.fh-swf.de/cluster_badge.svg" style="height: 32px" alt="Open in FH Cluster"></a>


# KI-Trainer 2026: Bau deinen eigenen WM-Experten ⚽🤖

Willkommen im Repository zum Schul-Workshop **"KI-Trainer 2026: Bau deinen eigenen WM-Experten"**! 

In diesem praxisorientierten Workshop lernen Schülerinnen und Schüler, wie moderne Künstliche Intelligenz (KI) jenseits von einfachem Chatten funktioniert. Sie bauen einen eigenen intelligenten KI-Experten für die Fußball-Weltmeisterschaft 2026, der auf echte Daten zugreift, statistische Simulationen durchführt und aktuelle News recherchiert.

---

## 🚀 Die Kernkonzepte des Workshops

1. **RAG (Retrieval-Augmented Generation)**: Der Agent wird mit echten WM-Daten (Daten-Chunks in ChromaDB) gefüttert, damit er Fakten kennt, die ChatGPT & Co. mangels aktuellem Trainingsdatenstand nicht wissen können.
2. **Model Context Protocol (MCP)**: Die Schüler lernen, wie eine KI über standardisierte Schnittstellen (Tools) auf externe Daten und Rechenlogiken zugreifen kann.
3. **Monte-Carlo-Simulation**: Spielergebnisse werden mathematisch auf Basis von ELO-Ratings simuliert, um Turnierszenarien vorherzusagen.
4. **ReAct-Agenten-Loops**: Der Agent entscheidet eigenständig, ob er zur Beantwortung einer Frage die Wissensdatenbank (RAG) durchsuchen oder ein Berechnungs-Tool (MCP) ausführen muss.

---

## 📂 Repository-Struktur

```bash
├── .github/workflows/          # CI/CD Pipelines
│   ├── release-please.yml      # Automatisches Versionieren & Release-Changelogs
│   └── build-images.yml        # Docker-Build & Push an ghcr.io (FastAPI MCP-Server)
├── data-pipeline/              # Skripte zum Laden von ELO-Daten & Spielplänen
│   └── data/                   # JSON-Rohdaten für ELO, Teams und Spielpläne
├── k8s/                        # Kubernetes GitOps Manifeste (Kustomize)
│   ├── kustomization.yaml      # Orchestriert die K8s-Dienste
│   ├── chromadb-deployment.yaml# ChromaDB Vektordatenbank
│   ├── mcp-server-deployment.yaml # Der FastAPI-MCP-Server
│   ├── langflow-deployment.yaml# Visuelle KI-Pipeline (Langflow)
│   └── ingress.yaml            # Ingress-Routings für die Services
├── langflow-components/        # Eigene Python-Komponenten für Langflow
├── langflow-flows/             # Vorkonfigurierter RAG-Chatbot-Flow
├── mcp-server/                 # FastAPI MCP-Server mit ELO- & Simulations-Tools
│   ├── tools/                  # Implementierung der Python-Tools
│   ├── server.py               # Haupteinstiegspunkt mit MCP-Routes
│   └── logo.svg                # Das offizielle Logo des MCP-Servers
├── notebooks/                  # Deutschsprachige Jupyter-Notebooks für Schüler
│   ├── 01_mcp_client.ipynb     # MCP-Grundlagen & HTTP-Verbindung
│   ├── 02_monte_carlo.ipynb    # ELO-Wahrscheinlichkeiten & Turniersimulation
│   ├── 03_rag_intro.ipynb      # Dokumente einlesen & ChromaDB-Abfragen
│   └── 04_soccer_agent.ipynb   # Bau des fertigen ReAct-Entscheidungsagenten
├── argocd-app.yaml             # ArgoCD Application Bootstrapper (GitOps)
├── pyproject.toml              # Python-Projektkonfiguration (uv-kompatibel)
└── WALKTHROUGH.md              # Detaillierter technischer Walkthrough
```

---

## 🛠️ Lokale Einrichtung (Entwickler & Lehrer)

Das Projekt nutzt **[Astral uv](https://github.com/astral-sh/uv)** für extrem schnelles und einfaches Python-Paketmanagement.

### 1. Repository klonen & Abhängigkeiten installieren
```bash
git clone https://github.com/fhswf/soccer-agent.git
cd soccer-agent
uv sync
```

### 2. Datenpipeline initialisieren
Um ELO-Daten und WM-Spielpläne herunterzuladen/vorzubereiten:
```bash
uv run python cli.py ingest-data
```

### 3. MCP-Server lokal starten
Der MCP-Server stellt ELO-Abfragen und Simulationstools bereit:
```bash
cd mcp-server
uv run uvicorn server:app --host 127.0.0.1 --port 9000
```
Das offizielle Logo des Servers kann unter `http://127.0.0.1:9000/logo.svg` abgerufen werden.

---

## ☸️ K8s & GitOps Deployment (Infrastruktur)

Die Bereitstellung der Server-Komponenten (ChromaDB, Langflow, MCP-Server) erfolgt vollautomatisch über GitOps mit **ArgoCD**. Das System greift dabei auf ein externes LiteLLM-Gateway (`https://litellm.fh-swf.cloud/v1`) zu.

1. Stelle sicher, dass ArgoCD auf deinem Kubernetes-Cluster läuft.
2. Wende die Bootstrapping-Datei im Root-Verzeichnis an:
   ```bash
   kubectl apply -f argocd-app.yaml
   ```
3. ArgoCD synchronisiert daraufhin die Kustomize-Konfigurationen aus dem `k8s/` Ordner und erstellt alle Deployments im Namespace `soccer-agent`.

---

## 🤖 CI/CD Workflows

Dieses Repository nutzt automatisierte GitHub Actions für ein stabiles Deployment:

- **Release Please**: Erstellt bei standardisierten Commit-Nachrichten (Conventional Commits) automatisch Pull Requests mit Versions-Bumps in `pyproject.toml` und generiert Changelogs für neue Releases.
- **Docker Image Build**: Baut bei jedem Push auf den `main`-Branch oder bei neuen Release-Tags automatisch das Docker-Image des MCP-Servers und publiziert es auf der GitHub Container Registry:
  `ghcr.io/fhswf/soccer-agent/mcp-server:latest`
