"""
ONSA Engine — SHA-256 hash-chain audit trail.

Each chain is stored as a JSON Lines file.  The engine appends records
atomically and maintains a head-hash for fast integrity checks.
"""
from __future__ import annotations

import hashlib
import json
import os
import threading
from pathlib import Path

from openclaw.config import ONSA_CHAINS_DIR
from openclaw.onsa.models import AuditAction, AuditChain, AuditRecord


class ONSAEngine:
    """Core audit engine — append-only hash chains."""

    def __init__(self, chains_dir: Path | None = None):
        self._dir = chains_dir or ONSA_CHAINS_DIR
        self._dir.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self._chains: dict[str, AuditChain] = {}
        self._load_chains()

    # ---- public API --------------------------------------------------

    def create_chain(
        self, tenant_id: str = "default", description: str = ""
    ) -> AuditChain:
        """Create a new, empty audit chain."""
        chain = AuditChain(tenant_id=tenant_id, description=description)
        self._chains[chain.chain_id] = chain
        self._save_chain_meta(chain)
        return chain

    def append(
        self,
        chain_id: str,
        action: str | AuditAction,
        actor: str,
        data: dict,
        metadata: dict | None = None,
    ) -> AuditRecord:
        """Append a new record to the chain.

        The record's ``current_hash`` is the SHA-256 of the canonical
        JSON representation of (evidence_hash + prev_hash + action +
        actor + timestamp + sequence).
        """
        action_str = action.value if isinstance(action, AuditAction) else action

        with self._lock:
            chain = self._chains.get(chain_id)
            if chain is None:
                raise ValueError(f"Chain {chain_id} not found")

            evidence_hash = self._hash_data(data)

            record = AuditRecord(
                sequence=chain.length,
                chain_id=chain_id,
                tenant_id=chain.tenant_id,
                actor=actor,
                action=action_str,
                evidence_hash=evidence_hash,
                prev_hash=chain.head_hash,
                metadata=metadata or {},
            )
            record.current_hash = self._compute_record_hash(record)

            # Persist record
            chain_file = self._chain_file(chain_id)
            with open(chain_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(record.to_dict(), separators=(",", ":")) + "\n")

            # Update chain head
            chain.head_hash = record.current_hash
            chain.length += 1
            self._save_chain_meta(chain)

            return record

    def get_chain(self, chain_id: str) -> AuditChain | None:
        return self._chains.get(chain_id)

    def list_chains(self, tenant_id: str | None = None) -> list[AuditChain]:
        chains = list(self._chains.values())
        if tenant_id:
            chains = [c for c in chains if c.tenant_id == tenant_id]
        return chains

    def get_records(
        self, chain_id: str, from_seq: int = 0, to_seq: int | None = None
    ) -> list[AuditRecord]:
        """Read records from the chain file."""
        chain_file = self._chain_file(chain_id)
        if not chain_file.exists():
            return []

        records: list[AuditRecord] = []
        with open(chain_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                rec = AuditRecord.from_dict(json.loads(line))
                if rec.sequence < from_seq:
                    continue
                if to_seq is not None and rec.sequence > to_seq:
                    break
                records.append(rec)
        return records

    # ---- hashing -----------------------------------------------------

    @staticmethod
    def _hash_data(data: dict) -> str:
        """SHA-256 of the canonical JSON representation of evidence data."""
        canonical = json.dumps(data, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(canonical.encode()).hexdigest()

    @staticmethod
    def _compute_record_hash(record: AuditRecord) -> str:
        """SHA-256 of the fields that constitute the chain link."""
        payload = json.dumps(
            {
                "sequence": record.sequence,
                "chain_id": record.chain_id,
                "timestamp": record.timestamp,
                "actor": record.actor,
                "action": record.action,
                "evidence_hash": record.evidence_hash,
                "prev_hash": record.prev_hash,
            },
            sort_keys=True,
            separators=(",", ":"),
        )
        return hashlib.sha256(payload.encode()).hexdigest()

    # ---- persistence helpers -----------------------------------------

    def _chain_file(self, chain_id: str) -> Path:
        return self._dir / f"{chain_id}.jsonl"

    def _meta_file(self, chain_id: str) -> Path:
        return self._dir / f"{chain_id}.meta.json"

    def _save_chain_meta(self, chain: AuditChain) -> None:
        with open(self._meta_file(chain.chain_id), "w", encoding="utf-8") as f:
            json.dump(chain.to_dict(), f, indent=2)

    def _load_chains(self) -> None:
        """Load all chain metadata from disk."""
        for meta_path in self._dir.glob("*.meta.json"):
            try:
                with open(meta_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                chain_id = data.get("chain_id", meta_path.stem.replace(".meta", ""))
                self._chains[chain_id] = AuditChain(
                    chain_id=chain_id,
                    tenant_id=data.get("tenant_id", "default"),
                    created_at=data.get("created_at", ""),
                    head_hash=data.get("head_hash", "0" * 64),
                    length=data.get("length", 0),
                    description=data.get("description", ""),
                )
            except Exception:
                continue
