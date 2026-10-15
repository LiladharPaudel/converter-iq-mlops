"""ConverterIQ RAG pipeline CLI.  Run from backend/:  python -m app.rag.cli ...

    python -m app.rag.cli --all    --method recursive-split     # chunk + embed + load
    python -m app.rag.cli --query  "Phase C current collapses to zero"
    python -m app.rag.cli --example            # writes rag_data/outputs/example-retrieval.md
    python -m app.rag.cli --chat
    python -m app.rag.cli --agent "Explain the latest verdict"
"""
import argparse
from .config import CHUNK_METHODS, DEFAULT_METHOD

EXAMPLE_CONTEXT = {
    "label": "Phase C disconnection", "confidence": 0.96, "healthy": False,
    "alternatives": [{"label": "Grid unbalance", "probability": 0.02}],
    "first_fault_cycle": 8, "n_cycles": 40,
    "mean_unbalance": 0.41, "mean_distortion": 0.03, "in_distribution": True,
}
EXAMPLE_QUESTION = "Explain this verdict to a field technician and list what to inspect first."


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--chunk", action="store_true")
    p.add_argument("--embed", action="store_true")
    p.add_argument("--load", action="store_true")
    p.add_argument("--all", action="store_true", help="chunk + embed + load")
    p.add_argument("--query", type=str, help="retrieval only, no generation")
    p.add_argument("--example", nargs="?", const=EXAMPLE_QUESTION, help="full run with a sample verdict as context")
    p.add_argument("--chat", action="store_true")
    p.add_argument("--agent", type=str)
    p.add_argument("--method", choices=CHUNK_METHODS, default=DEFAULT_METHOD)
    p.add_argument("--k", type=int, default=5)
    a = p.parse_args()

    if a.chunk or a.all:
        from . import chunker; chunker.run(a.method)
    if a.embed or a.all:
        from . import embedder; embedder.run(a.method)
    if a.load or a.all:
        from . import vectordb; vectordb.run_load(a.method)
    if a.query:
        from . import vectordb; vectordb.run_query(a.query, a.method, a.k)
    if a.example:
        from . import rag_chat; rag_chat.run_example(a.example, a.method, a.k, EXAMPLE_CONTEXT)
    if a.chat:
        from . import rag_chat; rag_chat.run_chat(a.method, a.k)
    if a.agent:
        from . import agent; agent.run_agent(a.agent)
    if not any([a.chunk, a.embed, a.load, a.all, a.query, a.example, a.chat, a.agent]):
        p.print_help()


if __name__ == "__main__":
    main()
