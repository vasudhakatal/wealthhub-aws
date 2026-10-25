import hashlib
import hmac
import os
import secrets
from datetime import UTC, datetime, timedelta

import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

SECRET = os.environ.get("JWT_SECRET") or secrets.token_urlsafe(48)
PASSWORD = os.environ.get("DEMO_PASSWORD", "local-demo-only")
bearer = HTTPBearer(auto_error=False)


def check_password(value):
    return hmac.compare_digest(
        hashlib.sha256(value.encode()).digest(),
        hashlib.sha256(PASSWORD.encode()).digest(),
    )


def token():
    return jwt.encode(
        {
            "sub": "demo-adviser",
            "iss": "wealthhub",
            "aud": "wealthhub-local",
            "exp": datetime.now(UTC) + timedelta(hours=1),
        },
        SECRET,
        algorithm="HS256",
    )


def require_user(credentials: HTTPAuthorizationCredentials | None = Depends(bearer)):
    try:
        if credentials is None:
            raise ValueError("missing token")
        return jwt.decode(
            credentials.credentials,
            SECRET,
            algorithms=["HS256"],
            audience="wealthhub-local",
            issuer="wealthhub",
        )["sub"]
    except (jwt.PyJWTError, ValueError):
        raise HTTPException(status_code=401, detail="Please sign in again") from None
