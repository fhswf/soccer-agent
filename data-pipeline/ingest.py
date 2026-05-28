"""
ingest.py
=========
Bettet alle Chunks (aus clean.py) mit OpenAI text-embedding-3-small ein und
speichert sie in ChromaDB (primär) und optional Qdrant (sekundär).

Voraussetzungen:
  - OPENAI_API_KEY Umgebungsvariable gesetzt (oder in .env)
  - ChromaDB läuft auf chromadb:8000 (oder als embedded)
  - Qdrant läuft auf qdrant:6333 (optional)
  - data/chunks.json existiert (erst clean.py ausführen)

Aufruf:
  python ingest.py                    # ChromaDB + Qdrant
  python ingest.py --only-chroma      # nur ChromaDB
  OPENAI_BASE_URL=http://... python ingest.py  # LiteLLM-Gateway nutzen
"""

from __future__ import annotations

import argparse
import json
import os
import time
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

DATA_DIR = Path(__file__).parent / "data"

EMBEDDING_MODEL = "text-embedding-3-small"
COLLECTION_NAME = "wm2026"

# Batch-Größe für API-Aufrufe (OpenAI erlaubt bis zu 2048 Inputs pro Request)
BATCH_SIZE = 50


# ---------------------------------------------------------------------------
# OpenAI Embedding
# ---------------------------------------------------------------------------

def get_openai_client() -> OpenAI:
    """Erstellt einen OpenAI-Client (unterstützt auch LiteLLM-Gateway via OPENAI_BASE_URL)."""
    base_url = os.environ.get("OPENAI_BASE_URL")
    api_key = os.environ.get("OPENAI_API_KEY", "dummy")
    if base_url:
        print(f"Nutze LiteLLM-Gateway: {base_url}")
        return OpenAI(api_key=api_key, base_url=base_url)
    return OpenAI(api_key=api_key)


def embed_texts(client: OpenAI, texts: list[str]) -> list[list[float]]:
    """Bettet eine Liste von Texten ein und gibt die Vektoren zurück."""
    all_embeddings: list[list[float]] = []
    for i in range(0, len(texts), BATCH_SIZE):
        batch = texts[i : i + BATCH_SIZE]
        try:
            response = client.embeddings.create(model=EMBEDDING_MODEL, input=batch)
            embeddings = [item.embedding for item in response.data]
        except Exception as e:
            api_key = getattr(client, "api_key", "dummy")
            if "dummy" in str(api_key) or "dein" in str(api_key) or "401" in str(e):
                print(f"  [WARNUNG] OpenAI API-Key ungültig oder nicht gesetzt. Erstelle Dummy-Embeddings für {len(batch)} Texte. ({e})")
                embeddings = [[0.0] * 1536 for _ in batch]
            else:
                raise e
        all_embeddings.extend(embeddings)
        print(f"  Batch {i // BATCH_SIZE + 1}/{(len(texts) - 1) // BATCH_SIZE + 1} eingebettet ({len(batch)} Texte)")
        # Rate-Limit-Schutz
        time.sleep(0.1)
    return all_embeddings


# ---------------------------------------------------------------------------
# ChromaDB
# ---------------------------------------------------------------------------

def ingest_chroma(chunks: list[dict], embeddings: list[list[float]]) -> None:
    """Speichert Chunks + Embeddings in ChromaDB."""
    try:
        import chromadb
    except ImportError:
        print("ChromaDB nicht installiert: pip install chromadb")
        return

    chroma_host = os.environ.get("CHROMA_HOST", "chromadb")
    chroma_port = int(os.environ.get("CHROMA_PORT", "8000"))

    try:
        client = chromadb.HttpClient(host=chroma_host, port=chroma_port)
        print(f"ChromaDB: Verbunden mit {chroma_host}:{chroma_port}")
    except Exception:
        # Fallback: Embedded ChromaDB (lokal gespeichert)
        chroma_dir = DATA_DIR / "chroma"
        chroma_dir.mkdir(exist_ok=True)
        client = chromadb.PersistentClient(path=str(chroma_dir))
        print(f"ChromaDB: Embedded-Modus (Pfad: {chroma_dir})")

    # Collection löschen und neu erstellen (idempotent)
    try:
        client.delete_collection(COLLECTION_NAME)
        print(f"  Alte Collection '{COLLECTION_NAME}' gelöscht.")
    except Exception:
        pass

    collection = client.create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )

    # In Batches einfügen
    ids = [c["chunk_id"] for c in chunks]
    documents = [c["text"] for c in chunks]
    metadatas = [
        {k: v for k, v in c.items() if k not in ("text", "chunk_id") and isinstance(v, (str, int, float, bool))}
        for c in chunks
    ]

    for i in range(0, len(chunks), BATCH_SIZE):
        collection.add(
            ids=ids[i : i + BATCH_SIZE],
            documents=documents[i : i + BATCH_SIZE],
            embeddings=embeddings[i : i + BATCH_SIZE],
            metadatas=metadatas[i : i + BATCH_SIZE],
        )
    print(f"  → {len(chunks)} Chunks in ChromaDB Collection '{COLLECTION_NAME}' gespeichert.")


# ---------------------------------------------------------------------------
# Qdrant
# ---------------------------------------------------------------------------

def ingest_qdrant(chunks: list[dict], embeddings: list[list[float]]) -> None:
    """Speichert Chunks + Embeddings in Qdrant."""
    try:
        from qdrant_client import QdrantClient
        from qdrant_client.models import Distance, VectorParams, PointStruct
    except ImportError:
        print("Qdrant-Client nicht installiert: pip install qdrant-client")
        return

    qdrant_host = os.environ.get("QDRANT_HOST", "qdrant")
    qdrant_port = int(os.environ.get("QDRANT_PORT", "6333"))
    vector_size = len(embeddings[0])

    try:
        client = QdrantClient(host=qdrant_host, port=qdrant_port)
        client.get_collections()  # Verbindungstest
        print(f"Qdrant: Verbunden mit {qdrant_host}:{qdrant_port}")
    except Exception as e:
        print(f"Qdrant nicht erreichbar ({e}) – übersprungen.")
        return

    # Collection neu erstellen
    if client.collection_exists(COLLECTION_NAME):
        client.delete_collection(COLLECTION_NAME)
    client.create_collection(
        collection_name=COLLECTION_NAME,
        vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE),
    )

    points = [
        PointStruct(
            id=i,
            vector=embeddings[i],
            payload={
                "chunk_id": chunks[i]["chunk_id"],
                "text": chunks[i]["text"],
                "source": chunks[i]["source"],
                "data_type": chunks[i]["data_type"],
                "team": chunks[i]["team"],
            },
        )
        for i in range(len(chunks))
    ]
    client.upsert(collection_name=COLLECTION_NAME, points=points)
    print(f"  → {len(chunks)} Chunks in Qdrant Collection '{COLLECTION_NAME}' gespeichert.")


# ---------------------------------------------------------------------------
# Hauptprogramm
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="WM-2026-Chunks in Vektordatenbanken einspeisen")
    parser.add_argument("--only-chroma", action="store_true", help="Nur ChromaDB befüllen")
    parser.add_argument("--only-qdrant", action="store_true", help="Nur Qdrant befüllen")
    parser.add_argument("--skip-embed", action="store_true",
                        help="Embeddings aus embeddings.json laden statt neu berechnen")
    args = parser.parse_args()

    # Chunks laden
    chunks_path = DATA_DIR / "chunks.json"
    if not chunks_path.exists():
        print("FEHLER: chunks.json nicht gefunden. Erst clean.py ausführen!")
        return
    with open(chunks_path, encoding="utf-8") as f:
        chunks = json.load(f)
    print(f"Geladene Chunks: {len(chunks)}")

    # Embeddings berechnen oder laden
    embed_path = DATA_DIR / "embeddings.json"
    if args.skip_embed and embed_path.exists():
        with open(embed_path, encoding="utf-8") as f:
            embeddings = json.load(f)
        print(f"Embeddings geladen: {len(embeddings)} Vektoren")
    else:
        client = get_openai_client()
        texts = [c["text"] for c in chunks]
        print(f"Erstelle Embeddings für {len(texts)} Texte mit {EMBEDDING_MODEL} …")
        embeddings = embed_texts(client, texts)
        # Cachen für Wiederverwendung
        with open(embed_path, "w") as f:
            json.dump(embeddings, f)
        print(f"Embeddings gecacht: {embed_path}")

    # Einspeichern
    if not args.only_qdrant:
        print("\n--- ChromaDB ---")
        ingest_chroma(chunks, embeddings)

    if not args.only_chroma:
        print("\n--- Qdrant ---")
        ingest_qdrant(chunks, embeddings)

    print("\n✅ Ingest abgeschlossen!")


if __name__ == "__main__":
    main()
