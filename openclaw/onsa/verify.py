"""
ONSA chain verification — proves that no record has been tampered with.
"""
from __future__ import annotations

from openclaw.onsa.engine import ONSAEngine
from openclaw.onsa.models import AuditRecord, VerificationResult


def verify_record(record: AuditRecord) -> bool:
    """Re-compute a single record's hash and compare."""
    expected = ONSAEngine._compute_record_hash(record)
    return expected == record.current_hash


def verify_chain(
    engine: ONSAEngine,
    chain_id: str,
    from_seq: int = 0,
    to_seq: int | None = None,
) -> VerificationResult:
    """Walk the chain and verify every link.

    Checks:
    1. Each record's hash matches its recomputed value.
    2. Each record's prev_hash matches the previous record's current_hash.
    3. Sequence numbers are contiguous.
    """
    chain = engine.get_chain(chain_id)
    if chain is None:
        return VerificationResult(
            chain_id=chain_id,
            valid=False,
            message=f"Chain {chain_id} not found",
        )

    records = engine.get_records(chain_id, from_seq, to_seq)
    if not records:
        return VerificationResult(
            chain_id=chain_id,
            valid=True,
            records_checked=0,
            message="Chain is empty — nothing to verify",
        )

    prev_hash = records[0].prev_hash
    for i, rec in enumerate(records):
        # Check contiguous sequence
        expected_seq = from_seq + i
        if rec.sequence != expected_seq:
            return VerificationResult(
                chain_id=chain_id,
                valid=False,
                records_checked=i,
                first_invalid_seq=rec.sequence,
                message=f"Sequence gap: expected {expected_seq}, got {rec.sequence}",
            )

        # Check hash integrity
        if not verify_record(rec):
            return VerificationResult(
                chain_id=chain_id,
                valid=False,
                records_checked=i,
                first_invalid_seq=rec.sequence,
                message=f"Hash mismatch at sequence {rec.sequence}",
            )

        # Check chain linkage
        if rec.prev_hash != prev_hash:
            return VerificationResult(
                chain_id=chain_id,
                valid=False,
                records_checked=i,
                first_invalid_seq=rec.sequence,
                message=f"Chain break at sequence {rec.sequence}: prev_hash does not match",
            )

        prev_hash = rec.current_hash

    return VerificationResult(
        chain_id=chain_id,
        valid=True,
        records_checked=len(records),
        message=f"All {len(records)} records verified successfully",
    )
