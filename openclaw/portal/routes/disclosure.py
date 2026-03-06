"""
Disclosure routes — draft management, generation, approval workflow.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from openclaw.portal.routes.auth import get_current_user, require_role

router = APIRouter()

# In-memory draft store
_drafts: dict[str, list[dict]] = {}


class DraftGenerateRequest(BaseModel):
    """Request body to generate a new draft."""
    pass  # Incident ID comes from URL path


class DraftEditRequest(BaseModel):
    nature_and_scope: str | None = None
    data_impact: str | None = None
    material_impact: str | None = None
    remediation: str | None = None


@router.post("/incidents/{incident_id}/drafts")
async def generate_draft(incident_id: str, user: dict = Depends(get_current_user)):
    """Generate a disclosure draft for an incident."""
    from openclaw.disclosure.generator import DisclosureGenerator
    from openclaw.bridge.scanner import ScanFinding
    from openclaw.cops.scorer import MaterialityScore, ScoreBreakdown

    generator = DisclosureGenerator()

    # Build minimal context (in production, pull from DB)
    findings = [ScanFinding(url="placeholder")]
    materiality = MaterialityScore(score=0.5, level="medium")

    draft = await generator.generate_draft(
        incident_id=incident_id,
        findings=findings,
        materiality=materiality,
        timeline=[],
        version=len(_drafts.get(incident_id, [])) + 1,
    )

    draft_data = {
        "draft_id": f"draft_{incident_id}_{draft.version}",
        "incident_id": incident_id,
        "version": draft.version,
        "status": "draft",
        "nature_and_scope": draft.nature_and_scope.content,
        "data_impact": draft.data_impact.content,
        "material_impact": draft.material_impact.content,
        "remediation": draft.remediation.content,
        "executive_summary": draft.executive_summary,
        "confidence": {
            "nature_and_scope": draft.nature_and_scope.confidence.label,
            "data_impact": draft.data_impact.confidence.label,
            "material_impact": draft.material_impact.confidence.label,
            "remediation": draft.remediation.confidence.label,
        },
        "llm_model": draft.llm_model,
        "llm_provider": draft.llm_provider,
        "generated_at": draft.generated_at,
    }

    _drafts.setdefault(incident_id, []).append(draft_data)
    return draft_data


@router.get("/incidents/{incident_id}/drafts")
async def list_drafts(incident_id: str, user: dict = Depends(get_current_user)):
    """List all drafts for an incident."""
    return _drafts.get(incident_id, [])


@router.get("/incidents/{incident_id}/drafts/{draft_id}")
async def get_draft(incident_id: str, draft_id: str, user: dict = Depends(get_current_user)):
    """Get a specific draft."""
    for d in _drafts.get(incident_id, []):
        if d["draft_id"] == draft_id:
            return d
    raise HTTPException(status_code=404, detail="Draft not found")


@router.patch("/incidents/{incident_id}/drafts/{draft_id}")
async def edit_draft(
    incident_id: str,
    draft_id: str,
    body: DraftEditRequest,
    user: dict = Depends(get_current_user),
):
    """Edit sections of a draft."""
    for d in _drafts.get(incident_id, []):
        if d["draft_id"] == draft_id:
            if body.nature_and_scope is not None:
                d["nature_and_scope"] = body.nature_and_scope
            if body.data_impact is not None:
                d["data_impact"] = body.data_impact
            if body.material_impact is not None:
                d["material_impact"] = body.material_impact
            if body.remediation is not None:
                d["remediation"] = body.remediation
            return d
    raise HTTPException(status_code=404, detail="Draft not found")


@router.post("/incidents/{incident_id}/drafts/{draft_id}/approve")
async def approve_draft(
    incident_id: str,
    draft_id: str,
    user: dict = Depends(require_role("legal", "executive", "admin")),
):
    """Approve a draft (requires legal/executive/admin role)."""
    for d in _drafts.get(incident_id, []):
        if d["draft_id"] == draft_id:
            d["status"] = "approved"
            d["approved_by"] = user["username"]
            return d
    raise HTTPException(status_code=404, detail="Draft not found")
