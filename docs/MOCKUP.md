# ConverterIQ

AI-powered fault diagnosis for grid-connected power converters.
An engineer uploads a recorded episode of three-phase current (or, later, a
photo of the scope) and gets back a diagnosis, a confidence score and an
interactive replay of the waveform.

> Milestone 2 mock-up. The backend serves a rule-based *stand-in* classifier
> behind the same API contract the 1-D CNN will use, so the frontend and the
> deployment pipeline can be built and tested now.

```
converter-iq-mlops/
├── backend/            FastAPI service: parsing, features, stand-in model
│   ├── app/
│   │   ├── main.py     routes: /health, /model, /predict, /predict/image
│   │   ├── parsing.py  JSON / CSV episode readers
│   │   ├── features.py RMS, unbalance, distortion per cycle
│   │   ├── model.py    rule-based classifier (swap for the CNN here)
│   │   └── schemas.py  request / response models
│   ├── sample_data/    small episodes you can drag into the UI
│   └── tests/
├── frontend/           React + Vite single-page app
└── docker-compose.yml
```

## Run it locally

Backend (Python 3.11+, uv):

```bash
cd backend
uv venv
source .venv/bin/activate
uv sync
uv run uvicorn app.main:app --reload --port 8000
```

Frontend (Node 20+):

```bash
cd frontend
npm install
npm run dev          # http://localhost:5173, proxies /api -> :8000
```

Or both with Docker:

```bash
docker compose up --build   # UI on http://localhost:5173, API on :8000
```

Then drop `backend/sample_data/episode_phase_c_open.json` onto the upload
area.

## API

| Method | Path             | Body                          | Returns                                   |
|--------|------------------|-------------------------------|-------------------------------------------|
| GET    | `/api/health`    | –                             | `{status, model_version}`                 |
| GET    | `/api/model`     | –                             | model card: classes, input shape, version |
| POST   | `/api/predict`   | multipart file (.json / .csv) | episode diagnosis, see below              |
| POST   | `/api/predict/image` | multipart image           | 501 until photo ingestion ships (M4)      |

`/api/predict` response (abridged):

```json
{
  "episode": {"filename": "...", "n_cycles": 386, "sample_rate_hz": 1000},
  "verdict": {"label": "Phase C disconnection", "healthy": false,
              "confidence": 0.96, "alternatives": [{"label": "...", "probability": 0.02}]},
  "cycles": [{"index": 0, "rms": [1414, 1411, 1413], "unbalance": 0.003,
              "distortion": 0.01, "label": "Nominal operation", "confidence": 0.91}],
  "waveform": [[...60 values...], ...],
  "in_distribution": true,
  "inference_ms": 0.6
}
```

### Input format

Either the raw Zenodo export (a JSON list of records with a 60-value
`mea_value`: 20 samples × 3 phases, phase-major) or a CSV with 60 numeric
columns per row. Records with other lengths are rejected with a 422 and a
message saying what was found.

## Swapping in the real model

`backend/app/model.py` exposes one function, `classify(window) -> Prediction`.
Replace the rule block with a call into the trained CNN (ONNX / TorchScript),
keep the return type, and nothing else changes.

## Roadmap

1. Data processing + web interface — Oct 11
2. Containerised model, basic mock-up — Oct 20  ← this
3. Integrate model into running system — Nov 12
4. User-ready interface + screening, photo ingestion — Nov 22
5. Deployment-ready, no bugs — Dec 1
6. Kubernetes deployment + showcase — Dec 10
