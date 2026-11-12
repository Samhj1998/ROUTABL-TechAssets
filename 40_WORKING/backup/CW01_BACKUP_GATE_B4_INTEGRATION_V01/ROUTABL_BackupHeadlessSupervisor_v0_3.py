"""B4 isolated entry for scheduled/manual fixture runs. Owns shared flock."""
import argparse
from contextlib import contextmanager
import fcntl
import json
import os
import stat
from uuid import uuid4

from backup_runner_candidate import Inventory, Local, Nas, Stop, SHA, matches
import ROUTABL_BackupEvidenceAdapter_v0_1 as evidence
from fixture_boundary import install
from ROUTABL_MacToNasOneShot_v0_2 import Port

LABEL = "com.routabl.assetbackup.native.v043"
LOCK = evidence.ROOT / "shared-fixture.lock"
FILES = ("ROUTABL_BackupHeadlessSupervisor_v0_3.py", "ROUTABL_MacToNasOneShot_v0_2.py",
         "ROUTABL_BackupEvidenceAdapter_v0_1.py", "backup_runner_candidate.py", "fixture_worker.py", "fixture_boundary.py")

def identity(info):
    return info.st_dev, info.st_ino

@contextmanager
def execution_lock():
    fd = os.open(evidence.safe(LOCK), os.O_NOFOLLOW | os.O_CREAT | os.O_RDWR, 0o600)
    try:
        info = os.fstat(fd)
        if (not stat.S_ISREG(info.st_mode) or info.st_nlink != 1 or info.st_uid != os.geteuid()
                or info.st_mode & 0o077 or identity(info) != identity(LOCK.lstat())):
            raise Stop("FAILED_SAFE", "INVALID_LOCK")
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise Stop("SKIPPED_LOCK_HELD", "SHARED_LOCK_HELD")
        yield identity(info)
        if identity(info) != identity(LOCK.lstat()):
            raise Stop("FAILED_SAFE", "LOCK_REPLACED")
    finally:
        os.close(fd)

def pins():
    return {name: evidence.digest(evidence.ROOT / name) for name in FILES}

def approved(before, path):
    data = evidence.decode(evidence.read(path))
    expected = data["pinned_programs"]
    return (data["schema_version"] == "0.1" and data["scope"] == "ISOLATED_FIXTURE_ONLY"
            and data["allowed_label"] == LABEL and isinstance(expected, dict)
            and all(matches(SHA, digest) for digest in expected.values()) and expected == before)

def run(case, entry, active, bad_pin=False):
    run_id, events, port = uuid4().hex, [], None
    status, reason = "FAILED_SAFE", "UNCLASSIFIED"
    local = nas = None
    def record(stage, code, exit_code=None, executed=None, evidence=None):
        row = dict(stage=stage, code=code, exit_code=exit_code, executed=executed,
                   at_kst=port.now().isoformat(), run_id=run_id)
        inv = evidence.inventory if isinstance(evidence, Local) else evidence
        if isinstance(inv, Inventory):
            row.update(inv.__dict__)
        if isinstance(evidence, Local):
            row.update(snapshot_id=evidence.snapshot_id, local_receipt_sha256=evidence.receipt_sha256)
        if isinstance(evidence, Nas):
            row.update(cas_id=evidence.cas_id, local_receipt_sha256=evidence.local_receipt_sha256,
                       manifest_sha256=evidence.manifest_sha256, selection_sha256=evidence.selection_sha256)
        events.append(row)
    try:
        if active != [LABEL] or entry not in ("scheduled", "manual"):
            raise Stop("FAILED_SAFE", "SCHEDULE_NOT_SINGLE_AUTHORIZED_ENTRY")
        port = Port(evidence.fixture(case))
        with execution_lock():
            record("lock", "ACQUIRED", executed=False)
            before = pins()
            approval = evidence.ROOT / ("fixture_approval_bad.json" if bad_pin else "fixture_approval.json")
            approval_hash = evidence.digest(approval)
            if not approved(before, approval):
                raise Stop("FAILED_SAFE", "PROGRAM_PIN_MISMATCH")
            record("preflight", "PINS_VERIFIED", executed=False)
            try:
                status, local, nas = port.run(port.now(), record)
                reason = "VERIFIED"
            finally:
                if before != pins() or approval_hash != evidence.digest(approval):
                    raise Stop("FAILED_SAFE", "PIN_CHANGED_DURING_RUN")
                record("postflight", "PINS_UNCHANGED", executed=False)
    except Stop as error:
        status, reason = error.status, error.reason
    except Exception:
        status, reason = "FAILED_SAFE", "MISSING_OR_INVALID_FIXTURE_EVIDENCE"
    success = status == "NEW_BACKUP_VERIFIED"
    reused = status == "CURRENT_BACKUP_ALREADY_VERIFIED"
    work = [event["executed"] for event in events if event["stage"] in ("local", "nas")]
    did_work = True if True in work else (False if not work or all(value is False for value in work) else None)
    if status in ("SKIPPED_LOCK_HELD", "NO_NEW_BACKUP_EVIDENCE") and True not in work:
        did_work = False
    return dict(schema_version="0.1", scope="ISOLATED_FIXTURE_ONLY", run_id=run_id,
                status=status, reason=reason, entry=entry, actual_backup_success=success,
                backup_executed=did_work, events=events, processes=port.processes if port else [],
                verified_chain=dict(local=local.__dict__, nas=nas.__dict__) if success or reused else None)

def main():
    install()
    parser = argparse.ArgumentParser()
    parser.add_argument("case")
    parser.add_argument("entry", choices=("manual", "scheduled"))
    parser.add_argument("--label", action="append", required=True)
    parser.add_argument("--bad-pin", action="store_true")
    args = parser.parse_args()
    result = run(args.case, args.entry, args.label, args.bad_pin)
    print(json.dumps(result, default=lambda value: value.isoformat() if hasattr(value, "isoformat")
                     else value.__dict__, ensure_ascii=False))
    return {"NEW_BACKUP_VERIFIED": 0, "CURRENT_BACKUP_ALREADY_VERIFIED": 10,
            "SKIPPED_LOCK_HELD": 20}.get(result["status"], 30)

if __name__ == "__main__":
    raise SystemExit(main())
