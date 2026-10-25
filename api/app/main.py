import logging
import os
import re
import time
import uuid
from collections import defaultdict, deque
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Literal

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import select, text

from .auth import check_password, require_user, token
from .connectors import aggregate
from .db import Base, Client, Job, Session, engine

logger = logging.getLogger("wealthhub")
PDF_DIR = Path(os.environ.get("PDF_DIR", "./pdfs"))


@asynccontextmanager
async def lifespan(app):
    Base.metadata.create_all(engine)
    PDF_DIR.mkdir(parents=True, exist_ok=True)
    yield


app = FastAPI(
    title="WealthHub mock wealth API",
    version="0.1.0",
    lifespan=lifespan,
    root_path="/api",
)
requests = defaultdict(deque)


@app.middleware("http")
async def limits(request: Request, call_next):
    request_id = str(uuid.uuid4())
    if request.url.path != "/health":
        key = (
            request.client.host if request.client else "local",
            "login" if request.url.path == "/auth/login" else "api",
        )
        now = time.monotonic()
        # Bound memory for this single-process demo limiter.
        for old in list(requests):
            if not requests[old] or now - requests[old][-1] > 60:
                del requests[old]
        q = requests[key]
        while q and now - q[0] >= 60:
            q.popleft()
        if len(q) >= (10 if key[1] == "login" else 240):
            from fastapi.responses import JSONResponse

            return JSONResponse(
                {"detail": "Too many requests; wait one minute"},
                status_code=429,
                headers={"Retry-After": "60"},
            )
        q.append(now)
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Content-Type-Options"] = "nosniff"
    logger.info(
        "request id=%s method=%s path=%s status=%s",
        request_id,
        request.method,
        request.url.path,
        response.status_code,
    )
    return response


class Login(BaseModel):
    username: str = Field(max_length=100)
    password: str = Field(max_length=200)


class Onboard(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    email: str = Field(max_length=254)
    risk: Literal["Conservative", "Balanced", "Growth"]

    @field_validator("name")
    @classmethod
    def clean_name(cls, v):
        v = v.strip()
        if len(v) < 2 or any(ord(c) < 32 for c in v):
            raise ValueError("Use a name with at least two printable characters")
        return v

    @field_validator("email")
    @classmethod
    def clean_email(cls, v):
        if not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", v):
            raise ValueError("Enter a valid mock email")
        return v


@app.get("/health")
def health():
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
    return {"status": "ok", "mock_data_only": True}


@app.post("/auth/login")
def login(data: Login):
    if data.username != "demo" or not check_password(data.password):
        raise HTTPException(401, "Incorrect demo credentials")
    return {"access_token": token(), "token_type": "bearer"}


@app.get("/portfolio", dependencies=[Depends(require_user)])
async def portfolio():
    return await aggregate()


@app.get("/performance", dependencies=[Depends(require_user)])
def performance():
    return {
        "mock": True,
        "series": [
            {"month": month, "value": value}
            for month, value in zip(
                ["May", "Jun", "Jul", "Aug", "Sep", "Oct"],
                [215000, 220500, 218700, 231400, 236100, 244000],
            )
        ],
    }


@app.post("/onboard", status_code=202, dependencies=[Depends(require_user)])
def onboard(data: Onboard):
    client_id, job_id = str(uuid.uuid4()), str(uuid.uuid4())
    with Session.begin() as db:
        db.add(Client(id=client_id, **data.model_dump()))
        db.flush()
        db.add(Job(id=job_id, client_id=client_id, status="queued"))
    return {"client_id": client_id, "job_id": job_id, "status": "queued"}


@app.get("/jobs", dependencies=[Depends(require_user)])
def jobs():
    with Session() as db:
        rows = db.execute(
            select(Job, Client).join(Client).order_by(Job.created_at.desc()).limit(50)
        ).all()
        return [
            {
                "id": j.id,
                "client": c.name,
                "risk": c.risk,
                "status": j.status,
                "created_at": j.created_at.isoformat(),
                "error": j.error,
            }
            for j, c in rows
        ]


@app.get("/jobs/{job_id}", dependencies=[Depends(require_user)])
def job(job_id: str):
    with Session() as db:
        j = db.get(Job, job_id)
        if not j:
            raise HTTPException(404, "Job not found")
        return {"id": j.id, "status": j.status, "error": j.error}


@app.get("/jobs/{job_id}/pdf", dependencies=[Depends(require_user)])
def pdf(job_id: str):
    with Session() as db:
        j = db.get(Job, job_id)
        if not j or j.status != "completed" or not j.pdf:
            raise HTTPException(404, "PDF is not ready")
        path = PDF_DIR / j.pdf
        if not path.is_file():
            raise HTTPException(404, "PDF file is missing")
        return FileResponse(
            path, media_type="application/pdf", filename="wealthhub-welcome.pdf"
        )
