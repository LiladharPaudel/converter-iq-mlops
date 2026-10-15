"""Retrieval-augmented generation: retrieve -> grounded prompt -> Gemini."""
import json
import time
from datetime import datetime
from google.genai import types
from .config import GENERATIVE_MODEL, SYSTEM_PROMPT, OUTPUT_DIR, DEFAULT_METHOD
from .embedder import client
from .vectordb import retrieve
from .logger import get_logger


def build_prompt(question: str, hits: list[dict], context: dict | None = None) -> str:
    docs = "\n\n".join(f"### Source: {h['source']} (chunk {h['chunk_index']})\n{h['text']}" for h in hits)
    ctx = f"\n## Classifier verdict\n```json\n{json.dumps(context, indent=2)}\n```\n" if context else ""
    return f"## Reference passages\n{docs}\n{ctx}\n## Question\n{question}"


def generate(prompt: str) -> str:
    resp = client().models.generate_content(
        model=GENERATIVE_MODEL,
        contents=[types.Content(role="user", parts=[types.Part(text=prompt)])],
        config=types.GenerateContentConfig(system_instruction=SYSTEM_PROMPT, temperature=0.2, max_output_tokens=1024),
    )
    return resp.text or ""


def answer(question: str, method: str = DEFAULT_METHOD, k: int = 5, context: dict | None = None, log=None) -> tuple[str, list[dict]]:
    # Retrieve on the fault label + question so passages match the verdict, not just the wording.
    retrieval_query = f"{context['label']}: {question}" if context and context.get("label") else question
    hits = retrieve(retrieval_query, method, k, log)
    t0 = time.time()
    text = generate(build_prompt(question, hits, context))
    if log:
        log.info("generation (%s) took %.2fs, %d chars", GENERATIVE_MODEL, time.time() - t0, len(text))
    return text, hits


def run_chat(method: str, k: int) -> None:
    log = get_logger("chat")
    print(f"ConverterIQ assistant (collection: {method}). Type 'exit' to quit.\n")
    while True:
        q = input("you > ").strip()
        if q.lower() in ("exit", "quit", ""):
            break
        log.info("user: %s", q)
        text, _ = answer(q, method, k, log=log)
        log.info("assistant: %s", text.replace("\n", " ")[:300])
        print(f"\nassistant > {text}\n")


def run_example(question: str, method: str, k: int, context: dict | None = None) -> None:
    """Write one reproducible end-to-end run to outputs/example-retrieval.md (MS2 evidence)."""
    log = get_logger("example")
    log.info("question: %s", question)
    if context:
        log.info("context: %s", json.dumps(context))
    text, hits = answer(question, method, k, context, log=log)

    out = OUTPUT_DIR / "example-retrieval.md"
    with out.open("w") as f:
        f.write("# End-to-end retrieval example\n\n")
        f.write(f"- Date: {datetime.now():%Y-%m-%d %H:%M}\n- Collection: `{method}`\n- Top-k: {k}\n- Generator: `{GENERATIVE_MODEL}`\n\n")
        if context:
            f.write(f"## Classifier verdict\n\n```json\n{json.dumps(context, indent=2)}\n```\n\n")
        f.write(f"## Question\n\n{question}\n\n## Retrieved passages\n\n")
        for i, h in enumerate(hits, 1):
            f.write(f"**[{i}] {h['source']}** (chunk {h['chunk_index']}, cosine distance {h['distance']})\n\n> {h['text']}\n\n")
        f.write(f"## Generated answer\n\n{text}\n")
    log.info("wrote %s", out)
    print(text)
