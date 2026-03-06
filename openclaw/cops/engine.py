"""
COPS Engine — Correlation & Orchestration for Proactive Security.

Orchestrates the full flow: scan results -> scoring -> incident
management -> threshold alerts.
"""
from __future__ import annotations

import json
from dataclasses import asdict

from openclaw.bridge.scanner import ScanFinding, ScanResult
from openclaw.cops.scorer import MaterialityScore, score_findings
from openclaw.cops.state_machine import IncidentState, IncidentStateMachine
from openclaw.cops.timeline import build_timeline, TimelineEvent
from openclaw.onsa.engine import ONSAEngine
from openclaw.onsa.models import AuditAction
from openclaw.config import MATERIALITY_THRESHOLD


class COPSEngine:
    """Central orchestrator for the COPS subsystem."""

    def __init__(self, onsa: ONSAEngine):
        self.onsa = onsa

    def process_scan(
        self,
        scan_result: ScanResult,
        chain_id: str,
        actor: str = "cops",
    ) -> tuple[MaterialityScore, str]:
        """Process scan results: score findings and log to ONSA.

        Returns (MaterialityScore, incident_state_suggestion).
        """
        # Score findings
        mat_score = score_findings(scan_result.findings)

        # Log score to audit chain
        self.onsa.append(
            chain_id,
            AuditAction.SCORE_CALCULATED,
            actor=actor,
            data={
                "score": mat_score.score,
                "level": mat_score.level,
                "findings_count": mat_score.breakdown.findings_count,
            },
            metadata={
                "score": mat_score.score,
                "level": mat_score.level,
            },
        )

        # Determine suggested state based on score
        suggested_state = self._suggest_state(mat_score)

        return mat_score, suggested_state

    def recalculate_score(
        self,
        findings: list[ScanFinding],
        chain_id: str,
        actor: str = "cops",
    ) -> MaterialityScore:
        """Re-run scorer on a set of findings and log the update."""
        mat_score = score_findings(findings)

        self.onsa.append(
            chain_id,
            AuditAction.SCORE_UPDATED,
            actor=actor,
            data={
                "score": mat_score.score,
                "level": mat_score.level,
                "findings_count": mat_score.breakdown.findings_count,
            },
            metadata={
                "score": mat_score.score,
                "level": mat_score.level,
            },
        )

        return mat_score

    def check_thresholds(self, score: MaterialityScore) -> bool:
        """Return True if the score crosses the materiality threshold."""
        return score.score >= MATERIALITY_THRESHOLD

    def transition_incident(
        self,
        chain_id: str,
        current_state: str,
        target_state: str,
        actor: str = "system",
    ) -> bool:
        """Attempt a state transition and log it to ONSA."""
        result = IncidentStateMachine.transition(current_state, target_state, actor)

        self.onsa.append(
            chain_id,
            AuditAction.INCIDENT_STATE_CHANGED,
            actor=actor,
            data={
                "from_state": result.from_state,
                "to_state": result.to_state,
                "success": result.success,
                "message": result.message,
            },
            metadata={
                "from_state": result.from_state,
                "to_state": result.to_state,
            },
        )

        return result.success

    def get_timeline(self, chain_id: str) -> list[TimelineEvent]:
        """Build the timeline for an incident chain."""
        return build_timeline(self.onsa, chain_id)

    @staticmethod
    def _suggest_state(score: MaterialityScore) -> str:
        """Suggest an incident state based on the materiality score."""
        if score.level == "critical":
            return IncidentState.MATERIAL_LIKELY.value
        if score.level == "high":
            return IncidentState.ASSESSING.value
        if score.level == "medium":
            return IncidentState.INVESTIGATING.value
        return IncidentState.MONITORING.value
