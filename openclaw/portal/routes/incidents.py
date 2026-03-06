"""
Incident routes — CRUD, timeline, scoring.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from openclaw.portal.routes.auth import get_current_user
from openclaw.cops.state_machine import IncidentStateMachine, IncidentState
from openclaw.portal import app as portal_app

router = APIRouter()

# In-memory incident store (replace with DB queries in production)
_incidents: dict[str, dict] = {}


class IncidentCreate(BaseModel):
    title: str
    description: str = ""
    tenant_id: str = "default"


class IncidentResponse(BaseModel):
    id: str
    title: str
    description: str
    state: str
    materiality_score: float
    chain_id: str
    tenant_id: str


class StateTransitionRequest(BaseModel):
    target_state: str


@router.get("")
async def list_incidents(user: dict = Depends(get_current_user)):
    """List all incidents."""
    return list(_incidents.values())


@router.get("/{incident_id}")
async def get_incident(incident_id: str, user: dict = Depends(get_current_user)):
    """Get incident details with timeline."""
    incident = _incidents.get(incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")

    # Build timeline if chain exists
    timeline = []
    if incident.get("chain_id") and portal_app.onsa_engine:
        from openclaw.cops.timeline import build_timeline
        events = build_timeline(portal_app.onsa_engine, incident["chain_id"])
        timeline = [
            {
                "timestamp": e.timestamp,
                "action": e.action,
                "actor": e.actor,
                "description": e.description,
                "significance": e.significance,
            }
            for e in events
        ]

    return {**incident, "timeline": timeline}


@router.post("")
async def create_incident(body: IncidentCreate, user: dict = Depends(get_current_user)):
    """Create a new incident."""
    import uuid

    incident_id = uuid.uuid4().hex[:12]

    # Create ONSA chain
    chain_id = ""
    if portal_app.onsa_engine:
        chain = portal_app.onsa_engine.create_chain(
            tenant_id=body.tenant_id,
            description=f"Incident: {body.title}",
        )
        chain_id = chain.chain_id
        portal_app.onsa_engine.append(
            chain_id, "incident.created", actor=user["username"],
            data={"title": body.title, "description": body.description},
        )

    incident = {
        "id": incident_id,
        "title": body.title,
        "description": body.description,
        "state": IncidentState.MONITORING.value,
        "materiality_score": 0.0,
        "chain_id": chain_id,
        "tenant_id": body.tenant_id,
    }
    _incidents[incident_id] = incident
    return incident


@router.post("/{incident_id}/transition")
async def transition_state(
    incident_id: str,
    body: StateTransitionRequest,
    user: dict = Depends(get_current_user),
):
    """Transition an incident to a new state."""
    incident = _incidents.get(incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")

    if portal_app.cops_engine:
        success = portal_app.cops_engine.transition_incident(
            chain_id=incident["chain_id"],
            current_state=incident["state"],
            target_state=body.target_state,
            actor=user["username"],
        )
    else:
        result = IncidentStateMachine.transition(
            incident["state"], body.target_state, user["username"]
        )
        success = result.success

    if not success:
        allowed = IncidentStateMachine.get_allowed_transitions(incident["state"])
        raise HTTPException(
            status_code=400,
            detail=f"Invalid transition. Allowed: {allowed}",
        )

    incident["state"] = body.target_state
    return incident


@router.get("/{incident_id}/score")
async def get_score(incident_id: str, user: dict = Depends(get_current_user)):
    """Get materiality score breakdown."""
    incident = _incidents.get(incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")

    return {
        "incident_id": incident_id,
        "score": incident.get("materiality_score", 0.0),
        "state": incident.get("state"),
    }
