"""Isolated B3 state machine. Adapters supply attestations; this module has no I/O."""
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import re

KST = timezone(timedelta(hours=9))
SHA = re.compile(r"[0-9a-f]{64}")
MANIFEST = re.compile(r"asset_manifest_v0\.[0-9]+\.json")
SNAPSHOT = re.compile(r"ASSET_V21_[0-9]{8}_[0-9]{6}_KST_[0-9]+")
CAS_ID = re.compile(r"[A-Za-z0-9_-]{1,100}")

@dataclass(frozen=True)
class Inventory:
    manifest_name: str
    manifest_sha256: str
    selection_sha256: str
    file_count: int
    total_bytes: int

@dataclass(frozen=True)
class Local:
    inventory: Inventory
    snapshot_id: str
    created_at: datetime
    receipt_sha256: str
    locked: bool
    sha_verified: bool

@dataclass(frozen=True)
class Nas:
    cas_id: str
    snapshot_id: str
    local_receipt_sha256: str
    manifest_sha256: str
    selection_sha256: str
    completed: bool

@dataclass(frozen=True)
class Step:
    code: str
    exit_code: int
    executed: bool
    evidence: object = None

class Stop(Exception):
    def __init__(self, status, reason):
        self.status, self.reason = status, reason

def matches(pattern, value):
    return isinstance(value, str) and pattern.fullmatch(value) is not None

def valid_inventory(value):
    return (isinstance(value, Inventory) and matches(MANIFEST, value.manifest_name)
            and matches(SHA, value.manifest_sha256) and matches(SHA, value.selection_sha256)
            and type(value.file_count) is int and value.file_count > 0
            and type(value.total_bytes) is int and value.total_bytes > 0)

def kst(value):
    if not isinstance(value, datetime) or value.utcoffset() is None:
        raise Stop("FAILED_SAFE", "INVALID_TIMESTAMP")
    return value.astimezone(KST)

def stage(adapter, name, record, allowed, *args):
    try:
        result = adapter(*args)
    except TimeoutError:
        record(name, "TIMEOUT", executed=None)
        raise Stop("FAILED_SAFE", "TIMEOUT")
    except Exception:
        record(name, "ADAPTER_ERROR", executed=None)
        raise Stop("FAILED_SAFE", "ADAPTER_ERROR")
    if (not isinstance(result, Step) or type(result.exit_code) is not int
            or type(result.executed) is not bool or not isinstance(result.code, str)):
        record(name, "INVALID_RESULT", executed=None)
        raise Stop("FAILED_SAFE", "INVALID_STAGE_RESULT")
    code = result.code if result.code in allowed else "UNRECOGNIZED_STAGE_CODE"
    record(name, code, result.exit_code, result.executed, result.evidence)
    if result.exit_code != 0:
        raise Stop("FAILED_SAFE", "CHILD_NONZERO")
    if code == "UNRECOGNIZED_STAGE_CODE":
        raise Stop("FAILED_SAFE", "UNKNOWN_STAGE_CODE")
    return result

def verify_local(local, current, start, now, created, previous):
    if (not isinstance(local, Local) or not matches(SNAPSHOT, local.snapshot_id)
            or not matches(SHA, local.receipt_sha256) or not valid_inventory(local.inventory)
            or local.locked is not True or local.sha_verified is not True):
        raise Stop("FAILED_SAFE", "LOCAL_EVIDENCE_INVALID")
    if local.inventory != current:
        raise Stop("STALE_REGISTRY_BACKUP", "LOCAL_INVENTORY_MISMATCH")
    stamp = kst(local.created_at)
    if stamp.date() != start.date():
        raise Stop("STALE_REGISTRY_BACKUP", "LOCAL_NOT_SAME_KST_DAY")
    if created and (not start <= stamp <= now or
                    (previous is not None and previous.snapshot_id == local.snapshot_id)):
        raise Stop("NO_NEW_BACKUP_EVIDENCE", "SNAPSHOT_NOT_NEW")
    if not created and (stamp > start or previous != local):
        raise Stop("NO_NEW_BACKUP_EVIDENCE", "REUSE_NOT_PREEXISTING")

def verify_nas(nas, local):
    if (not isinstance(nas, Nas) or not matches(CAS_ID, nas.cas_id) or nas.completed is not True
            or (nas.snapshot_id, nas.local_receipt_sha256, nas.manifest_sha256,
                nas.selection_sha256) != (local.snapshot_id, local.receipt_sha256,
                                          local.inventory.manifest_sha256,
                                          local.inventory.selection_sha256)):
        raise Stop("NAS_CHAIN_NOT_VERIFIED", "NAS_EVIDENCE_MISSING_OR_MISMATCH")

def run_stages(port, start, record):
    current = port.inventory()
    if not valid_inventory(current):
        raise Stop("FAILED_SAFE", "CURRENT_INVENTORY_INVALID")
    previous = port.previous_local()
    if previous is not None and not isinstance(previous, Local):
        raise Stop("FAILED_SAFE", "PREVIOUS_LOCAL_INVALID")
    previous_nas = port.previous_nas()
    record("baseline", "INVENTORY_READ", evidence=current)
    local_step = stage(port.local, "local", record,
                       {"CREATED", "ALREADY_VERIFIED", "LOCK_HELD", "NO_WORK", "FAILED"}, current)
    if local_step.code == "LOCK_HELD" and not local_step.executed:
        raise Stop("SKIPPED_LOCK_HELD", "CHILD_LOCK_HELD")
    created = local_step.code == "CREATED" and local_step.executed
    reused = local_step.code == "ALREADY_VERIFIED" and not local_step.executed
    if not created and not reused:
        if local_step.code == "FAILED" or local_step.executed or local_step.code == "ALREADY_VERIFIED":
            raise Stop("FAILED_SAFE", "LOCAL_RESULT_CONTRADICTORY_OR_FAILED")
        raise Stop("NO_NEW_BACKUP_EVIDENCE", "LOCAL_WORK_NOT_PROVEN")
    local = local_step.evidence
    verify_local(local, current, start, kst(port.now()), created, previous)
    nas_step = stage(port.nas, "nas", record,
                     {"REPLICATED", "ALREADY_VERIFIED", "MISSING", "FAILED"}, local, created)
    if (nas_step.code, nas_step.executed) != (
            ("REPLICATED", True) if created else ("ALREADY_VERIFIED", False)):
        raise Stop("NAS_CHAIN_NOT_VERIFIED", "NAS_WORK_STATE_MISMATCH")
    nas = nas_step.evidence
    verify_nas(nas, local)
    if reused and previous_nas != nas:
        raise Stop("NAS_CHAIN_NOT_VERIFIED", "NAS_REUSE_NOT_PREEXISTING")
    final = stage(port.final, "final", record, {"CHAIN_VERIFIED", "FAILED"}, current, local, nas)
    if final.code != "CHAIN_VERIFIED" or not final.executed or final.evidence is not True:
        raise Stop("NAS_CHAIN_NOT_VERIFIED", "FINAL_ATTESTATION_MISSING")
    end_inventory = port.inventory()
    if not valid_inventory(end_inventory) or current != end_inventory:
        raise Stop("FAILED_SAFE", "INVENTORY_CHANGED")
    if kst(port.now()).date() != start.date():
        raise Stop("FAILED_SAFE", "RUN_CROSSED_KST_DATE")
    record("decision", "CHAIN_AND_INVENTORY_VERIFIED", 0, True, local)
    return ("NEW_BACKUP_VERIFIED" if created else "CURRENT_BACKUP_ALREADY_VERIFIED", local, nas)
