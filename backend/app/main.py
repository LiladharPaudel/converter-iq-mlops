from __future__ import annotations

import time
from collections import Counter

import numpy as np
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from . import features as F
from .model import CLASSES, MODEL_VERSION, classify, in_distribution
from .parsing import ParseError, parse_episode
from .schemas import CycleResult, EpisodeInfo, ModelCard, PredictResponse, Verdict

app = FastAPI(title="ConverterIQ API", version="0.2.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

MAX_UPLOAD_MB = 60


@app.get("/api/health")
def health():
    return {"status": "ok", "model_version": MODEL_VERSION}


@app.get("/api/model", response_model=ModelCard)
def model_card():
    return ModelCard(
        version=MODEL_VERSION,
        kind="rule-based stand-in",
        input_shape=[20, 3],
        classes=CLASSES,
        note="Threshold rules on RMS, unbalance, distortion and DC offset. "
        "Replaced by the 1-D CNN in milestone 3.",
    )


@app.post("/api/predict", response_model=PredictResponse)
async def predict(file: UploadFile = File(...)):
    raw = await file.read()
    if len(raw) > MAX_UPLOAD_MB * 1024 * 1024:
        raise HTTPException(413, f"File is larger than {MAX_UPLOAD_MB} MB.")
    try:
        episode = parse_episode(file.filename or "upload.json", raw)
    except ParseError as e:
        raise HTTPException(422, str(e)) from e

    t0 = time.perf_counter()
    cycles: list[CycleResult] = []
    preds = []
    for i, cyc in enumerate(episode):
        p = classify(cyc)
        preds.append(p)
        r = F.rms(cyc)
        cycles.append(
            CycleResult(
                index=i,
                rms=[round(float(x), 1) for x in r],
                unbalance=round(F.unbalance(r), 4),
                distortion=round(F.distortion(cyc), 4),
                label=p.label,
                confidence=p.confidence,
            )
        )
    ms = (time.perf_counter() - t0) * 1000

    return PredictResponse(
        episode=EpisodeInfo(filename=file.filename or "upload", n_cycles=len(episode)),
        verdict=_aggregate(preds),
        cycles=cycles,
        waveform=np.round(episode, 2).tolist(),
        in_distribution=in_distribution(episode),
        inference_ms=round(ms, 2),
        model_version=MODEL_VERSION,
    )


@app.post("/api/predict/image")
async def predict_image(file: UploadFile = File(...)):
    raise HTTPException(
        501,
        "Reading waveforms from a scope photo ships in milestone 4. "
        "For now, upload the logger's .json or .csv export.",
    )


def _aggregate(preds) -> Verdict:
    """Episode verdict = the fault that dominates the faulty cycles.

    A handful of early cycles can carry noisy labels (see data-quality notes),
    so a fault has to appear in at least 10% of cycles to name the episode.
    """
    faulty = [p for p in preds if not p.healthy]
    if len(faulty) >= max(1, 0.10 * len(preds)):
        label, _ = Counter(p.label for p in faulty).most_common(1)[0]
        chosen = [p for p in faulty if p.label == label]
        first = next(i for i, p in enumerate(preds) if p.label == label)
    else:
        label = "Nominal operation"
        chosen = [p for p in preds if p.healthy] or preds
        first = None

    conf = float(np.mean([p.confidence for p in chosen]))
    alt_counter: Counter[str] = Counter()
    for p in chosen:
        for a in p.alternatives:
            alt_counter[a.label] += a.probability
    alts = [{"label": k, "probability": round(v / len(chosen), 4)} for k, v in alt_counter.most_common(2)]
    return Verdict(
        label=label,
        healthy=(label == "Nominal operation"),
        confidence=round(conf, 4),
        alternatives=alts,
        first_fault_cycle=first,
    )
