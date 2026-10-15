import pathlib

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)
DATA = pathlib.Path(__file__).resolve().parents[1] / "sample_data"


def test_health():
    r = client.get("/api/health")
    assert r.status_code == 200 and r.json()["status"] == "ok"


def test_predict_fault_episode():
    f = DATA / "episode_phase_c_open.json"
    r = client.post("/api/predict", files={"file": (f.name, f.read_bytes(), "application/json")})
    assert r.status_code == 200
    body = r.json()
    assert body["verdict"]["label"] == "Phase C disconnection"
    assert body["verdict"]["first_fault_cycle"] == 8
    assert len(body["cycles"]) == 40


def test_image_not_ready():
    r = client.post("/api/predict/image", files={"file": ("a.jpg", b"xx", "image/jpeg")})
    assert r.status_code == 501


def test_rag_status_degrades_without_chroma(monkeypatch):
    monkeypatch.setenv("CHROMADB_HOST", "127.0.0.1")
    monkeypatch.setenv("CHROMADB_PORT", "1")  # nothing listens here
    r = client.get("/api/rag/status")
    assert r.status_code == 200
    assert r.json()["available"] is False


def test_rag_explain_503_when_not_indexed(monkeypatch):
    from app.rag import vectordb

    monkeypatch.setattr(vectordb, "status", lambda method=None: {"available": False, "collection": "x", "chunks": 0})
    body = {
        "verdict": {"label": "Phase C disconnection", "healthy": False, "confidence": 0.96, "alternatives": []},
        "episode": {"filename": "e.json", "n_cycles": 40},
    }
    r = client.post("/api/rag/explain", json=body)
    assert r.status_code == 503
