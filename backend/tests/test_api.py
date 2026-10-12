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
