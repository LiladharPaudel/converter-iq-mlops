"""Stage 3: load embeddings into ChromaDB, and query it.

One collection per chunking method, named converter-faults-<method>, so the
methods can be compared side by side.
"""
import json
import os
import time
import chromadb
from .config import CHROMADB_HOST, CHROMADB_PORT, COLLECTION_PREFIX, OUTPUT_DIR, DEFAULT_METHOD
from .embedder import embed_query
from .logger import get_logger


def get_client() -> chromadb.HttpClient:
    # Read env at call time so tests and compose overrides take effect without a reimport.
    host = os.getenv("CHROMADB_HOST", CHROMADB_HOST)
    port = int(os.getenv("CHROMADB_PORT", CHROMADB_PORT))
    return chromadb.HttpClient(host=host, port=port)


def collection_name(method: str) -> str:
    return f"{COLLECTION_PREFIX}-{method}"


def run_load(method: str, batch_size: int = 200) -> None:
    log = get_logger(f"load-{method}")
    client = get_client()
    name = collection_name(method)

    # Rebuild from scratch so the collection mirrors the embeddings file exactly.
    try:
        client.delete_collection(name)
        log.info("dropped existing collection %s", name)
    except Exception:
        pass
    col = client.create_collection(name=name, metadata={"hnsw:space": "cosine"})

    in_path = OUTPUT_DIR / f"embeddings-{method}.jsonl"
    records = [json.loads(l) for l in in_path.open()]
    log.info("loaded %d records from %s", len(records), in_path)

    for i in range(0, len(records), batch_size):
        batch = records[i : i + batch_size]
        col.add(
            ids=[r["id"] for r in batch],
            embeddings=[r["embedding"] for r in batch],
            documents=[r["text"] for r in batch],
            metadatas=[{"source": r["source"], "chunk_index": r["chunk_index"], "method": r["method"]} for r in batch],
        )
        log.info("upserted batch %d (%d records)", i // batch_size + 1, len(batch))

    log.info("load complete: collection=%s count=%d", name, col.count())


def retrieve(query: str, method: str = DEFAULT_METHOD, k: int = 5, log=None) -> list[dict]:
    t0 = time.time()
    col = get_client().get_collection(collection_name(method))
    qvec = embed_query(query)
    res = col.query(query_embeddings=[qvec], n_results=k, include=["documents", "metadatas", "distances"])
    hits = [
        {"text": d, "source": m["source"], "chunk_index": m["chunk_index"], "distance": round(dist, 4)}
        for d, m, dist in zip(res["documents"][0], res["metadatas"][0], res["distances"][0])
    ]
    if log:
        log.info("retrieved %d chunks from %s in %.2fs", len(hits), collection_name(method), time.time() - t0)
        for h in hits:
            log.info("  dist=%.4f  %s#%d  %s...", h["distance"], h["source"], h["chunk_index"], h["text"][:80])
    return hits


def run_query(query: str, method: str, k: int) -> None:
    log = get_logger("query")
    log.info("query: %s", query)
    hits = retrieve(query, method, k, log)
    print("\n" + "=" * 80)
    for i, h in enumerate(hits, 1):
        print(f"[{i}] {h['source']} (chunk {h['chunk_index']}, distance {h['distance']})\n{h['text']}\n")


def status(method: str = DEFAULT_METHOD) -> dict:
    """Used by GET /api/rag/status. Never raises."""
    try:
        col = get_client().get_collection(collection_name(method))
        return {"available": True, "collection": collection_name(method), "chunks": col.count()}
    except Exception as e:  # chroma down, or collection not built yet
        return {"available": False, "collection": collection_name(method), "chunks": 0, "reason": str(e)[:200]}
