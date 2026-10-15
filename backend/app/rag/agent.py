"""Optional: tool-calling agent (mirrors the #agents section of the class tutorial).

Gemini decides when to call `search_fault_docs` and `get_latest_prediction`
instead of us hard-wiring retrieval into every turn. `get_latest_prediction` is a
stub that MS3 will replace with a call to the model-serving API.
"""
import json
from google.genai import types
from .config import GENERATIVE_MODEL, SYSTEM_PROMPT, DEFAULT_METHOD
from .embedder import client
from .vectordb import retrieve
from .logger import get_logger


def search_fault_docs(query: str, k: int = 5) -> list[dict]:
    """Search the converter-fault knowledge base for passages relevant to `query`."""
    return retrieve(query, DEFAULT_METHOD, k)


def get_latest_prediction() -> dict:
    """Return the most recent ConverterIQ verdict (stub until MS3)."""
    return {"label": "Phase C disconnection", "confidence": 0.96, "first_fault_cycle": 8, "note": "stub; MS3 wires this to the prediction history"}


TOOLS = {"search_fault_docs": search_fault_docs, "get_latest_prediction": get_latest_prediction}


def run_agent(question: str, max_steps: int = 5) -> None:
    log = get_logger("agent")
    log.info("question: %s", question)
    tool_decls = types.Tool(function_declarations=[
        types.FunctionDeclaration.from_callable(client=client(), callable=fn) for fn in TOOLS.values()
    ])
    config = types.GenerateContentConfig(system_instruction=SYSTEM_PROMPT, tools=[tool_decls], temperature=0.2)
    contents = [types.Content(role="user", parts=[types.Part(text=question)])]

    for step in range(max_steps):
        resp = client().models.generate_content(model=GENERATIVE_MODEL, contents=contents, config=config)
        contents.append(resp.candidates[0].content)
        calls = resp.function_calls or []
        if not calls:
            log.info("final answer after %d step(s)", step + 1)
            print(resp.text)
            return
        parts = []
        for call in calls:
            log.info("tool call: %s(%s)", call.name, json.dumps(dict(call.args)))
            result = TOOLS[call.name](**dict(call.args))
            parts.append(types.Part.from_function_response(name=call.name, response={"result": result}))
        contents.append(types.Content(role="user", parts=parts))
    log.warning("hit max_steps without a final answer")
