"""API behaviour (limits, validation, headers) and worker behaviour (ordering, failure)."""

import pytest
from app.db import Job, Session

import worker.main as worker_main
from worker.main import process_one

BODY = {"name": "Taylor Demo", "email": "taylor@example.com", "risk": "Balanced"}


def test_performance_returns_six_months_of_synthetic_data(client, headers):
    data = client.get("/performance", headers=headers).json()
    assert data["mock"] is True
    assert [p["month"] for p in data["series"]] == ["May", "Jun", "Jul", "Aug", "Sep", "Oct"]
    assert data["series"][-1]["value"] == 244000


def test_responses_carry_security_and_trace_headers(client):
    r = client.get("/health")
    assert r.headers["X-Content-Type-Options"] == "nosniff"
    assert len(r.headers["X-Request-ID"]) == 36


def test_general_api_rate_limit_returns_429_with_retry_after(client, headers):
    for _ in range(240):
        assert client.get("/performance", headers=headers).status_code == 200
    r = client.get("/performance", headers=headers)
    assert r.status_code == 429
    assert r.headers["Retry-After"] == "60"


def test_health_check_is_never_rate_limited(client):
    assert all(client.get("/health").status_code == 200 for _ in range(30))


@pytest.mark.parametrize(
    "bad",
    [
        {**BODY, "name": "A"},
        {**BODY, "name": "x" * 101},
        {**BODY, "email": "a" * 250 + "@example.com"},
        {**BODY, "email": "no-at-sign.example.com"},
        {**BODY, "name": "Bad\x07Name"},
    ],
)
def test_onboarding_rejects_invalid_fields(client, headers, bad):
    assert client.post("/onboard", headers=headers, json=bad).status_code == 422


def test_name_is_trimmed_before_it_is_stored(client, headers):
    client.post("/onboard", headers=headers, json={**BODY, "name": "   Taylor   "})
    assert client.get("/jobs", headers=headers).json()[0]["client"] == "Taylor"


def test_new_job_is_queued_and_has_no_pdf_yet(client, headers):
    job_id = client.post("/onboard", headers=headers, json=BODY).json()["job_id"]
    assert client.get(f"/jobs/{job_id}", headers=headers).json()["status"] == "queued"
    assert client.get(f"/jobs/{job_id}/pdf", headers=headers).status_code == 404


def test_worker_processes_the_oldest_job_first(client, headers):
    first = client.post("/onboard", headers=headers, json=BODY).json()["job_id"]
    second = client.post("/onboard", headers=headers, json=BODY).json()["job_id"]
    assert process_one() is True
    with Session() as db:
        assert db.get(Job, first).status == "completed"
        assert db.get(Job, second).status == "queued"


def test_pdf_filename_is_derived_from_the_job_id(client, headers):
    job_id = client.post("/onboard", headers=headers, json=BODY).json()["job_id"]
    process_one()
    with Session() as db:
        assert db.get(Job, job_id).pdf == f"{job_id}.pdf"


def test_worker_marks_job_failed_when_pdf_generation_breaks(client, headers, monkeypatch):
    class Broken:
        def __init__(self, *args, **kwargs):
            pass

        def build(self, *args, **kwargs):
            raise RuntimeError("disk full")

    monkeypatch.setattr(worker_main, "SimpleDocTemplate", Broken)
    job_id = client.post("/onboard", headers=headers, json=BODY).json()["job_id"]
    assert process_one() is True
    job = client.get(f"/jobs/{job_id}", headers=headers).json()
    assert job["status"] == "failed"
    assert "PDF generation failed" in job["error"]
    assert client.get(f"/jobs/{job_id}/pdf", headers=headers).status_code == 404
