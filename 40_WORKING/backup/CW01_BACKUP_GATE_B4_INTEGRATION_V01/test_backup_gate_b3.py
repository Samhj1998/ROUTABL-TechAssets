"""Run with python3 -B. All inputs, lock state and stage results live in memory."""
from contextlib import contextmanager
from dataclasses import replace
from datetime import datetime, timedelta
import json
from uuid import uuid4

from backup_runner_candidate import Inventory, Local, Nas, Step, KST
from backup_supervisor_candidate import PRIMARY, supervised_run

START = datetime(2026, 11, 7, 4, 30, tzinfo=KST)
PINS = dict(runner="1"*64, gate="2"*64, nas="3"*64)
CURRENT = Inventory("asset_manifest_v0.27.json", "a"*64, "b"*64, 162, 84000)
OLD = Inventory("asset_manifest_v0.19.json", "c"*64, "d"*64, 130, 74000)
V028 = Inventory("asset_manifest_v0.28.json", "e"*64, "f"*64, 164, 89000)
NEW = Local(CURRENT, "ASSET_V21_20261107_043001_KST_101",
            START + timedelta(seconds=1), "4"*64, True, True)
SAME_DAY = replace(NEW, snapshot_id="ASSET_V21_20261107_042901_KST_102",
                   created_at=START - timedelta(seconds=59))
YESTERDAY = replace(SAME_DAY, snapshot_id="ASSET_V21_20261106_043146_KST_59950",
                    created_at=START - timedelta(days=1))
OLD_RECEIPT = replace(YESTERDAY, inventory=OLD)
V02 = "com.routabl.assetbackup.native.v02"

def chain(local):
    return Nas("CAS-" + local.snapshot_id, local.snapshot_id, local.receipt_sha256,
               local.inventory.manifest_sha256, local.inventory.selection_sha256, True)

class SimulatedLock:
    def __init__(self, held=False):
        self.held = held

    @contextmanager
    def enter(self):
        if self.held:
            yield False
            return
        self.held = True
        try:
            yield True
        finally:
            self.held = False

class FakePort:
    def __init__(self):
        self.lock = SimulatedLock()
        self.local_result = Step("CREATED", 0, True, NEW)
        self.nas_result = Step("REPLICATED", 0, True, chain(NEW))
        self.final_result = Step("CHAIN_VERIFIED", 0, True, True)
        self.known_local = self.known_nas = None
        self.current = self.after = CURRENT
        self.calls = []
        self.tick = -1
        self.inventory_reads = 0
        self.pins = dict(PINS)
        self.overlap = None
        self.overlap_result = None

    def now(self):
        self.tick += 1
        return START + timedelta(seconds=self.tick)

    def shared_lock(self):
        return self.lock.enter()

    def program_pins(self):
        return self.pins

    def inventory(self):
        self.inventory_reads += 1
        return self.current if self.inventory_reads == 1 else self.after

    def previous_local(self):
        return self.known_local

    def previous_nas(self):
        return self.known_nas

    def local(self, inventory):
        self.calls.append("local")
        if self.overlap is not None:
            self.overlap_result = execute(self.overlap)
        if isinstance(self.local_result, Exception):
            raise self.local_result
        return self.local_result

    def nas(self, local, created):
        self.calls.append("nas")
        return self.nas_result

    def final(self, inventory, local, nas):
        self.calls.append("final")
        return self.final_result

    def reuse(self, local):
        self.known_local, self.known_nas = local, chain(local)
        self.local_result = Step("ALREADY_VERIFIED", 0, False, local)
        self.nas_result = Step("ALREADY_VERIFIED", 0, False, self.known_nas)

def execute(port, active=(PRIMARY,)):
    return supervised_run(port, "B3-" + uuid4().hex, PRIMARY, active, PINS)

def test_cases():
    yield "01", "Current inventory, new local receipt, new linked CAS, final attestation", FakePort(), {}, "NEW_BACKUP_VERIFIED", "VERIFIED", ("local", "nas", "final"), True
    p = FakePort(); p.reuse(SAME_DAY)
    yield "02", "Preexisting, unchanged same-day local receipt and CAS", p, {}, "CURRENT_BACKUP_ALREADY_VERIFIED", "VERIFIED", ("local", "nas", "final"), False
    p = FakePort(); p.lock.held = True
    yield "03", "Shared execution lock held before entry", p, {}, "SKIPPED_LOCK_HELD", "SHARED_LOCK_HELD", (), False
    p = FakePort(); p.local_result = Step("NO_WORK", 0, False)
    yield "04", "Child exit=0 and backup_executed=false with no verified reuse", p, {}, "NO_NEW_BACKUP_EVIDENCE", "LOCAL_WORK_NOT_PROVEN", ("local",), False
    p = FakePort(); p.reuse(YESTERDAY)
    yield "05", "Yesterday's snapshot claims successful reuse even with latest inventory", p, {}, "STALE_REGISTRY_BACKUP", "LOCAL_NOT_SAME_KST_DAY", ("local",), False
    p = FakePort(); p.local_result = replace(p.local_result, evidence=replace(NEW, inventory=replace(CURRENT, manifest_sha256="0"*64)))
    yield "06", "Manifest SHA-256 differs from current inventory", p, {}, "STALE_REGISTRY_BACKUP", "LOCAL_INVENTORY_MISMATCH", ("local",), True
    p = FakePort(); p.local_result = replace(p.local_result, evidence=replace(NEW, inventory=replace(CURRENT, selection_sha256="0"*64)))
    yield "07", "Selection SHA-256 differs from current inventory", p, {}, "STALE_REGISTRY_BACKUP", "LOCAL_INVENTORY_MISMATCH", ("local",), True
    p = FakePort(); p.nas_result = Step("MISSING", 0, False)
    yield "08", "Missing NAS receipt", p, {}, "NAS_CHAIN_NOT_VERIFIED", "NAS_WORK_STATE_MISMATCH", ("local", "nas"), True
    p = FakePort(); p.nas_result = replace(p.nas_result, evidence=replace(chain(NEW), local_receipt_sha256="0"*64))
    yield "09", "NAS CAS points at a different local receipt hash", p, {}, "NAS_CHAIN_NOT_VERIFIED", "NAS_EVIDENCE_MISSING_OR_MISMATCH", ("local", "nas"), True
    yield "10", "Both native schedule labels are enabled", FakePort(), {"active": (PRIMARY, V02)}, "FAILED_SAFE", "SCHEDULE_NOT_SINGLE_AUTHORIZED_ENTRY", (), False
    p = FakePort(); p.pins["gate"] = "0"*64
    yield "11", "Approved Gate SHA-256 pin mismatch", p, {}, "FAILED_SAFE", "PROGRAM_PIN_MISMATCH", (), False
    p = FakePort(); p.local_result = Step("FAILED", 7, False)
    yield "12", "Nonzero child exit", p, {}, "FAILED_SAFE", "CHILD_NONZERO", ("local",), False
    p = FakePort(); p.local_result = TimeoutError("MOCK_PRIVATE_OUTPUT")
    yield "13", "Child timeout with unknown side effects; exception text withheld", p, {}, "FAILED_SAFE", "TIMEOUT", ("local",), None
    p = FakePort(); p.reuse(OLD_RECEIPT); p.local_result = Step("LOCK_HELD", 0, False, OLD_RECEIPT)
    yield "14", "11/7 defect simulation: shared child lock, exit 0, valid stale v0.19 local/CAS pair", p, {}, "SKIPPED_LOCK_HELD", "CHILD_LOCK_HELD", ("local",), False
    p = FakePort(); p.overlap = FakePort(); p.overlap.lock = p.lock
    yield "15", "Second invocation during first holder's local stage shares the same lock", p, {}, "NEW_BACKUP_VERIFIED", "VERIFIED", ("local", "nas", "final"), True
    p = FakePort(); p.after = V028
    yield "16", "Inventory changes after local and NAS phases", p, {}, "FAILED_SAFE", "INVENTORY_CHANGED", ("local", "nas", "final"), True
    p = FakePort(); p.local_result = replace(p.local_result, evidence=replace(NEW, locked=False))
    yield "17", "Local receipt was never locked", p, {}, "FAILED_SAFE", "LOCAL_EVIDENCE_INVALID", ("local",), True
    p = FakePort(); p.local_result = replace(p.local_result, evidence=replace(NEW, inventory=replace(CURRENT, total_bytes=83000)))
    yield "18", "Selected bytes differ even with matching digests", p, {}, "STALE_REGISTRY_BACKUP", "LOCAL_INVENTORY_MISMATCH", ("local",), True
    p = FakePort(); p.final_result = Step("CHAIN_VERIFIED", 0, True, False)
    yield "19", "Final stage did not attest the chain", p, {}, "NAS_CHAIN_NOT_VERIFIED", "FINAL_ATTESTATION_MISSING", ("local", "nas", "final"), True
    p = FakePort(); p.current = p.after = V028
    candidate = replace(NEW, inventory=V028)
    p.local_result = replace(p.local_result, evidence=candidate)
    p.nas_result = replace(p.nas_result, evidence=chain(candidate))
    yield "20", "Virtual 164-entry v0.28 contract compatibility", p, {}, "NEW_BACKUP_VERIFIED", "VERIFIED", ("local", "nas", "final"), True
    p = FakePort(); p.known_local = NEW
    yield "21", "Previously observed snapshot identifier claimed as new", p, {}, "NO_NEW_BACKUP_EVIDENCE", "SNAPSHOT_NOT_NEW", ("local",), True
    p = FakePort(); p.reuse(SAME_DAY); p.known_nas = None
    yield "22", "CAS claimed as already verified without baseline CAS evidence", p, {}, "NAS_CHAIN_NOT_VERIFIED", "NAS_REUSE_NOT_PREEXISTING", ("local", "nas"), False

def run():
    cases = []
    for number, input_condition, port, kwargs, expected, reason, calls, executed in test_cases():
        result = execute(port, **kwargs)
        checks = {
            "status": result["status"] == expected,
            "reason": result["reason"] == reason,
            "stage_calls": tuple(port.calls) == calls,
            "actual_work": result["backup_executed"] is executed,
            "new_success_flag": result["actual_backup_success"] is (expected == "NEW_BACKUP_VERIFIED"),
            "safe_output": "MOCK_PRIVATE_OUTPUT" not in json.dumps(result),
            "event_envelope": all(set(("run_id", "at_kst", "stage", "exit_code", "executed", "code"))
                                  <= set(event) for event in result["events"]),
            "receipt_identity": ((expected in ("NEW_BACKUP_VERIFIED", "CURRENT_BACKUP_ALREADY_VERIFIED"))
                                 == ("local_receipt_sha256" in result and "nas_cas_id" in result)),
        }
        legacy = overlap = None
        if number == "14":
            local, nas = port.known_local, port.known_nas
            # Model only the legacy exit/lineage predicate under otherwise favorable conditions.
            legacy = (port.local_result.exit_code == 0 and local.locked and local.sha_verified
                      and nas.completed and nas.snapshot_id == local.snapshot_id
                      and nas.local_receipt_sha256 == local.receipt_sha256
                      and nas.manifest_sha256 == local.inventory.manifest_sha256)
            checks["legacy_false_success_reproduced"] = legacy is True and not result["actual_backup_success"]
        if number == "15":
            overlap = port.overlap_result
            checks["overlap_stopped_before_child"] = (
                overlap["status"] == "SKIPPED_LOCK_HELD" and port.overlap.calls == [] and not port.lock.held)
        cases.append(dict(case=number, input=input_condition, expected=expected, actual=result["status"],
                          checks=checks, legacy_would_report_success=legacy, overlap=overlap,
                          verdict="PASS" if all(checks.values()) else "FAIL", result=result))
    passed = sum(case["verdict"] == "PASS" for case in cases)
    print(json.dumps(dict(dataset="SYNTHETIC_ONLY", passed=passed, total=len(cases), cases=cases), indent=2))
    return 0 if passed == len(cases) else 1

if __name__ == "__main__":
    raise SystemExit(run())
