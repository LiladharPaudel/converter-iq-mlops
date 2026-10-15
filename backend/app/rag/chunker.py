"""Stage 1: split documents into chunks.

Three strategies are implemented so we can compare retrieval quality in MS3:
  char-split      fixed-size windows with overlap (baseline)
  recursive-split split on paragraph -> sentence -> word boundaries
  semantic-split  group sentences whose embeddings are similar

Output: outputs/chunks-<method>.jsonl, one JSON object per chunk.
"""
import json
import re
import uuid
import numpy as np
from langchain_text_splitters import CharacterTextSplitter, RecursiveCharacterTextSplitter
from .config import OUTPUT_DIR, CHUNK_METHODS
from .loaders import load_documents
from .logger import get_logger


def char_split(text: str, size: int = 350, overlap: int = 40) -> list[str]:
    splitter = CharacterTextSplitter(chunk_size=size, chunk_overlap=overlap, separator="", strip_whitespace=False)
    return splitter.split_text(text)


def recursive_split(text: str, size: int = 350, overlap: int = 40) -> list[str]:
    splitter = RecursiveCharacterTextSplitter(chunk_size=size, chunk_overlap=overlap, separators=["\n\n", "\n", ". ", " ", ""])
    return splitter.split_text(text)


def semantic_split(text: str, embed_fn, threshold: float = 0.80, max_sentences: int = 12) -> list[str]:
    """Greedy sentence grouping. A new chunk starts when cosine similarity between
    the current sentence and the running chunk centroid drops below `threshold`."""
    sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if s.strip()]
    if len(sentences) <= 1:
        return sentences
    vecs = np.array(embed_fn(sentences))
    vecs = vecs / np.linalg.norm(vecs, axis=1, keepdims=True)

    chunks, current, centroid = [], [], None
    for sent, v in zip(sentences, vecs):
        if current and (float(v @ centroid) < threshold or len(current) >= max_sentences):
            chunks.append(" ".join(current))
            current, centroid = [], None
        current.append(sent)
        centroid = v if centroid is None else (centroid * (len(current) - 1) + v) / len(current)
        centroid = centroid / np.linalg.norm(centroid)
    if current:
        chunks.append(" ".join(current))
    return chunks


def run(method: str) -> None:
    assert method in CHUNK_METHODS, f"method must be one of {CHUNK_METHODS}"
    log = get_logger(f"chunk-{method}")
    OUTPUT_DIR.mkdir(exist_ok=True)
    out_path = OUTPUT_DIR / f"chunks-{method}.jsonl"

    embed_fn = None
    if method == "semantic-split":
        from .embedder import embed_texts
        embed_fn = embed_texts

    n_docs, n_chunks = 0, 0
    with out_path.open("w") as f:
        for doc in load_documents():
            n_docs += 1
            if method == "char-split":
                pieces = char_split(doc["text"])
            elif method == "recursive-split":
                pieces = recursive_split(doc["text"])
            else:
                pieces = semantic_split(doc["text"], embed_fn)
            for i, piece in enumerate(pieces):
                f.write(json.dumps({
                    "id": str(uuid.uuid4()),
                    "source": doc["source"],
                    "chunk_index": i,
                    "method": method,
                    "text": piece,
                }) + "\n")
            n_chunks += len(pieces)
            log.info("%-40s chars=%7d chunks=%4d", doc["source"], len(doc["text"]), len(pieces))

    log.info("chunking complete: method=%s docs=%d chunks=%d -> %s", method, n_docs, n_chunks, out_path)
