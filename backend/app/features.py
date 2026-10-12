"""Hand-engineered features for one cycle. Also what the UI shows."""
from __future__ import annotations

import numpy as np

from .parsing import to_phases


def rms(cycle: np.ndarray) -> np.ndarray:
    ph = to_phases(cycle)
    return np.sqrt(np.mean(ph**2, axis=1))


def unbalance(r: np.ndarray) -> float:
    """Max deviation from the mean RMS, as a fraction of the mean."""
    m = r.mean()
    if m <= 1e-9:
        return 1.0
    return float(np.max(np.abs(r - m)) / m)


def distortion(cycle: np.ndarray) -> float:
    """Fraction of energy outside the fundamental (bin 1 of a 20-pt FFT),
    averaged over phases that actually carry current."""
    ph = to_phases(cycle)
    vals = []
    for p in ph:
        if np.sqrt(np.mean(p**2)) < 1e-6:
            continue
        spec = np.abs(np.fft.rfft(p - p.mean()))
        total = (spec**2).sum()
        if total <= 1e-12:
            continue
        vals.append(1.0 - spec[1] ** 2 / total)
    return float(np.mean(vals)) if vals else 0.0


def dc_offset(cycle: np.ndarray) -> float:
    ph = to_phases(cycle)
    r = rms(cycle)
    scale = r.mean() if r.mean() > 1e-9 else 1.0
    return float(np.max(np.abs(ph.mean(axis=1))) / scale)
