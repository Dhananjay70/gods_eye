"""
Openclaw Portal — FastAPI web application.
"""
from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from openclaw.db.database import init_db
from openclaw.onsa.engine import ONSAEngine
from openclaw.cops.engine import COPSEngine

import os

_PORTAL_DIR = os.path.dirname(os.path.abspath(__file__))

# Shared instances
onsa_engine: ONSAEngine | None = None
cops_engine: COPSEngine | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup / shutdown hooks."""
    global onsa_engine, cops_engine
    await init_db()
    onsa_engine = ONSAEngine()
    cops_engine = COPSEngine(onsa_engine)
    yield


app = FastAPI(
    title="Openclaw Portal",
    description="Compliance & Disclosure Platform — powered by Gods Eye",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files & templates
static_dir = os.path.join(_PORTAL_DIR, "static")
os.makedirs(static_dir, exist_ok=True)
app.mount("/static", StaticFiles(directory=static_dir), name="static")

templates_dir = os.path.join(_PORTAL_DIR, "templates")
os.makedirs(templates_dir, exist_ok=True)
templates = Jinja2Templates(directory=templates_dir)

# Register route modules
from openclaw.portal.routes import auth, incidents, scans, disclosure, audit  # noqa: E402

app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(incidents.router, prefix="/api/incidents", tags=["incidents"])
app.include_router(scans.router, prefix="/api/scans", tags=["scans"])
app.include_router(disclosure.router, prefix="/api", tags=["disclosure"])
app.include_router(audit.router, prefix="/api/audit", tags=["audit"])


@app.get("/")
async def root():
    return {
        "name": "Openclaw Portal",
        "version": "0.1.0",
        "status": "running",
        "docs": "/docs",
    }


@app.get("/health")
async def health():
    return {"status": "ok"}
