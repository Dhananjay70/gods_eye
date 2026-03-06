"""
Openclaw configuration — settings loaded from environment variables.
"""
from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


def _resolve_data_dir() -> Path:
    """Return the data directory, creating it if needed."""
    p = Path(os.getenv("OPENCLAW_DATA_DIR", os.path.join(os.getcwd(), "openclaw_data")))
    p.mkdir(parents=True, exist_ok=True)
    return p


DATA_DIR: Path = _resolve_data_dir()

DB_URL: str = os.getenv(
    "OPENCLAW_DB_URL",
    f"sqlite+aiosqlite:///{DATA_DIR / 'openclaw.db'}",
)

LLM_PROVIDER: str = os.getenv("OPENCLAW_LLM_PROVIDER", "ollama")

ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")

OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

ONSA_CHAINS_DIR: Path = DATA_DIR / "chains"
ONSA_CHAINS_DIR.mkdir(parents=True, exist_ok=True)

EXPORT_DIR: Path = DATA_DIR / "exports"
EXPORT_DIR.mkdir(parents=True, exist_ok=True)

JWT_SECRET: str = os.getenv("OPENCLAW_JWT_SECRET", "change-me-in-production")
JWT_ALGORITHM: str = "HS256"
JWT_EXPIRE_MINUTES: int = int(os.getenv("OPENCLAW_JWT_EXPIRE_MINUTES", "480"))

PORTAL_HOST: str = os.getenv("OPENCLAW_HOST", "127.0.0.1")
PORTAL_PORT: int = int(os.getenv("OPENCLAW_PORT", "8000"))

# Score threshold that triggers automatic escalation
MATERIALITY_THRESHOLD: float = float(os.getenv("OPENCLAW_MATERIALITY_THRESHOLD", "0.7"))
