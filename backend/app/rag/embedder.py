"""Stage 2: embed chunks with Vertex AI (Gemini embedding model).

Reads  outputs/chunks-<method>.jsonl
Writes outputs/embeddings-<method>.jsonl  (same records + "embedding": [...])
"""
import json
import time
from google import genai
from google.genai import types
from .config import GCP_PROJECT, GCP_LOCATION, EMBEDDING_MODEL, EMBEDDING_DIM, OUTPUT_DIR
from .logger import get_logger

_client = None


def client() -> genai.Client:
    global _client
    if _client is None:
        _client = genai.Client(vertexai=True, project=GCP_PROJECT, location=GCP_LOCATION)
    return _client


def embed_texts(texts: list[str], task: str = "RETRIEVAL_DOCUMENT", batch_size: int = 100) -> list[list[float]]:
    """Batched embedding call. Vertex caps batch size, so we page through."""
    out: list[list[float]] = []
    for i in range(0, len(texts), batch_size):
        batch = texts[i : i + batch_size]
        resp = client().models.embed_content(
            model=EMBEDDING_MODEL,
            contents=batch,
            config=types.EmbedContentConfig(task_type=task, output_dimensionality=EMBEDDING_DIM),
        )
        out.extend(e.values for e in resp.embeddings)
    return out


def embed_query(text: str) -> list[float]:
    return embed_texts([text], task="RETRIEVAL_QUERY")[0]


def run(method: str, batch_size: int = 100) -> None:
    log = get_logger(f"embed-{method}")
    in_path = OUTPUT_DIR / f"chunks-{method}.jsonl"
    out_path = OUTPUT_DIR / f"embeddings-{method}.jsonl"
    records = [json.loads(l) for l in in_path.open()]
    log.info("loaded %d chunks from %s", len(records), in_path)
    log.info("model=%s dim=%d batch_size=%d", EMBEDDING_MODEL, EMBEDDING_DIM, batch_size)

    t0 = time.time()
    with out_path.open("w") as f:
        for i in range(0, len(records), batch_size):
            batch = records[i : i + batch_size]
            vecs = embed_texts([r["text"] for r in batch], batch_size=batch_size)
            for r, v in zip(batch, vecs):
                r["embedding"] = v
                f.write(json.dumps(r) + "\n")
            log.info("batch %3d: embedded %3d chunks (%.1fs elapsed)", i // batch_size + 1, len(batch), time.time() - t0)

    log.info("embedding complete: %d vectors -> %s", len(records), out_path)
