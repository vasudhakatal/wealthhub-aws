"""Authentication: password check, JWT claims, and rejection of bad tokens."""

from datetime import UTC, datetime, timedelta

import jwt
import pytest
from app.auth import SECRET, check_password, token

PROTECTED_GETS = ["/portfolio", "/performance", "/jobs", "/jobs/some-id", "/jobs/some-id/pdf"]


def make_token(**overrides):
    claims = {
        "sub": "demo-adviser",
        "iss": "wealthhub",
        "aud": "wealthhub-local",
        "exp": datetime.now(UTC) + timedelta(hours=1),
    }
    claims.update(overrides)
    return jwt.encode(claims, SECRET, algorithm="HS256")


def test_check_password_accepts_only_the_configured_password():
    assert check_password("local-demo-only") is True
    assert check_password("Local-Demo-Only") is False
    assert check_password("") is False


def test_issued_token_has_expected_claims_and_expiry():
    claims = jwt.decode(
        token(), SECRET, algorithms=["HS256"], audience="wealthhub-local", issuer="wealthhub"
    )
    assert claims["sub"] == "demo-adviser"
    remaining = datetime.fromtimestamp(claims["exp"], UTC) - datetime.now(UTC)
    assert timedelta(minutes=55) < remaining <= timedelta(hours=1)


def test_wrong_username_is_rejected_even_with_right_password(client):
    r = client.post("/auth/login", json={"username": "admin", "password": "local-demo-only"})
    assert r.status_code == 401


@pytest.mark.parametrize("path", PROTECTED_GETS)
def test_protected_routes_require_a_token(client, path):
    assert client.get(path).status_code == 401


def test_onboarding_requires_a_token(client):
    body = {"name": "Taylor", "email": "t@example.com", "risk": "Balanced"}
    assert client.post("/onboard", json=body).status_code == 401


def test_token_signed_with_wrong_secret_is_rejected(client):
    forged = jwt.encode(
        {
            "sub": "x",
            "iss": "wealthhub",
            "aud": "wealthhub-local",
            "exp": datetime.now(UTC) + timedelta(hours=1),
        },
        "a-completely-different-secret-value-0123456789",
        algorithm="HS256",
    )
    assert client.get("/jobs", headers={"Authorization": f"Bearer {forged}"}).status_code == 401


def test_token_for_wrong_audience_is_rejected(client):
    bad = make_token(aud="some-other-service")
    assert client.get("/jobs", headers={"Authorization": f"Bearer {bad}"}).status_code == 401
