"""
ONSA export — bundle audit records + proofs into a self-contained ZIP.
"""
from __future__ import annotations

import json
import os
import zipfile
from pathlib import Path

from openclaw.config import EXPORT_DIR
from openclaw.onsa.engine import ONSAEngine
from openclaw.onsa.verify import verify_chain


VERIFY_SCRIPT = '''\
#!/usr/bin/env python3
"""Standalone verifier — run this inside the exported audit package."""
import hashlib, json, sys

def compute_hash(rec):
    payload = json.dumps({
        "sequence": rec["sequence"],
        "chain_id": rec["chain_id"],
        "timestamp": rec["timestamp"],
        "actor": rec["actor"],
        "action": rec["action"],
        "evidence_hash": rec["evidence_hash"],
        "prev_hash": rec["prev_hash"],
    }, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode()).hexdigest()

def main():
    with open("records.jsonl", "r") as f:
        records = [json.loads(line) for line in f if line.strip()]
    if not records:
        print("No records found."); return
    prev_hash = records[0]["prev_hash"]
    for i, rec in enumerate(records):
        expected = compute_hash(rec)
        if expected != rec["current_hash"]:
            print(f"FAIL: Hash mismatch at sequence {rec['sequence']}")
            sys.exit(1)
        if rec["prev_hash"] != prev_hash:
            print(f"FAIL: Chain break at sequence {rec['sequence']}")
            sys.exit(1)
        prev_hash = rec["current_hash"]
    print(f"OK: All {len(records)} records verified.")

if __name__ == "__main__":
    main()
'''


def export_package(
    engine: ONSAEngine,
    chain_id: str,
    output_path: Path | str | None = None,
) -> Path:
    """Create a ZIP audit package for the given chain.

    Contents:
      records.jsonl     — all chain records
      chain_proof.json  — verification result + chain metadata
      verify.py         — standalone verification script
    """
    chain = engine.get_chain(chain_id)
    if chain is None:
        raise ValueError(f"Chain {chain_id} not found")

    if output_path is None:
        output_path = EXPORT_DIR / f"audit_{chain_id[:12]}.zip"
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    records = engine.get_records(chain_id)
    verification = verify_chain(engine, chain_id)

    proof = {
        "chain": chain.to_dict(),
        "verification": {
            "valid": verification.valid,
            "records_checked": verification.records_checked,
            "message": verification.message,
            "verified_at": verification.verified_at,
        },
    }

    with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zf:
        # Records
        lines = "\n".join(
            json.dumps(r.to_dict(), separators=(",", ":")) for r in records
        )
        zf.writestr("records.jsonl", lines + "\n")

        # Proof
        zf.writestr("chain_proof.json", json.dumps(proof, indent=2))

        # Standalone verifier
        zf.writestr("verify.py", VERIFY_SCRIPT)

    return output_path
