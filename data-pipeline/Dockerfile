# ================================================================
# Dockerfile — Datenpipeline
# Einmaliger Job: Daten laden, bereinigen, in Vektordatenbank speichern
#
# Aufruf:
#   docker build -f data-pipeline/Dockerfile -t wm2026-pipeline .
#   docker run --env-file .env \
#     -v wm2026-chroma:/app/data-pipeline/data/chroma \
#     wm2026-pipeline
# ================================================================

FROM python:3.12-slim

WORKDIR /app

# uv installieren (schnelles Python-Paketmanagement)
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

COPY pyproject.toml .
RUN --mount=type=cache,target=/root/.cache/uv \
    uv pip install --system -r pyproject.toml

# Quellcode
COPY data-pipeline/ ./data-pipeline/

# Datenpfad
VOLUME ["/app/data-pipeline/data/chroma"]

# Standardbefehl: Komplette Pipeline (fetch → scrape → clean → ingest)
# Einzelne Schritte über CMD überschreiben:
#   docker run ... wm2026-pipeline python3 data-pipeline/fetch_elo.py
CMD ["sh", "-c", \
     "python3 data-pipeline/fetch_elo.py && \
      python3 data-pipeline/fetch_fixtures.py && \
      python3 data-pipeline/scrape_news.py && \
      python3 data-pipeline/clean.py && \
      python3 data-pipeline/ingest.py"]
