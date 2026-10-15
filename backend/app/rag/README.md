# ConverterIQ RAG pipeline

Retrieval-augmented explanation layer for ConverterIQ. The classifier in
`app/model.py` names the fault; this pipeline tells the engineer what that fault
is, whether the measured features back it up, and what to inspect first, with
every claim cited to a document in the knowledge base.

## Architecture

```
rag_data/input-datasets/      --chunk            --embed                --load
 papers, datasheets      ──►  chunker.py   ──►   embedder.py      ──►   vectordb.py
 (.pdf .txt .md)              3 strategies       Vertex AI              ChromaDB
                              chunks-*.jsonl     gemini-embedding-001   converter-faults-<method>
                                                 embeddings-*.jsonl
                                                                             │
   POST /api/rag/explain                                                     │
   { verdict, episode, question }                                            ▼
        └──► rag_chat.answer()  ──►  embed("<label>: <question>")  ──►  top-k passages
                                                                             │
                   prompt = system rules + passages + verdict JSON + question ▼
                                                                    Gemini 2.5 Flash
                                                                             │
                                               { answer, passages, model, latency_ms }
                                                                             ▼
                                                        frontend AssistantPanel.jsx
```

Three compose services take part: `api` (FastAPI, imports this package),
`chromadb` (vector store, persisted volume), and `rag-index` (same image as
`api`, runs `python -m app.rag.cli`; profile `index`, so it only starts when
you call it).

## Stages

**1. Chunk** (`chunker.py`) reads every `.pdf`, `.txt`, `.md` in
`rag_data/input-datasets/` and writes `rag_data/outputs/chunks-<method>.jsonl`.

| Method | Split rule | Use |
|---|---|---|
| `char-split` | 350 chars, 40 overlap | baseline |
| `recursive-split` | paragraph → sentence → word | default; keeps inspection procedures intact |
| `semantic-split` | new chunk when sentence cosine to running centroid < 0.80 | papers whose sections mix topics |

**2. Embed** (`embedder.py`) calls Vertex AI `gemini-embedding-001` in batches
of 100 with `task_type=RETRIEVAL_DOCUMENT` (chunks) or `RETRIEVAL_QUERY`
(questions), 768 dims. Writes `embeddings-<method>.jsonl`.

**3. Load** (`vectordb.py`) drops and recreates ChromaDB collection
`converter-faults-<method>` (cosine), upserts in batches of 200, logs the final
count. `status()` powers `GET /api/rag/status` and never raises.

**4. Generate** (`rag_chat.py`) retrieves on `"<fault label>: <question>"` so
passages follow the verdict, then prompts Gemini 2.5 Flash at temperature 0.2
with the system rules in `config.py`: cite file names in brackets, say when the
passages do not cover something, answer in the order physics → evidence →
inspection steps.

**5. Agent** (`agent.py`, optional) is a tool-calling variant from the class
tutorial: Gemini decides when to call `search_fault_docs` and
`get_latest_prediction`. The latter is a stub until MS3.

## How the app uses it

`frontend/src/components/AssistantPanel.jsx` sits under the cycle timeline on
the results screen. It calls `/api/rag/status` once; if the collection is
missing it shows the indexing command instead of a chat box. "Explain this
verdict" posts the verdict, episode info, mean unbalance and distortion to
`/api/rag/explain`; follow-up questions reuse the same context. Each answer
has a "Show sources" toggle that lists the retrieved passages with their
cosine distances.

## Setup

1. Service-account JSON with the **Vertex AI User** role at
   `secrets/llm-service-account.json` (repo root; git-ignored).
2. `cp .env.example .env`, set `GCP_PROJECT`.
3. Add documents to `backend/rag_data/input-datasets/` (10-20 PDFs is plenty;
   a seed `.txt` is included so the pipeline runs before you have papers).

## Usage

```bash
docker compose up -d chromadb
docker compose run --rm rag-index                          # --all: chunk, embed, load (default method)
docker compose run --rm rag-index --all --method char-split
docker compose run --rm rag-index --query "phase C current collapses to zero"
docker compose run --rm rag-index --example                # writes rag_data/outputs/example-retrieval.md
docker compose run --rm rag-index --chat
docker compose run --rm rag-index --agent "Explain the latest verdict"
```

Locally without Docker (from `backend/`, with `.env` exported and ChromaDB on
`localhost:8001`): `CHROMADB_PORT=8001 python -m app.rag.cli --all`.

## Logs

Each stage writes `rag_data/outputs/logs/run-<stage>-<timestamp>.log`:
per-document char and chunk counts, embedding batch progress and elapsed
time, upsert batches and final collection size, and for queries each retrieved
passage with its distance plus generation latency. Commit one log per stage as
MS2 evidence.

## End-to-end evidence

`--example` runs a fixed verdict (Phase C disconnection, 0.96, first fault at
cycle 9 of 40, mean unbalance 0.41) through retrieval and generation and writes
`rag_data/outputs/example-retrieval.md` with the verdict JSON, the retrieved
passages, and the cited answer. Commit that file.

## Decisions

- Pipeline lives inside the API package, not a sibling service, so
  `/api/rag/explain` imports `answer()` directly and there is one image to
  build and deploy.
- RAG is optional at runtime. `/api/predict` and the tests do not need GCP
  credentials or ChromaDB; the UI hides the assistant when the index is absent.
- One ChromaDB collection per chunk method, so MS3 can compare retrieval
  quality on held-out questions without re-embedding.
- Retrieval query is prefixed with the fault label. A user asking "what should
  I check first?" otherwise retrieves generic maintenance text.

## Tests

`tests/test_api.py` covers the degraded paths: `/api/rag/status` returns
`available: false` when ChromaDB is unreachable, and `/api/rag/explain` returns
503 when the index is not built. Live Vertex calls are exercised by
`--example`, not by pytest.

## Roadmap

- MS3: swap the agent's prediction stub for the real model; evaluate the three
  chunk methods; add the retrieved passages to the downloadable report.
- MS4: stream the answer token by token; let the engineer upload a site
  manual to the knowledge base from the UI.
- MS5: nightly re-index from a GCS bucket.
