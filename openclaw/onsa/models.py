"""
ONSA data models — immutable audit records and chains.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum


class AuditAction(str, Enum):
    """Well-known audit event types."""
    SCAN_STARTED = "scan.started"
    SCAN_COMPLETED = "scan.completed"
    FINDING_RECORDED = "finding.recorded"
    INCIDENT_CREATED = "incident.created"
    INCIDENT_STATE_CHANGED = "incident.state_changed"
    SCORE_CALCULATED = "score.calculated"
    SCORE_UPDATED = "score.updated"
    DRAFT_GENERATED = "draft.generated"
    DRAFT_EDITED = "draft.edited"
    DRAFT_APPROVED = "draft.approved"
    HUMAN_DECISION = "human.decision"
    EXPORT_CREATED = "export.created"
    CHAIN_VERIFIED = "chain.verified"


@dataclass
class AuditRecord:
    """A single immutable entry in an ONSA hash chain."""
    record_id: str = field(default_factory=lambda: uuid.uuid4().hex)
    sequence: int = 0
    chain_id: str = ""
    tenant_id: str = "default"
    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    actor: str = "system"
    action: str = ""
    evidence_hash: str = ""
    prev_hash: str = "0" * 64
    current_hash: str = ""
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "record_id": self.record_id,
            "sequence": self.sequence,
            "chain_id": self.chain_id,
            "tenant_id": self.tenant_id,
            "timestamp": self.timestamp,
            "actor": self.actor,
            "action": self.action,
            "evidence_hash": self.evidence_hash,
            "prev_hash": self.prev_hash,
            "current_hash": self.current_hash,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, d: dict) -> AuditRecord:
        return cls(**{k: v for k, v in d.items() if k in cls.__dataclass_fields__})


@dataclass
class AuditChain:
    """Metadata about a hash chain."""
    chain_id: str = field(default_factory=lambda: uuid.uuid4().hex)
    tenant_id: str = "default"
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    head_hash: str = "0" * 64
    length: int = 0
    description: str = ""

    def to_dict(self) -> dict:
        return {
            "chain_id": self.chain_id,
            "tenant_id": self.tenant_id,
            "created_at": self.created_at,
            "head_hash": self.head_hash,
            "length": self.length,
            "description": self.description,
        }


@dataclass
class VerificationResult:
    """Outcome of a chain verification."""
    chain_id: str = ""
    valid: bool = True
    records_checked: int = 0
    first_invalid_seq: int | None = None
    message: str = ""
    verified_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
