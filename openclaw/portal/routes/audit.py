"""
Audit routes — ONSA chain verification and export.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel

from openclaw.portal.routes.auth import get_current_user
from openclaw.portal import app as portal_app

router = APIRouter()


class VerifyRequest(BaseModel):
    chain_id: str


@router.post("/verify")
async def verify_chain(body: VerifyRequest, user: dict = Depends(get_current_user)):
    """Verify the integrity of an ONSA audit chain."""
    from openclaw.onsa.verify import verify_chain as do_verify
    from openclaw.onsa.engine import ONSAEngine

    onsa = portal_app.onsa_engine or ONSAEngine()
    result = do_verify(onsa, body.chain_id)

    return {
        "chain_id": body.chain_id,
        "valid": result.valid,
        "records_checked": result.records_checked,
        "first_invalid_seq": result.first_invalid_seq,
        "message": result.message,
        "verified_at": result.verified_at,
    }


@router.get("/chains")
async def list_chains(tenant: str | None = None, user: dict = Depends(get_current_user)):
    """List all ONSA audit chains."""
    from openclaw.onsa.engine import ONSAEngine

    onsa = portal_app.onsa_engine or ONSAEngine()
    chains = onsa.list_chains(tenant_id=tenant)

    return [
        {
            "chain_id": c.chain_id,
            "tenant_id": c.tenant_id,
            "length": c.length,
            "head_hash": c.head_hash[:16] + "...",
            "created_at": c.created_at,
            "description": c.description,
        }
        for c in chains
    ]


@router.get("/export/{chain_id}")
async def export_audit_package(chain_id: str, user: dict = Depends(get_current_user)):
    """Export an audit chain as a verifiable ZIP package."""
    from openclaw.onsa.engine import ONSAEngine
    from openclaw.onsa.export import export_package

    onsa = portal_app.onsa_engine or ONSAEngine()

    try:
        path = export_package(onsa, chain_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    return FileResponse(
        path=str(path),
        media_type="application/zip",
        filename=path.name,
    )
