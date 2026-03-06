"""
Bridge adapter — wraps gods_eye.py as a library so Openclaw can drive scans
without modifying the original tool.
"""
from __future__ import annotations

import asyncio
import json
import os
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path

# Ensure the repo root is on sys.path so `import gods_eye` works.
_REPO_ROOT = str(Path(__file__).resolve().parent.parent.parent)
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

import gods_eye  # noqa: E402


@dataclass
class ScanFinding:
    """Normalised representation of a single Gods Eye result."""
    url: str
    final_url: str = ""
    status: int | str = 0
    title: str = ""
    load_ms: int = 0
    sec_grade: str = "F"
    sec_headers: list[str] = field(default_factory=list)
    techs: list[str] = field(default_factory=list)
    category: str = ""
    headers: dict[str, str] = field(default_factory=dict)
    tls: dict[str, str] = field(default_factory=dict)
    redirect_chain: list[str] = field(default_factory=list)
    cookies: list[dict] = field(default_factory=list)
    console_logs: list[str] = field(default_factory=list)
    screenshot_path: str = ""
    diff_pct: float = 0.0
    diff_severity: str = ""
    content_changes: list[dict] = field(default_factory=list)
    notes: str = ""
    raw: dict = field(default_factory=dict)


@dataclass
class ScanResult:
    """Aggregate result of a full Gods Eye scan run."""
    scan_id: str = ""
    started_at: str = ""
    finished_at: str = ""
    total: int = 0
    success: int = 0
    warn: int = 0
    fail: int = 0
    runtime_seconds: float = 0.0
    output_dir: str = ""
    findings: list[ScanFinding] = field(default_factory=list)


def parse_gods_eye_result(result_dict: dict) -> ScanFinding:
    """Convert a raw gods_eye result dict into a normalised ScanFinding."""
    return ScanFinding(
        url=result_dict.get("url", ""),
        final_url=result_dict.get("final_url", ""),
        status=result_dict.get("status", 0),
        title=result_dict.get("title", ""),
        load_ms=result_dict.get("load_ms", 0),
        sec_grade=result_dict.get("sec_grade", "F"),
        sec_headers=result_dict.get("sec_headers", []),
        techs=result_dict.get("techs", []),
        category=result_dict.get("category", ""),
        headers=result_dict.get("headers", {}),
        tls=result_dict.get("tls", {}),
        redirect_chain=result_dict.get("redirect_chain", []),
        cookies=result_dict.get("cookies", []),
        console_logs=result_dict.get("console_logs", []),
        screenshot_path=result_dict.get("screenshot_path", result_dict.get("screenshot", "")),
        diff_pct=result_dict.get("diff_pct", 0.0),
        diff_severity=result_dict.get("diff_severity", ""),
        content_changes=result_dict.get("content_changes", []),
        notes=result_dict.get("notes", ""),
        raw=result_dict,
    )


async def run_scan(
    urls: list[str],
    out_dir: str | None = None,
    threads: int = 5,
    timeout: int = 8000,
    viewport: dict[str, int] | None = None,
    full_page: bool = False,
    retries: int = 2,
    wait_mode: str = "balanced",
    proxy: str | None = None,
    extra_headers: dict[str, str] | None = None,
    img_format: str = "png",
) -> ScanResult:
    """Run a Gods Eye scan and return structured results.

    This is the primary integration point — it calls gods_eye.run_parallel()
    directly without spawning a subprocess, giving us full access to the
    result dicts.
    """
    if viewport is None:
        viewport = {"width": 1920, "height": 1080}

    if out_dir is None:
        out_dir = os.path.join(os.getcwd(), f"openclaw_scan_{int(time.time())}")
    os.makedirs(out_dir, exist_ok=True)

    scan_id = f"scan_{int(time.time())}_{os.getpid()}"
    started_at = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    start = time.time()

    total, success, warn, fail, raw_results = await gods_eye.run_parallel(
        urls=urls,
        out_dir=out_dir,
        threads=threads,
        timeout=timeout,
        viewport=viewport,
        full_page=full_page,
        retries=retries,
        wait_mode=wait_mode,
        proxy=proxy,
        extra_headers=extra_headers,
        img_format=img_format,
    )

    elapsed = time.time() - start
    finished_at = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

    findings = [parse_gods_eye_result(r) for r in raw_results]

    # Persist raw results as JSON for auditability
    results_json = os.path.join(out_dir, "results.json")
    gods_eye.export_json(raw_results, results_json)

    return ScanResult(
        scan_id=scan_id,
        started_at=started_at,
        finished_at=finished_at,
        total=total,
        success=success,
        warn=warn,
        fail=fail,
        runtime_seconds=round(elapsed, 2),
        output_dir=out_dir,
        findings=findings,
    )
