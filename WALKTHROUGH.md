# Walkthrough: Implementation of KI-Trainer 2026 soccer-agent Workshop

We have successfully implemented the infrastructure files, educational notebooks, Langflow nodes, and Kubernetes manifests for the "KI-Trainer 2026: Bau deinen eigenen WM-Experten" workshop.

---

## 1. JupyterLab Notebooks (in German)
Four pedagogical, step-by-step notebooks have been generated in [notebooks/](file:///home/cgawron/git/soccer-agent/notebooks/):

1. **[01_mcp_client.ipynb](file:///home/cgawron/git/soccer-agent/notebooks/01_mcp_client.ipynb)**
   - Introduces Model Context Protocol (MCP) clients and servers.
   - Shows how to programmatically query the `/tools` list and execute tools like `get_team_elo` or `simulate_tournament` using HTTP requests in Python.
2. **[02_monte_carlo.ipynb](file:///home/cgawron/git/soccer-agent/notebooks/02_monte_carlo.ipynb)**
   - Explains the mathematical concepts of Monte Carlo simulation.
   - Guides students through implementing ELO-based winning probability, simulating matches, running multiple iterations, and exploring the impact of Heimvorteil (Home Boost). Includes interactive sliders.
3. **[03_rag_intro.ipynb](file:///home/cgawron/git/soccer-agent/notebooks/03_rag_intro.ipynb)**
   - Explains Retrieval-Augmented Generation (RAG).
   - Shows how to read text chunks from `chunks.json`, convert them to embeddings via the LiteLLM Gateway, save them into ChromaDB, and perform semantic similarity queries.
4. **[04_soccer_agent.ipynb](file:///home/cgawron/git/soccer-agent/notebooks/04_soccer_agent.ipynb)**
   - Guides students through writing a fully functional ReAct (Reasoning & Action) agent.
   - Teaches how to formulate system prompts, structure tool schemas, orchestrate the LLM function-calling loop, and query both RAG database context and live MCP tools.

---

## 2. Langflow Integration
We added visual programming files in [langflow-components/](file:///home/cgawron/git/soccer-agent/langflow-components/) and [langflow-flows/](file:///home/cgawron/git/soccer-agent/langflow-flows/):

- **[mcp_tool_caller.py](file:///home/cgawron/git/soccer-agent/langflow-components/mcp_tool_caller.py)**: A custom Langflow Python component that automatically queries the MCP server's `/call` endpoint, formatting ELO stats, news searches, and simulations for display.
- **[wm_agent_flow.json](file:///home/cgawron/git/soccer-agent/langflow-flows/wm_agent_flow.json)**: A pre-configured RAG chat canvas connecting Chat Input -> ChromaDB Retriever -> Prompt Template -> OpenAIChatModel (via LiteLLM) -> Chat Output.

---

## 3. Kubernetes manifests (`k8s/`)
A complete declarative deployment pipeline has been created in [k8s/](file:///home/cgawron/git/soccer-agent/k8s/):

- **[kustomization.yaml](file:///home/cgawron/git/soccer-agent/k8s/kustomization.yaml)**: Orchestrates resources in the `soccer-agent` namespace.
- **[litellm-configmap.yaml](file:///home/cgawron/git/soccer-agent/k8s/litellm-configmap.yaml)** & **[litellm-deployment.yaml](file:///home/cgawron/git/soccer-agent/k8s/litellm-deployment.yaml)**: Deploys a LiteLLM proxy routing generic model requests to provider API keys.
- **[chromadb-deployment.yaml](file:///home/cgawron/git/soccer-agent/k8s/chromadb-deployment.yaml)**: Runs ChromaDB in client-server mode with a Persistent Volume.
- **[mcp-server-deployment.yaml](file:///home/cgawron/git/soccer-agent/k8s/mcp-server-deployment.yaml)**: Serves the FastAPI ELO, schedule, and tournament simulation tools (now configured to pull from `ghcr.io/fhswf/soccer-agent/mcp-server:latest`).
- **[langflow-deployment.yaml](file:///home/cgawron/git/soccer-agent/k8s/langflow-deployment.yaml)**: Runs Langflow with SQLite database persistence.
- **[ingress.yaml](file:///home/cgawron/git/soccer-agent/k8s/ingress.yaml)**: Maps ingress rules under subpaths (with `/jupyter` removed as JupyterLab is hosted separately).
- **[argocd-app.yaml](file:///home/cgawron/git/soccer-agent/argocd-app.yaml)**: An ArgoCD Application manifest for automated GitOps deployment targeting the `fhswf` GitHub organization.

---

## 4. CI/CD & Automated Release Management
To support automated integration, we added the following files at the repository root:

- **[.github/workflows/release-please.yml](file:///home/cgawron/git/soccer-agent/.github/workflows/release-please.yml)**: Runs Google's `release-please-action` to parse conventional commits, generate a changelog, bump the version in `pyproject.toml`, and handle GitHub releases automatically.
- **[.github/workflows/build-images.yml](file:///home/cgawron/git/soccer-agent/.github/workflows/build-images.yml)**: Rebuilds and pushes the MCP Server Docker image to `ghcr.io/fhswf/soccer-agent/mcp-server` whenever commits are pushed to `main` or new releases are tagged.
- **[release-please-config.json](file:///home/cgawron/git/soccer-agent/release-please-config.json)** & **[.release-please-manifest.json](file:///home/cgawron/git/soccer-agent/.release-please-manifest.json)**: Configuration and version manifest files for managing standard Python releases via `release-please`.

---

## 5. Visual Branding & Server Logo
We added branding for the MCP server:
- **[logo.svg](file:///home/cgawron/git/soccer-agent/mcp-server/logo.svg)**: A beautiful geometric vector logo combining a cybernetic soccer ball pattern with neural-network nodes.
- **FastAPI Logo Endpoint**: Added a new route at `/logo.svg` in [server.py](file:///home/cgawron/git/soccer-agent/mcp-server/server.py) to dynamically serve this SVG image to user interfaces.

---

## Verification & Testing Results

- **Data Pipeline Verification**: Verified that ELO data and fixtures are correctly parsed and loaded.
- **Tool Verification**: Successfully ran a test script that validates the python tool implementation for `get_team_elo`, `get_matches`, and the Monte Carlo `simulate_tournament` logic.
- **YAML Validation**: Verified that all YAML manifests (`argocd-app.yaml`, `k8s/` files, and `.github/` workflows) are syntactically valid and pass YAML validation parser checks.
- **FastAPI /logo.svg Route**: Tested the FastAPI server locally, confirming `/logo.svg` is registered and correctly returns the SVG vector graphic.

