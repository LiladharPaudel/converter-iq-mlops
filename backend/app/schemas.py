"""Request/response models shared by the API and the frontend."""
from __future__ import annotations

from pydantic import BaseModel, Field


class Alternative(BaseModel):
    label: str
    probability: float = Field(ge=0, le=1)


class Prediction(BaseModel):
    """What the classifier says about a single 20 x 3 cycle."""

    label: str
    healthy: bool
    confidence: float = Field(ge=0, le=1)
    alternatives: list[Alternative] = []


class CycleResult(BaseModel):
    index: int
    rms: list[float]            # [A, B, C] in amperes
    unbalance: float            # 0..1, max deviation from mean RMS
    distortion: float           # 0..1, non-fundamental energy fraction
    label: str
    confidence: float


class EpisodeInfo(BaseModel):
    filename: str
    n_cycles: int
    samples_per_phase: int = 20
    phases: int = 3
    sample_rate_hz: int = 1000
    source: str = "file"        # "file" | "image"


class Verdict(Prediction):
    """Episode-level verdict, aggregated across cycles."""

    first_fault_cycle: int | None = None


class PredictResponse(BaseModel):
    episode: EpisodeInfo
    verdict: Verdict
    cycles: list[CycleResult]
    waveform: list[list[float]]  # n_cycles x 60, phase-major like the dataset
    in_distribution: bool
    inference_ms: float
    model_version: str


class ModelCard(BaseModel):
    version: str
    kind: str
    input_shape: list[int]
    classes: list[str]
    note: str


# ---- RAG (milestone 2) ----

class RagStatus(BaseModel):
    available: bool
    collection: str
    chunks: int
    reason: str | None = None


class ExplainRequest(BaseModel):
    """The frontend sends back the verdict it already has, plus a question."""

    verdict: Verdict
    episode: EpisodeInfo
    question: str = "Explain this verdict to a field technician and list what to inspect first."
    mean_unbalance: float | None = None
    mean_distortion: float | None = None
    in_distribution: bool | None = None
    k: int = Field(default=5, ge=1, le=10)


class Passage(BaseModel):
    source: str
    chunk_index: int
    distance: float
    text: str


class ExplainResponse(BaseModel):
    answer: str
    passages: list[Passage]
    model: str
    latency_ms: float
