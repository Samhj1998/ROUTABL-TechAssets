"""B3 schedule, pin, and shared-lock boundary. No operational adapters are shipped."""
import re
from backup_runner_candidate import (
    CAS_ID, SHA, SNAPSHOT, Inventory, Local, Nas, Stop, kst, matches,
    run_stages, valid_inventory,
)

PRIMARY = "com.routabl.assetbackup.native.v042"
PIN_NAMES = {"runner", "gate", "nas"}
RUN_ID = re.compile(r"B3-[0-9a-f]{32}")

def verify_pins(expected, observed):
    return (isinstance(expected, dict) and isinstance(observed, dict)
            and set(expected) == PIN_NAMES == set(observed)
            and all(matches(SHA, digest) for digest in expected.values())
            and expected == observed)

def supervised_run(port, run_id, entry, active_entries, expected_pins):
    events = []
    local = nas = None
    status, reason = "FAILED_SAFE", "ADAPTER_ERROR"

    def record(stage, code, exit_code=None, executed=None, evidence=None):
        stamp = kst(port.now()).isoformat()
        event = dict(run_id=run_id, at_kst=stamp, stage=stage, code=code,
                     exit_code=exit_code, executed=executed)
        inv = evidence.inventory if isinstance(evidence, Local) else evidence
        if isinstance(inv, Inventory) and valid_inventory(inv):
            event.update(manifest_name=inv.manifest_name, manifest_sha256=inv.manifest_sha256,
                         selection_sha256=inv.selection_sha256, selected_files=inv.file_count,
                         selected_bytes=inv.total_bytes)
        if isinstance(evidence, (Local, Nas)) and matches(SNAPSHOT, evidence.snapshot_id):
            event["snapshot_id"] = evidence.snapshot_id
        if isinstance(evidence, Local) and matches(SHA, evidence.receipt_sha256):
            event["local_receipt_sha256"] = evidence.receipt_sha256
        if isinstance(evidence, Nas):
            if matches(CAS_ID, evidence.cas_id):
                event["cas_id"] = evidence.cas_id
            if matches(SHA, evidence.local_receipt_sha256):
                event["local_receipt_sha256"] = evidence.local_receipt_sha256
        events.append(event)

    if not matches(RUN_ID, run_id):
        return dict(status="FAILED_SAFE", reason="INVALID_RUN_ID", events=[],
                    backup_executed=False, actual_backup_success=False)
    entered = False
    try:
        if not isinstance(active_entries, (tuple, list)) or tuple(active_entries) != (PRIMARY,) or entry != PRIMARY:
            raise Stop("FAILED_SAFE", "SCHEDULE_NOT_SINGLE_AUTHORIZED_ENTRY")
        with port.shared_lock() as acquired:
            if acquired is False:
                record("lock", "CONTENDED", executed=False)
                raise Stop("SKIPPED_LOCK_HELD", "SHARED_LOCK_HELD")
            if acquired is not True:
                raise Stop("FAILED_SAFE", "INVALID_LOCK_ATTESTATION")
            entered = True
            start = kst(port.now())
            record("lock", "ACQUIRED", executed=False)
            if not verify_pins(expected_pins, port.program_pins()):
                raise Stop("FAILED_SAFE", "PROGRAM_PIN_MISMATCH")
            record("preflight", "PINS_VERIFIED", executed=True)
            status, local, nas = run_stages(port, start, record)
            reason = "VERIFIED"
    except Stop as error:
        status, reason = error.status, error.reason
    except TimeoutError:
        status, reason = "FAILED_SAFE", "TIMEOUT"
    except Exception:
        status, reason = "FAILED_SAFE", "ADAPTER_ERROR"
    try:
        record("outcome", reason)
    except Exception:
        status, reason = "FAILED_SAFE", "OUTCOME_EVIDENCE_UNAVAILABLE"
    attempted = [e for e in events if e["stage"] in ("local", "nas")]
    if any(e["executed"] is True for e in attempted):
        executed = True
    elif any(e["executed"] is None for e in attempted) or (
            entered and reason in ("ADAPTER_ERROR", "TIMEOUT", "OUTCOME_EVIDENCE_UNAVAILABLE")):
        executed = None
    else:
        executed = False
    result = dict(status=status, reason=reason, events=events, backup_executed=executed,
                  actual_backup_success=status == "NEW_BACKUP_VERIFIED")
    if status in ("NEW_BACKUP_VERIFIED", "CURRENT_BACKUP_ALREADY_VERIFIED"):
        result.update(snapshot_id=local.snapshot_id, local_receipt_sha256=local.receipt_sha256,
                      nas_cas_id=nas.cas_id)
    return result
