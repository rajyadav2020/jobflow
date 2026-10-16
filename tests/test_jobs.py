import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.job_store import InMemoryJobStore, get_job_store

VALID_REPORT = {
    "type": "report",
    "input": {
        "report_type": "sales",
        "date_from": "2026-01-01",
        "date_to": "2026-03-31",
    },
}


@pytest.fixture
def client():
    store = InMemoryJobStore()
    app.dependency_overrides[get_job_store] = lambda: store
    yield TestClient(app)
    app.dependency_overrides.clear()


def test_submit_valid_job_returns_queued(client):
    r = client.post("/jobs", json=VALID_REPORT)
    assert r.status_code == 201
    body = r.json()
    assert body["status"] == "queued"
    assert "id" in body


def test_submit_rejects_end_date_before_start_date(client):
    bad = {
        "type": "report",
        "input": {
            "report_type": "sales",
            "date_from": "2026-03-31",
            "date_to": "2026-01-01",
        },
    }
    r = client.post("/jobs", json=bad)
    assert r.status_code == 422
    assert "date_to" in r.text


def test_submit_rejects_wrong_input_for_type(client):
    bad = {
        "type": "notification",
        "input": {"channel": "pigeon", "recipient": "a@b.com", "message": "hi"},
    }
    r = client.post("/jobs", json=bad)
    assert r.status_code == 422
    assert "channel" in r.text


def test_submit_rejects_unknown_type(client):
    r = client.post("/jobs", json={"type": "teleport", "input": {}})
    assert r.status_code == 422


def test_get_job_returns_submitted_input(client):
    job_id = client.post("/jobs", json=VALID_REPORT).json()["id"]
    r = client.get(f"/jobs/{job_id}")
    assert r.status_code == 200
    assert r.json()["input"]["report_type"] == "sales"
    assert r.json()["status"] == "queued"


def test_get_unknown_job_returns_404(client):
    r = client.get("/jobs/00000000-0000-0000-0000-000000000000")
    assert r.status_code == 404


def test_get_malformed_id_returns_422(client):
    r = client.get("/jobs/not-a-uuid")
    assert r.status_code == 422


def test_list_filters_by_status(client):
    client.post("/jobs", json=VALID_REPORT)
    client.post("/jobs", json=VALID_REPORT)

    queued = client.get("/jobs", params={"status": "queued"}).json()
    assert queued["total"] == 2

    completed = client.get("/jobs", params={"status": "completed"}).json()
    assert completed["total"] == 0
    assert completed["items"] == []


def test_list_pagination(client):
    for _ in range(3):
        client.post("/jobs", json=VALID_REPORT)
    page = client.get("/jobs", params={"limit": 2, "offset": 0}).json()
    assert len(page["items"]) == 2
    assert page["total"] == 3