"""
COPS Timeline Builder — aggregates events into a chronological timeline
for an incident.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from openclaw.onsa.engine import ONSAEngine
from openclaw.onsa.models import AuditRecord


@dataclass
class TimelineEvent:
    """A single event in an incident timeline."""
    timestamp: str
    action: str
    actor: str
    description: str
    significance: str = "info"  # info, warning, critical
    evidence_refs: list[str] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)


# Map audit actions to human-readable descriptions + significance
ACTION_DESCRIPTIONS: dict[str, tuple[str, str]] = {
    "scan.started": ("Security scan initiated", "info"),
    "scan.completed": ("Security scan completed", "info"),
    "finding.recorded": ("Security finding recorded", "info"),
    "incident.created": ("Incident created", "warning"),
    "incident.state_changed": ("Incident state changed", "warning"),
    "score.calculated": ("Materiality score calculated", "info"),
    "score.updated": ("Materiality score updated", "warning"),
    "draft.generated": ("Disclosure draft generated", "warning"),
    "draft.edited": ("Disclosure draft edited", "info"),
    "draft.approved": ("Disclosure draft approved", "critical"),
    "human.decision": ("Human decision recorded", "critical"),
    "export.created": ("Audit package exported", "info"),
    "chain.verified": ("Chain integrity verified", "info"),
}


def _record_to_event(record: AuditRecord) -> TimelineEvent:
    """Convert an ONSA audit record to a timeline event."""
    desc_template, significance = ACTION_DESCRIPTIONS.get(
        record.action, (record.action, "info")
    )

    # Enrich description with metadata
    meta = record.metadata or {}
    description = desc_template
    if record.action == "finding.recorded":
        url = meta.get("url", "")
        grade = meta.get("sec_grade", "")
        if url:
            description = f"Finding: {url} (grade: {grade})"
    elif record.action == "incident.state_changed":
        from_s = meta.get("from_state", "")
        to_s = meta.get("to_state", "")
        description = f"State: {from_s} -> {to_s}"
    elif record.action == "score.calculated" or record.action == "score.updated":
        score = meta.get("score", "")
        level = meta.get("level", "")
        description = f"Materiality: {score} ({level})"
        if level in ("high", "critical"):
            significance = "critical"

    return TimelineEvent(
        timestamp=record.timestamp,
        action=record.action,
        actor=record.actor,
        description=description,
        significance=significance,
        evidence_refs=[record.current_hash],
        metadata=meta,
    )


def build_timeline(
    engine: ONSAEngine,
    chain_id: str,
) -> list[TimelineEvent]:
    """Build a chronological timeline from all records in a chain."""
    records = engine.get_records(chain_id)
    events = [_record_to_event(r) for r in records]
    events.sort(key=lambda e: e.timestamp)
    return events
