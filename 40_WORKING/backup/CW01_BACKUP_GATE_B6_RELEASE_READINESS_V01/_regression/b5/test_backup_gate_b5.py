"""B5 regression and local OS probes. All created paths are inside this package."""
import copy
import fcntl
import hashlib
import json
import os
from pathlib import Path
import select
import signal
import tempfile
import time
from datetime import datetime, timedelta

from ROUTABL_BackupEvidenceNormalizer_v0_1 import KST, NAS_BASE, digest, normalize, receipt_selection

ROOT = Path(__file__).resolve().parent
M = "asset_manifest_v0.27.json"
OLD = "asset_manifest_v0.19.json"
SNAP = "ASSET_V21_20261107_043146_KST_123"
CAS_NAME = "CAS_" + SNAP + ".json"
NOW = datetime(2026,11,7,4,41,tzinfo=KST)
MANIFEST_BYTES = b'{"synthetic":true}'
H = digest(MANIFEST_BYTES)

def encode(obj):
    return json.dumps(obj, ensure_ascii=False, indent=2).encode()

def fixture():
    records = [{"relative_path":"projects/한글.txt","sha256":"a"*64,"size":27,"category":"project"},
               {"relative_path":"registered_assets/one","sha256":"b"*64,"size":5,"category":"registry"}]
    selection, count, size = receipt_selection({"records":records})
    fields = dict(manifest_name=M, manifest_sha256=H, selection_sha256=selection)
    earlier = (NOW - timedelta(minutes=7)).isoformat()
    local = dict(fields, status="SUCCESS", snapshot_name=SNAP, created_at_kst=earlier,
                 locked_after_backup=True, sha256_verified=True, file_count=count, source_bytes=size)
    receipt = dict(fields, type="ROUTABL_ASSET_V21_AES256_SELECTIVE_SNAPSHOT", snapshot_name=SNAP,
                   created_at_kst=(NOW-timedelta(minutes=8)).isoformat(), source_manifest=M,
                   source_manifest_sha256=H, file_count=count, all_snapshot_sha256_verified=True,
                   records=records, summary=dict(fields,total_files=count,total_source_bytes=size))
    local["receipt_sha256"] = digest(encode(receipt))
    anchor = str(NAS_BASE/"NAS_MANUAL_ASSET_V21_20261103_120000_KST_4")
    link = dict(local_receipt_sha256=local["receipt_sha256"], manifest_sha256=H, selection_sha256=selection)
    one = dict(link, status="SUCCESS_LOCAL_TO_NAS_ENCRYPTED_CAS", verified_at_kst=NOW.isoformat(),
               aes_image_detached=True, local_snapshot=SNAP, manifest_name=M, local_file_count=count,
               nas_cas_manifest=CAS_NAME, cas_components=2)
    cas = dict(link, type="ROUTABL_CIPHERTEXT_CAS_V01", local_snapshot_name=SNAP,
               created_kst=(NOW-timedelta(minutes=5)).isoformat(), anchor_snapshot=anchor,
               completed=True, components=2, total_ciphertext_bytes=33,
               files=[dict(relative_path="bands/1", sha256="c"*64,size=30,reference={"type":"blob"}),
                      dict(relative_path="token",sha256="d"*64,size=3,
                           reference=dict(type="anchor",snapshot=anchor,relative_path="token"))])
    return local, one, cas, receipt

def lock_inode_probe(work):
    path, old = work/"lock", work/"original-lock"
    with path.open("xb") as first:
        fcntl.flock(first, fcntl.LOCK_EX | fcntl.LOCK_NB)
        path.rename(old)
        with path.open("xb") as second:
            fcntl.flock(second, fcntl.LOCK_EX | fcntl.LOCK_NB)
            original = os.fstat(first.fileno())
            replacement = os.fstat(second.fileno())
            mismatch = (original.st_dev, original.st_ino) != (replacement.st_dev, replacement.st_ino)
    return mismatch, {"separate_inodes_both_locked":mismatch,"lstat_vs_original_fd_detected":mismatch}

def pin_probe(work):
    path = work/"candidate.bin"
    approved = b"first-approved-payload"
    changed = b"replacement-payload"
    path.write_bytes(approved)
    fd = os.open(path, os.O_RDONLY|os.O_NOFOLLOW)
    try:
        before = os.read(fd, 4096)
        new = work/"replacement.bin"
        new.write_bytes(changed)
        new.replace(path)
        os.lseek(fd,0,os.SEEK_SET)
        held = os.read(fd,4096)
        fresh = path.read_bytes()
        detected = digest(before) != digest(fresh)
        return detected and held == before == approved, {"fresh_open_detected_change":detected,
                                                        "held_descriptor_same_bytes":held == approved}
    finally:
        os.close(fd)

def escaped_group_probe():
    control_r, control_w = os.pipe()
    proof_r, proof_w = os.pipe()
    worker = os.fork()
    if worker == 0:
        os.close(control_w)
        os.close(proof_r)
        os.setsid()
        if os.fork() == 0:
            os.setsid()
            os.write(proof_w,b"R")
            if os.read(control_r,1) == b"P":
                os.write(proof_w,b"S")
            os.close(proof_w)
            os._exit(0)
        os.close(control_r)
        os.close(proof_w)
        signal.pause()
        os._exit(1)
    os.close(control_r)
    os.close(proof_w)
    reaped = False
    def receive():
        ready, _, _ = select.select([proof_r], [], [], 3)
        return os.read(proof_r,1) if ready else None
    try:
        assert receive() == b"R", "child did not detach"
        os.killpg(worker, signal.SIGTERM)
        _, result = os.waitpid(worker, 0)
        reaped = True
        os.write(control_w,b"P")
        survived = receive() == b"S"
        closed = receive() == b""
        return (survived and closed and os.WIFSIGNALED(result)), {
            "original_group_leader_terminated":os.WIFSIGNALED(result),
            "escaped_descendant_answered_after_signal":survived,
            "escaped_descendant_closed_probe_channel_on_exit":closed,
        }
    finally:
        os.close(control_w)
        os.close(proof_r)
        if not reaped:
            try:
                os.kill(worker,signal.SIGKILL)
            except ProcessLookupError:
                pass
            os.waitpid(worker,0)

def run():
    rows = []
    def record(name, expected, actual, details=None):
        rows.append(dict(case=name, expected=expected, actual=actual,
                         verdict="PASS" if actual == expected else "FAIL", details=details))
    def eval_fixture(name, expected, tweak=None, receipt=False, now=NOW, manifest=M,
                     selected=None, manifest_bytes=MANIFEST_BYTES, cas_name=CAS_NAME):
        l, o, c, r = fixture()
        if tweak:
            tweak(l,o,c,r)
        raw = encode(r) if receipt else None
        value = normalize(encode(l),encode(o),encode(c),manifest,manifest_bytes,cas_name,now,
                          receipt_raw=raw,selected_now=selected)
        if expected == "PARTIAL":
            actual = value.get("status") if value.get("actual_backup_verified") is False else "UNSAFE_SUCCESS"
        else:
            actual = value.get("reason")
        record(name,expected,actual,value)
        return value

    good = eval_fixture("raw_receipt_and_selection_recompute", "PARTIAL", receipt=True)
    record("raw_hash_and_selection_are_distinct_from_media_verification",True,
           good.get("local_receipt_bytes_verified") and good.get("selection_recomputed_from_receipt")
           and good.get("current_cas_component_sha256")=="NOT_PERFORMED")
    missing = eval_fixture("offline_local_receipt", "PARTIAL")
    record("missing_receipt_fail_closed",False,missing.get("local_receipt_bytes_verified"))
    stale = eval_fixture("newer_registry_and_yesterday", "PARTIAL", now=NOW+timedelta(days=1),
                         manifest="asset_manifest_v0.28.json", manifest_bytes=b"newest")
    record("stale_flags",[False,False],[stale.get("same_day_kst"),stale.get("current_registry_match")])
    current = eval_fixture("different_current_selection", "PARTIAL", selected=("f"*64,2,32))
    record("current_selection_mismatch",False,current.get("current_selection_match"))
    eval_fixture("local_sha_mismatch","LOCAL_RECEIPT_HASH_MISMATCH",
                 lambda l,o,c,r:r.update(extra=True),receipt=True)
    def rewrite_bad_selection(l,o,c,r):
        r["records"][0]["size"] += 1
        value = digest(encode(r))
        l["receipt_sha256"] = o["local_receipt_sha256"] = c["local_receipt_sha256"] = value
    eval_fixture("tampered_rows_with_fresh_receipt_hash","LOCAL_SELECTION_RECOMPUTE_MISMATCH",
                 rewrite_bad_selection,receipt=True)
    eval_fixture("cas_wrong_lineage","CAS_LINEAGE_MISMATCH",lambda l,o,c,r:c.update(local_receipt_sha256="0"*64))
    eval_fixture("cas_incomplete","CAS_NOT_COMPLETE",lambda l,o,c,r:c.update(completed=1))
    eval_fixture("cas_wrong_totals","CAS_TOTALS_MISMATCH",lambda l,o,c,r:c.update(total_ciphertext_bytes=99))
    eval_fixture("cas_duplicate_path","ROW_INTEGRITY",lambda l,o,c,r:c["files"][1].update(relative_path="bands/1"))
    eval_fixture("cas_traversal","UNSAFE_RELATIVE_PATH",lambda l,o,c,r:c["files"][0].update(relative_path="bands/../one"))
    eval_fixture("cas_anchor_outside_root","CAS_ANCHOR_NAME",lambda l,o,c,r:c["files"][1]["reference"].update(snapshot="/tmp/anchor"))
    eval_fixture("lock_status_false","LOCAL_STATUS_INCOMPLETE",lambda l,o,c,r:l.update(locked_after_backup=False))
    eval_fixture("bad_cas_manifest_name","ONESHOT_LINK_MISMATCH",cas_name="unrelated.json")
    eval_fixture("future_cas","INVALID_CHRONOLOGY",lambda l,o,c,r:c.update(created_kst=(NOW+timedelta(minutes=1)).isoformat()))
    l,o,c,_ = fixture()
    duplicate = encode(l).replace(b'{',b'{"status":"SUCCESS",',1)
    value = normalize(duplicate,encode(o),encode(c),M,MANIFEST_BYTES,CAS_NAME,NOW)
    record("duplicate_json_key","DUPLICATE_JSON_KEY",value.get("reason"))
    with tempfile.TemporaryDirectory(prefix="b5-fixture-",dir=ROOT) as tmp:
        work = Path(tmp)
        for name, test in (("lock_inode_replacement",lambda:lock_inode_probe(work)),
                           ("approval_pin_replacement",lambda:pin_probe(work)),
                           ("detached_process_group_escape",escaped_group_probe)):
            try:
                actual, details = test()
            except (OSError, AssertionError) as error:
                actual,details = False, {"failure":type(error).__name__}
            record(name,True,actual,details)
    passed = sum(row["verdict"]=="PASS" for row in rows)
    print(json.dumps({"scope":"ISOLATED_FIXTURES","passed":passed,"total":len(rows),"cases":rows},indent=2))
    return 0 if passed==len(rows) else 1

if __name__ == "__main__":
    raise SystemExit(run())
