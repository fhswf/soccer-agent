# ================================================================
# Dockerfile — MCP-Server
# Dauerhaft laufender Dienst, der WM-Tools via HTTP bereitstellt
#
# Aufruf:
#   docker build -f mcp-server/Dockerfile -t wm2026-mcp .
#   docker run -p 9000:9000 \
#     -v /pfad/zu/data-pipeline/data:/app/data-pipeline/data:ro \
#     wm2026-mcp
# ================================================================

FROM python:3.12-slim

WORKDIR /app

# uv installieren
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Abhängigkeiten (Layer-Caching)
COPY pyproject.toml .
RUN uv pip install --system --no-cache -r pyproject.toml

# Quellcode
COPY mcp-server/ ./mcp-server/
# Datendateien (read-only mount in docker run, hier als COPY-Fallback)
COPY data-pipeline/data/ ./data-pipeline/data/

WORKDIR /app/mcp-server

ENV DATA_DIR=/app/data-pipeline/data
ENV PORT=9000

EXPOSE 9000

HEALTHCHECK --interval=30s --timeout=5s \
  CMD curl -f http://localhost:9000/health || exit 1

CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "9000"]
