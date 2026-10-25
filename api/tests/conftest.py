import os
import tempfile
from pathlib import Path

TEST_DIR = Path(tempfile.mkdtemp(prefix="wealthhub-test-"))
os.environ["DATABASE_URL"] = "sqlite:///" + str(TEST_DIR / "test.db")
os.environ["PDF_DIR"] = str(TEST_DIR / "pdfs")
os.environ["JWT_SECRET"] = "test-secret-that-is-at-least-thirty-two-characters"
os.environ["DEMO_PASSWORD"] = "local-demo-only"

import pytest
from app.db import Base, engine
from app.main import app, requests
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    Base.metadata.drop_all(engine)
    requests.clear()
    with TestClient(app) as c:
        yield c


@pytest.fixture
def headers(client):
    r = client.post(
        "/auth/login", json={"username": "demo", "password": "local-demo-only"}
    )
    return {"Authorization": "Bearer " + r.json()["access_token"]}
