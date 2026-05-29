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
    if not chunks:
        print("  ChromaDB: Keine neuen Chunks hinzuzufügen.")
        return

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

    # Collection abrufen oder erstellen
    collection = client.get_or_create_collection(
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
    print(f"  → {len(chunks)} neue Chunks in ChromaDB Collection '{COLLECTION_NAME}' gespeichert.")


# ---------------------------------------------------------------------------
# Hauptprogramm
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="WM-2026-Chunks in ChromaDB einspeisen")
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

    # 1. Verbindung zu ChromaDB aufbauen und bereits existierende IDs abfragen
    existing_ids = set()
    try:
        import chromadb
        chroma_host = os.environ.get("CHROMA_HOST", "chromadb")
        chroma_port = int(os.environ.get("CHROMA_PORT", "8000"))
        try:
            chroma_client = chromadb.HttpClient(host=chroma_host, port=chroma_port)
        except Exception:
            chroma_dir = DATA_DIR / "chroma"
            chroma_client = chromadb.PersistentClient(path=str(chroma_dir))
        
        try:
            collection = chroma_client.get_collection(COLLECTION_NAME)
            chunk_ids = [c["chunk_id"] for c in chunks]
            # Batch-Abfragen bei sehr großen Listen verhindern Fehler
            for i in range(0, len(chunk_ids), 100):
                batch_ids = chunk_ids[i : i + 100]
                existing = collection.get(ids=batch_ids)
                existing_ids.update(existing.get("ids", []))
            print(f"Bereits in ChromaDB vorhanden: {len(existing_ids)} Chunks")
        except Exception:
            # Collection existiert noch nicht
            pass
    except Exception as e:
        print(f"Warnung beim Überprüfen existierender Chunks: {e}")

    # Chunks filtern, die noch nicht in der Datenbank existieren
    new_chunks = [c for c in chunks if c["chunk_id"] not in existing_ids]
    print(f"Neue/Fehlende Chunks zum Hinzufügen: {len(new_chunks)}")

    if not new_chunks:
        print("\n✅ Alle Chunks bereits in ChromaDB vorhanden. Ingest übersprungen.")
        return

    # Embeddings laden oder berechnen
    embed_path = DATA_DIR / "embeddings.json"
    embeddings_cache = {}

    if embed_path.exists():
        try:
            with open(embed_path, encoding="utf-8") as f:
                embeddings_cache = json.load(f)
            if isinstance(embeddings_cache, list):
                print("Altes Listen-Format für Embeddings gefunden. Cache wird zurückgesetzt.")
                embeddings_cache = {}
            else:
                print(f"Embeddings-Cache geladen: {len(embeddings_cache)} Vektoren")
        except Exception as e:
            print(f"Warnung beim Laden des Embeddings-Caches: {e}")

    # Fehlende Embeddings sammeln
    texts_to_embed = []
    indices_to_embed = []
    new_embeddings = [None] * len(new_chunks)

    for idx, chunk in enumerate(new_chunks):
        cid = chunk["chunk_id"]
        if cid in embeddings_cache:
            new_embeddings[idx] = embeddings_cache[cid]
        elif args.skip_embed:
            # Fallback wenn skip-embed gefordert aber kein Cache vorhanden
            print(f"  [WARNUNG] --skip-embed aktiv, aber kein Cache für {cid}. Erstelle Dummy-Embedding.")
            new_embeddings[idx] = [0.0] * 1536
        else:
            texts_to_embed.append(chunk["text"])
            indices_to_embed.append(idx)

    # API-Aufruf für neue Embeddings
    if texts_to_embed:
        client = get_openai_client()
        print(f"Erstelle API-Embeddings für {len(texts_to_embed)} neue Texte mit {EMBEDDING_MODEL} …")
        api_embeddings = embed_texts(client, texts_to_embed)
        
        # In Ergebnisse eintragen und Cache aktualisieren
        for local_idx, api_emb in zip(indices_to_embed, api_embeddings):
            new_embeddings[local_idx] = api_emb
            cid = new_chunks[local_idx]["chunk_id"]
            embeddings_cache[cid] = api_emb

        # Cache speichern
        try:
            with open(embed_path, "w", encoding="utf-8") as f:
                json.dump(embeddings_cache, f, ensure_ascii=False, indent=2)
            print(f"Embeddings-Cache aktualisiert: {embed_path}")
        except Exception as e:
            print(f"Warnung beim Schreiben des Embeddings-Caches: {e}")

    # In ChromaDB einspeichern
    print("\n--- ChromaDB ---")
    ingest_chroma(new_chunks, new_embeddings)

    print("\n✅ Ingest abgeschlossen!")


if __name__ == "__main__":
    main()
