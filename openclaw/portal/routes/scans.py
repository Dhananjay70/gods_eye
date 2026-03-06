"""
Scan routes — trigger and view Gods Eye scans.
"""
from __future__ import annotations

import asyncio
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from openclaw.portal.routes.auth import get_current_user
from openclaw.portal import app as portal_app

router = APIRouter()

# In-memory scan store
_scans: dict[str, dict] = {}


class ScanRequest(BaseModel):
    urls: list[str]
    threads: int = 5
    timeout: int = 8000
    wait_mode: str = "balanced"
    tenant_id: str = "default"


@router.post("")
async def trigger_scan(body: ScanRequest, user: dict = Depends(get_current_user)):
    """Trigger a new Gods Eye scan."""
    from openclaw.bridge.scanner import run_scan
    from openclaw.onsa.engine import ONSAEngine
    from openclaw.onsa.models import AuditAction
    from openclaw.cops.scorer import score_findings

    if not body.urls:
        raise HTTPException(status_code=400, detail="No URLs provided")

    onsa = portal_app.onsa_engine or ONSAEngine()

    # Create audit chain
    chain = onsa.create_chain(tenant_id=body.tenant_id, description="Portal scan")
    onsa.append(chain.chain_id, AuditAction.SCAN_STARTED, actor=user["username"],
                data={"urls_count": len(body.urls)})

    # Run scan
    result = await run_scan(
        urls=body.urls,
        threads=body.threads,
        timeout=body.timeout,
        wait_mode=body.wait_mode,
    )

    # Log findings
    for finding in result.findings:
        onsa.append(chain.chain_id, AuditAction.FINDING_RECORDED, actor="gods_eye",
                    data={"url": finding.url, "status": str(finding.status), "sec_grade": finding.sec_grade})

    onsa.append(chain.chain_id, AuditAction.SCAN_COMPLETED, actor="gods_eye",
                data={"total": result.total, "success": result.success, "fail": result.fail})

    # Score
    mat_score = score_findings(result.findings)

    scan_data = {
        "scan_id": result.scan_id,
        "chain_id": chain.chain_id,
        "total": result.total,
        "success": result.success,
        "warn": result.warn,
        "fail": result.fail,
        "runtime_seconds": result.runtime_seconds,
        "materiality_score": mat_score.score,
        "materiality_level": mat_score.level,
        "findings_count": len(result.findings),
        "output_dir": result.output_dir,
    }
    _scans[result.scan_id] = scan_data

    return scan_data


@router.get("")
async def list_scans(user: dict = Depends(get_current_user)):
    """List all scans."""
    return list(_scans.values())


@router.get("/{scan_id}")
async def get_scan(scan_id: str, user: dict = Depends(get_current_user)):
    """Get scan details."""
    scan = _scans.get(scan_id)
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")
    return scan
