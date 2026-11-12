"""Synthetic Gate and CAS wire producer for actual subprocess tests."""
from datetime import datetime, timedelta, timezone
from hashlib import sha256
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from fixture_boundary import install
from ROUTABL_BackupEvidenceAdapter_v0_1 import fixture, read, safe, decode

def write(base, name, data):
    with safe(base / name).open("xb") as f:
        f.write(json.dumps(data, separators=(",", ":")).encode() + b"\n")

def emit(data):
    print(json.dumps(data), flush=True)

def local_receipt(base, data, now):
    stamp = now.isoformat()
    snap = now.strftime("ASSET_V21_%Y%m%d_%H%M%S_KST_") + str(os.getpid())
    fields = {**data["fingerprint"], "snapshot_name": snap, "created_at_kst": stamp}
    write(base, "local_receipt.json", dict(**fields, all_snapshot_sha256_verified=True))
    write(base, "local_status.json", dict(**fields, receipt_sha256=sha256(read(base/"local_receipt.json")).hexdigest(),
          status="SUCCESS", locked_after_backup=True, sha256_verified=True))

def cas_receipt(base, config):
    local = decode(read(base / "local_status.json"))
    blob = read(base / "cas_blob.bin")
    write(base, "nas_receipt.json", dict(
        cas_id="CAS-" + local["snapshot_name"], local_snapshot_name=local["snapshot_name"],
        local_receipt_sha256=("0"*64 if config == "mismatch" else local["receipt_sha256"]),
        manifest_sha256=local["manifest_sha256"], selection_sha256=local["selection_sha256"],
        completed=config != "incomplete", components=1, ciphertext_sha256=sha256(blob).hexdigest(),
        ciphertext_bytes=len(blob)))

def main():
    install()
    name, stage = sys.argv[1:]
    base = fixture(name)
    data = decode(read(base / "config.json"))
    if stage == "grandchild":
        signal.signal(signal.SIGTERM, signal.SIG_IGN)
        write(base, "grandchild.json", {"pid": os.getpid()})
        time.sleep(30)
        return 1
    if stage == "gate":
        case = data["gate"]
        if case == "timeout":
            signal.signal(signal.SIGTERM, signal.SIG_IGN)
            subprocess.Popen([sys.executable, "-I", "-B", str(ROOT/"fixture_worker.py"), name, "grandchild"],
                             cwd=ROOT, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            time.sleep(30)
            return 1
        if case == "hold":
            write(base, "ready.json", {"pid": os.getpid()})
            time.sleep(0.8)
        if case == "exit7":
            return 7
        if case == "malformed":
            print("non-json synthetic line", flush=True)
            return 0
        if case == "child_lock":
            emit(dict(job="local", state="ALREADY_RUNNING", executed=False))
            return 0
        reuse = case == "reuse"
        ready = dict(job="local", mode="check" if case == "no_work" else "run",
                     gate="SKIPPED_CURRENT_SNAPSHOT_VERIFIED" if reuse else "READY_FOR_LOCAL_ONCE",
                     manifest=data["fingerprint"]["manifest_name"],
                     files=data["fingerprint"]["file_count"], no_work_executed=reuse or case == "no_work")
        hashes = {k: data["fingerprint"][k] for k in ("manifest_sha256", "selection_sha256")}
        emit(dict(**ready, **hashes))
        if reuse or case == "no_work":
            return 0
        local_receipt(base, data, datetime.now(timezone(timedelta(hours=9))))
        emit(dict(job="local", result="SUCCESS", receipt_chain_verified=True, **hashes))
        return 0
    if stage != "nas":
        return 2
    case = data["nas"]
    if case == "reindex":
        emit(dict(result="SNAPSHOT_ALREADY_INDEXED", verification={"all_bands_sha256_verified":False}))
        return 0
    if case == "change":
        with safe(base/"assets"/"asset").open("ab") as f:
            f.write(b" changed after local")
    if case != "missing":
        cas_receipt(base, case)
    emit(dict(result="INCREMENTAL_SNAPSHOT_VERIFIED"))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
