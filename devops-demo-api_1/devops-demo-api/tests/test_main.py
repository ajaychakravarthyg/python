from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_root():
    r = client.get("/")
    assert r.status_code == 200
    assert r.json()["message"].startswith("hello")


def test_healthz():
    assert client.get("/healthz").status_code == 200


def test_metrics_exposed():
    assert client.get("/metrics").status_code == 200
