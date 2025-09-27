from __future__ import annotations
import time
from dataclasses import dataclass, asdict

@dataclass
class AuditRecord:
    run_id: str
    timestamp: float
    params: dict
    artifacts: dict
    input_fingerprint: dict

def new_audit(run_id: str, params: dict, artifacts: dict, input_fingerprint: dict):
    return AuditRecord(
        run_id=run_id,
        timestamp=time.time(),
        params=params,
        artifacts=artifacts,
        input_fingerprint=input_fingerprint,
    )

def to_json(rec: AuditRecord) -> dict:
    return asdict(rec)