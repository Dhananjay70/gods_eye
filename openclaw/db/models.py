"""
ORM models for Openclaw — persisted in SQLite via SQLAlchemy.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from openclaw.db.database import Base


def _uuid() -> str:
    return uuid.uuid4().hex


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Tenant(Base):
    __tablename__ = "tenants"

    id = Column(String(32), primary_key=True, default=_uuid)
    name = Column(String(255), nullable=False, unique=True)
    created_at = Column(DateTime, default=_utcnow)

    users = relationship("User", back_populates="tenant")
    incidents = relationship("Incident", back_populates="tenant")


class User(Base):
    __tablename__ = "users"

    id = Column(String(32), primary_key=True, default=_uuid)
    tenant_id = Column(String(32), ForeignKey("tenants.id"), nullable=False)
    username = Column(String(100), nullable=False, unique=True)
    email = Column(String(255), nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(20), nullable=False, default="analyst")  # analyst, legal, executive, admin
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=_utcnow)

    tenant = relationship("Tenant", back_populates="users")


class Incident(Base):
    __tablename__ = "incidents"

    id = Column(String(32), primary_key=True, default=_uuid)
    tenant_id = Column(String(32), ForeignKey("tenants.id"), nullable=False)
    title = Column(String(500), nullable=False)
    description = Column(Text, default="")
    state = Column(String(30), nullable=False, default="monitoring")
    materiality_score = Column(Float, default=0.0)
    chain_id = Column(String(32), default="")
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)

    tenant = relationship("Tenant", back_populates="incidents")
    scan_results = relationship("ScanResultRecord", back_populates="incident")
    drafts = relationship("DisclosureDraft", back_populates="incident")


class ScanResultRecord(Base):
    __tablename__ = "scan_results"

    id = Column(String(32), primary_key=True, default=_uuid)
    incident_id = Column(String(32), ForeignKey("incidents.id"), nullable=True)
    scan_id = Column(String(64), nullable=False)
    url = Column(String(2048), nullable=False)
    status = Column(String(10), default="0")
    sec_grade = Column(String(2), default="F")
    techs = Column(Text, default="")  # JSON-encoded list
    category = Column(String(100), default="")
    title = Column(String(500), default="")
    diff_severity = Column(String(20), default="")
    output_dir = Column(String(1024), default="")
    raw_json = Column(Text, default="")  # Full result dict
    created_at = Column(DateTime, default=_utcnow)

    incident = relationship("Incident", back_populates="scan_results")


class AuditRecordDB(Base):
    """Index into ONSA chain records for fast lookup (source of truth is JSONL)."""
    __tablename__ = "audit_records"

    id = Column(String(32), primary_key=True, default=_uuid)
    chain_id = Column(String(32), nullable=False, index=True)
    sequence = Column(Integer, nullable=False)
    action = Column(String(50), nullable=False)
    actor = Column(String(100), nullable=False)
    current_hash = Column(String(64), nullable=False)
    timestamp = Column(String(30), nullable=False)


class DisclosureDraft(Base):
    __tablename__ = "disclosure_drafts"

    id = Column(String(32), primary_key=True, default=_uuid)
    incident_id = Column(String(32), ForeignKey("incidents.id"), nullable=False)
    version = Column(Integer, default=1)
    status = Column(String(20), default="draft")  # draft, review, approved, filed
    nature_and_scope = Column(Text, default="")
    data_impact = Column(Text, default="")
    material_impact = Column(Text, default="")
    remediation = Column(Text, default="")
    confidence_scores = Column(Text, default="")  # JSON
    llm_model_used = Column(String(100), default="")
    created_by = Column(String(100), default="system")
    created_at = Column(DateTime, default=_utcnow)

    incident = relationship("Incident", back_populates="drafts")
