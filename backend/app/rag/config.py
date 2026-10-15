"""RAG settings. Everything comes from environment variables so the same code
runs in the api container, the one-off indexing container, and pytest."""
import os
from pathlib import Path

GCP_PROJECT = os.getenv("GCP_PROJECT")
GCP_LOCATION = os.getenv("GCP_LOCATION", "us-central1")

EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "gemini-embedding-001")
EMBEDDING_DIM = int(os.getenv("EMBEDDING_DIM", "768"))
GENERATIVE_MODEL = os.getenv("GENERATIVE_MODEL", "gemini-2.5-flash")

CHROMADB_HOST = os.getenv("CHROMADB_HOST", "localhost")
CHROMADB_PORT = int(os.getenv("CHROMADB_PORT", "8000"))

RAG_DATA_DIR = Path(os.getenv("RAG_DATA_DIR", Path(__file__).resolve().parents[2] / "rag_data"))
INPUT_DIR = RAG_DATA_DIR / "input-datasets"
OUTPUT_DIR = RAG_DATA_DIR / "outputs"
LOG_DIR = OUTPUT_DIR / "logs"

CHUNK_METHODS = ("char-split", "recursive-split", "semantic-split")
DEFAULT_METHOD = os.getenv("RAG_CHUNK_METHOD", "recursive-split")
COLLECTION_PREFIX = "converter-faults"

SYSTEM_PROMPT = """You are the diagnostic assistant inside ConverterIQ, a tool that
classifies faults in grid-connected power converters from three-phase current
recordings. The classifier's labels are: Nominal operation, Phase A/B/C
disconnection, Grid unbalance, Harmonic distortion, DC offset / bus abnormality,
Overcurrent / short circuit.

You will receive the classifier's verdict (label, confidence, alternatives,
per-episode features) and a set of reference passages from research papers and
manufacturer datasheets. Explain the verdict to a field engineer.

Rules:
- Ground every technical claim in the reference passages. Cite the file name in
  square brackets after the claim, e.g. [paper_02_open_circuit.pdf].
- If the passages do not cover something, say so; do not invent sources.
- Structure: (1) what this fault is physically, (2) why the measured features
  support or weaken the verdict, (3) what to inspect first, in order.
- Under 250 words unless asked for more. No preamble.
"""
