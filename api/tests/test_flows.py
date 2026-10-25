import asyncio

import jwt
from app.auth import SECRET
from app.connectors import aggregate, fetch_source
from app.db import Client, Job, Session

from worker.main import process_one


def test_health_and_auth(client, headers):
    assert client.get("/health").json()["status"] == "ok"
    assert client.get("/portfolio").status_code == 401
    assert (
        client.get(
            "/portfolio", headers={"Authorization": "Bearer invalid"}
        ).status_code
        == 401
    )
    assert (
        client.post(
            "/auth/login", json={"username": "demo", "password": "wrong"}
        ).status_code
        == 401
    )
    assert client.get("/portfolio", headers=headers).json()["total"] == 244000


def test_expired_token(client):
    token = jwt.encode(
        {"sub": "demo-adviser", "iss": "wealthhub", "aud": "wealthhub-local", "exp": 1},
        SECRET,
        algorithm="HS256",
    )
    assert (
        client.get("/jobs", headers={"Authorization": "Bearer " + token}).status_code
        == 401
    )


def test_source_failure_is_partial():
    attempts = []

    async def failing(name):
        if name == "shares":
            attempts.append(name)
            raise ConnectionError("unavailable")
        return await fetch_source(name)

    result = asyncio.run(aggregate(failing))
    assert len(attempts) == 2
    assert result["sources"]["shares"] == "unavailable"
    assert result["total"] == 127100


def test_timeout_retries_are_bounded():
    async def slow(name):
        await asyncio.sleep(1)

    result = asyncio.run(aggregate(slow, timeout=0.01))
    assert result["total"] == 0
    assert set(result["sources"].values()) == {"unavailable"}


def test_onboarding_pdf_end_to_end(client, headers):
    response = client.post(
        "/onboard",
        headers=headers,
        json={
            "name": "Taylor <Demo>",
            "email": "taylor@example.com",
            "risk": "Balanced",
        },
    )
    assert response.status_code == 202
    body = response.json()
    assert client.get(f"/jobs/{body['job_id']}/pdf", headers=headers).status_code == 404
    with Session() as db:
        assert db.get(Client, body["client_id"]).risk == "Balanced"
        assert db.get(Job, body["job_id"]).status == "queued"
    assert process_one() is True
    assert process_one() is False
    assert (
        client.get(f"/jobs/{body['job_id']}", headers=headers).json()["status"]
        == "completed"
    )
    pdf = client.get(f"/jobs/{body['job_id']}/pdf", headers=headers)
    assert pdf.status_code == 200
    assert pdf.content.startswith(b"%PDF")
    assert client.get("/jobs", headers=headers).json()[0]["client"] == "Taylor <Demo>"
    assert client.get(f"/jobs/{body['job_id']}/pdf").status_code == 401


def test_invalid_input_does_not_queue(client, headers):
    for body in [
        dict(name=" ", email="t@example.com", risk="Balanced"),
        dict(name="Demo", email="invalid", risk="Balanced"),
        dict(name="Demo", email="t@example.com", risk="Extreme"),
    ]:
        assert client.post("/onboard", headers=headers, json=body).status_code == 422
    assert client.get("/jobs", headers=headers).json() == []
    assert client.get("/jobs/nonexistent", headers=headers).status_code == 404


def test_login_rate_limit(client):
    for _ in range(10):
        assert (
            client.post(
                "/auth/login", json={"username": "demo", "password": "wrong"}
            ).status_code
            == 401
        )
    assert (
        client.post(
            "/auth/login", json={"username": "demo", "password": "wrong"}
        ).status_code
        == 429
    )
