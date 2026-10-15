"""Turn an uploaded episode into an (n_cycles, 60) float array.

Accepts the raw Zenodo export (JSON list of records with a 60-value
``mea_value``) or a CSV with 60 numeric columns per row. The layout is
phase-major, matching the dataset: values 0-19 phase A, 20-39 phase B,
40-59 phase C.
"""
from __future__ import annotations

import csv
import io
import json

import numpy as np

SAMPLES = 20
PHASES = 3
WIDTH = SAMPLES * PHASES
MAX_CYCLES = 5000  # keep the response payload sane for the mock-up


class ParseError(ValueError):
    pass


def parse_episode(filename: str, raw: bytes) -> np.ndarray:
    name = filename.lower()
    if name.endswith(".json"):
        rows = _from_json(raw)
    elif name.endswith((".csv", ".tsv", ".txt")):
        rows = _from_csv(raw)
    else:
        raise ParseError("Unsupported file type. Upload a .json or .csv episode.")

    if not rows:
        raise ParseError("The file contains no cycle records.")

    bad = {len(r) for r in rows if len(r) != WIDTH}
    if bad:
        raise ParseError(
            f"Each record needs {WIDTH} values (20 samples x 3 phases); "
            f"found records with {sorted(bad)} values."
        )

    arr = np.asarray(rows[:MAX_CYCLES], dtype=float)
    if not np.isfinite(arr).all():
        raise ParseError("The file contains non-numeric or infinite values.")
    return arr


def _from_json(raw: bytes) -> list[list[float]]:
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        raise ParseError(f"Invalid JSON: {e.msg} at position {e.pos}.") from e

    if isinstance(data, dict):
        data = data.get("records") or data.get("data") or []
    if not isinstance(data, list):
        raise ParseError("Expected a JSON list of records.")

    rows: list[list[float]] = []
    for rec in data:
        vals = rec.get("mea_value") if isinstance(rec, dict) else rec
        if isinstance(vals, list):
            rows.append([float(v) for v in vals])
    return rows


def _from_csv(raw: bytes) -> list[list[float]]:
    text = raw.decode("utf-8-sig", errors="replace")
    reader = csv.reader(io.StringIO(text))
    rows: list[list[float]] = []
    for line in reader:
        if not line:
            continue
        try:
            rows.append([float(v) for v in line])
        except ValueError:
            continue  # header or label column; skip
    return rows


def to_phases(cycle: np.ndarray) -> np.ndarray:
    """(60,) -> (3, 20)"""
    return cycle.reshape(PHASES, SAMPLES)
