"""Run isolated B4 acceptance tests using macOS subprocesses and flock."""
from datetime import datetime, timedelta
import json
from pathlib import Path
import subprocess
import sys
import time

from backup_runner_candidate import KST
from ROUTABL_BackupEvidenceAdapter_v0_1 import inventory, digest, ROOT
from ROUTABL_BackupHeadlessSupervisor_v0_3 import LABEL, pins
from fixture_worker import local_receipt, cas_receipt

ENTRY = str(ROOT / "ROUTABL_BackupHeadlessSupervisor_v0_3.py")
OLD = "com.routabl.assetbackup.native.v042"

def write(path, data):
    path.write_text(json.dumps(data) + "\n", encoding="utf-8")

def seed(name, gate="new", nas="new", old=False, stale=False):
    base = ROOT / "cases" / name
    (base / "registry").mkdir(parents=True)
    (base / "assets").mkdir()
    write(base / "registry/asset_manifest_v0.9.json", {"fixture":9})
    write(base / "registry/asset_manifest_v0.27.json", {"fixture":27})
    (base / "assets/asset").write_bytes(b"synthetic backup asset")
    (base / "cas_blob.bin").write_bytes(b"synthetic ciphertext component")
    write(base / "selection.json", {"files":[dict(name="asset", target="relative", category="fixture")]})
    inv = inventory(base)
    fields = dict(manifest_name=inv.manifest_name, manifest_sha256=inv.manifest_sha256,
                  selection_sha256=inv.selection_sha256, file_count=inv.file_count, source_bytes=inv.total_bytes)
    assert inv.manifest_name == "asset_manifest_v0.27.json"
    write(base / "config.json", dict(gate=gate, nas=nas, fingerprint=fields))
    if gate == "reuse":
        if stale:
            fields = dict(fields, manifest_name="asset_manifest_v0.19.json", manifest_sha256="a"*64)
        local_receipt(base, {"fingerprint":fields}, datetime.now(KST) - timedelta(days=int(old), seconds=1))
        cas_receipt(base, "new")
    return base

def spawn(name, entry="manual", duplicate=False, bad_pin=False):
    args = [sys.executable, "-B", ENTRY, name, entry, "--label", LABEL]
    if duplicate:
        args += ["--label", OLD]
    if bad_pin:
        args += ["--bad-pin"]
    return subprocess.Popen(args, cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

def collect(process):
    out, err = process.communicate(timeout=8)
    if not out:
        raise RuntimeError("Test entry produced no JSON: " + err.decode(errors="replace"))
    return json.loads(out), process.returncode

def process_active(pid):
    result = subprocess.run(["/bin/ps", "-o", "stat=", "-p", str(pid)], capture_output=True, text=True)
    state = result.stdout.strip()
    return bool(state and not state.startswith("Z"))

def main():
    records = []
    approval = dict(schema_version="0.1", scope="ISOLATED_FIXTURE_ONLY",
                    allowed_label=LABEL, pinned_programs=pins())
    write(ROOT/"fixture_approval.json", approval)
    write(ROOT/"fixture_approval_bad.json", dict(approval, pinned_programs={
        **approval["pinned_programs"], "fixture_worker.py":"0"*64}))

    def add(case, expected, result, code, extra=True, **details):
        expected_exit = {"NEW_BACKUP_VERIFIED":0, "CURRENT_BACKUP_ALREADY_VERIFIED":10,
                         "SKIPPED_LOCK_HELD":20}.get(expected, 30)
        passed = (result["status"] == expected and code == expected_exit and extra
                  and result["actual_backup_success"] is (expected == "NEW_BACKUP_VERIFIED"))
        records.append(dict(case=case, expected=expected, verdict="PASS" if passed else "FAIL",
                            result=result, entry_exit=code, details=details))

    seed("normal")
    result, code = collect(spawn("normal"))
    add("normal_new", "NEW_BACKUP_VERIFIED", result, code,
        extra=len(result["processes"]) == 2 and result["backup_executed"] is True
        and any(event["code"] == "PINS_UNCHANGED" for event in result["events"]))

    base = seed("first", gate="hold")
    seed("second")
    first = spawn("first", "scheduled")
    try:
        until = time.monotonic() + 3
        while not (base/"ready.json").exists() and first.poll() is None and time.monotonic() < until:
            time.sleep(0.02)
        ready = (base/"ready.json").exists() and first.poll() is None
        overlap, overlap_exit = collect(spawn("second", "manual"))
        add("os_lock_contention_manual_vs_scheduled", "SKIPPED_LOCK_HELD", overlap, overlap_exit,
            extra=ready and not overlap["processes"],
            lock_holder_pid=first.pid, contender_children=len(overlap["processes"]))
    finally:
        holder, holder_exit = collect(first)
    add("lock_owner_finishes", "NEW_BACKUP_VERIFIED", holder, holder_exit)

    matrix = [
        ("child_lock", "child_lock", "new", "SKIPPED_LOCK_HELD", "CHILD_LOCK_HELD"),
        ("exit_zero_no_work", "no_work", "new", "NO_NEW_BACKUP_EVIDENCE", "LOCAL_WORK_NOT_PROVEN"),
        ("child_exit7", "exit7", "new", "FAILED_SAFE", "CHILD_NONZERO"),
        ("child_timeout", "timeout", "new", "FAILED_SAFE", "TIMEOUT"),
        ("pin_mismatch", "new", "new", "FAILED_SAFE", "PROGRAM_PIN_MISMATCH"),
        ("today_reuse", "reuse", "reindex", "CURRENT_BACKUP_ALREADY_VERIFIED", "VERIFIED"),
        ("stale_manifest", "reuse", "reindex", "STALE_REGISTRY_BACKUP", "LOCAL_INVENTORY_MISMATCH"),
        ("old_snapshot", "reuse", "reindex", "STALE_REGISTRY_BACKUP", "LOCAL_NOT_SAME_KST_DAY"),
        ("selection_changed", "new", "change", "FAILED_SAFE", "INVENTORY_CHANGED"),
        ("nas_incomplete", "new", "incomplete", "NAS_CHAIN_NOT_VERIFIED", "NAS_EVIDENCE_MISSING_OR_MISMATCH"),
        ("nas_mismatch", "new", "mismatch", "NAS_CHAIN_NOT_VERIFIED", "NAS_EVIDENCE_MISSING_OR_MISMATCH"),
        ("nas_missing", "new", "missing", "NAS_CHAIN_NOT_VERIFIED", "NAS_EVIDENCE_MISSING_OR_MISMATCH"),
        ("nas_indexed_is_not_new", "new", "reindex", "NAS_CHAIN_NOT_VERIFIED", "NAS_WORK_STATE_MISMATCH"),
        ("duplicate_schedule", "new", "new", "FAILED_SAFE", "SCHEDULE_NOT_SINGLE_AUTHORIZED_ENTRY"),
        ("malformed_wire", "malformed", "new", "FAILED_SAFE", "LOCAL_RESULT_CONTRADICTORY_OR_FAILED"),
    ]
    for name, gate, nas, expected, reason in matrix:
        base = seed(name, gate, nas, old=name=="old_snapshot", stale=name=="stale_manifest")
        result, code = collect(spawn(name, duplicate=name=="duplicate_schedule", bad_pin=name=="pin_mismatch"))
        ok, details = result["reason"] == reason, {}
        if name == "child_timeout":
            marker = base/"grandchild.json"
            grandchild = json.loads(marker.read_text())["pid"] if marker.exists() else None
            row = result["processes"][0] if result["processes"] else {}
            ok = (ok and grandchild is not None and not process_active(grandchild)
                  and row.get("timed_out") is True and row.get("exit_code") == -9
                  and not row.get("live_descendants") and not process_active(row["pid"]))
            details = dict(grandchild_pid=grandchild, grandchild_live=process_active(grandchild)
                           if grandchild is not None else None, force_kill_signal=9)
        if name in ("pin_mismatch", "duplicate_schedule"):
            ok = ok and not result["processes"]
        if name == "child_exit7":
            ok = ok and result["processes"][0]["exit_code"] == 7
        if name == "today_reuse":
            ok = ok and result["backup_executed"] is False
        add(name, expected, result, code, extra=ok, **details)

    outside, code = collect(spawn("../CW01_BACKUP_GATE_B3_CANDIDATE_V01"))
    add("path_traversal_rejected", "FAILED_SAFE", outside, code,
        extra=outside["reason"] == "INVALID_CASE_NAME" and not outside["processes"])
    probe = """
from fixture_boundary import install
from pathlib import Path
import subprocess
install()
checks = [
    lambda: Path('/Users/yongho/ROUTABL-TechAssets/30_REGISTRY/asset_manifest_v0.27.json').read_bytes(),
    lambda: subprocess.run(['/bin/echo', 'unapproved executable']),
]
for check in checks:
    try:
        check()
    except PermissionError:
        continue
    raise SystemExit(1)
"""
    audit = subprocess.run([sys.executable, "-B", "-c", probe], cwd=ROOT, capture_output=True)
    records.append(dict(case="audit_denies_outside_read_and_unapproved_exec",
                        verdict="PASS" if audit.returncode == 0 else "FAIL", exit=audit.returncode))
    passed = sum(row["verdict"] == "PASS" for row in records)
    print(json.dumps(dict(passed=passed, total=len(records), cases=records), indent=2))
    return 0 if passed == len(records) else 1

if __name__ == "__main__":
    raise SystemExit(main())
