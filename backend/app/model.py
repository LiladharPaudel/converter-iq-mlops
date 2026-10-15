"""Stand-in classifier.

A handful of threshold rules on engineered features, so the API, the UI
and the deployment pipeline can be exercised before the CNN is trained.
Replace the body of ``classify`` with a call into the trained model and
keep the return type; nothing downstream changes.
"""
from __future__ import annotations

import os

import numpy as np

from . import features as F
from .schemas import Alternative, Prediction

MODEL_VERSION = os.getenv("MODEL_VERSION", "rules-v0")

CLASSES = [
    "Nominal operation",
    "Phase A disconnection",
    "Phase B disconnection",
    "Phase C disconnection",
    "Grid unbalance",
    "Harmonic distortion",
    "DC offset / bus abnormality",
    "Overcurrent / short circuit",
]

NOMINAL_RMS = 1500.0  # A, from the dataset's healthy records


def classify(cycle: np.ndarray) -> Prediction:
    r = F.rms(cycle)
    unb = F.unbalance(r)
    thd = F.distortion(cycle)
    dco = F.dc_offset(cycle)
    peak = np.max(np.abs(cycle))

    scores = {c: 0.02 for c in CLASSES}

    dead = r < 0.05 * NOMINAL_RMS
    if dead.sum() == 1:
        scores[f"Phase {'ABC'[int(np.argmax(dead))]} disconnection"] = 0.96
    elif peak > 2.5 * NOMINAL_RMS * np.sqrt(2):
        scores["Overcurrent / short circuit"] = 0.90
    elif dco > 0.25:
        scores["DC offset / bus abnormality"] = 0.85
    elif thd > 0.15:
        scores["Harmonic distortion"] = min(0.98, 0.70 + thd)
    elif unb > 0.12:
        scores["Grid unbalance"] = min(0.95, 0.60 + unb)
    else:
        # healthy; confidence shrinks as the signal drifts from textbook
        scores["Nominal operation"] = max(0.55, 0.97 - 2 * unb - 2 * thd)

    total = sum(scores.values())
    probs = {k: v / total for k, v in scores.items()}
    ranked = sorted(probs.items(), key=lambda kv: kv[1], reverse=True)
    top, p = ranked[0]
    return Prediction(
        label=top,
        healthy=(top == "Nominal operation"),
        confidence=round(float(p), 4),
        alternatives=[Alternative(label=k, probability=round(float(v), 4)) for k, v in ranked[1:3]],
    )


def in_distribution(episode: np.ndarray) -> bool:
    """Crude OOD screen: amplitude within an order of magnitude of training."""
    peak = float(np.max(np.abs(episode)))
    return 0.05 * NOMINAL_RMS <= peak <= 20 * NOMINAL_RMS
