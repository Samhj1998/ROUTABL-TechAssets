#!/usr/bin/env python3
"""ROUTABL headless backup v0.3 gate (new isolated version; not installed).

Same-day idempotence requires matching current manifest AND current selected-source
fingerprint. NAS idempotence requires the current local snapshot/receipt chain.
No Terminal, network, password, or launchd side effect. Explicit 'run' required.
"""
import argparse
import datetime
import fcntl
import hashlib
import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path
from zoneinfo import ZoneInfo

HOME=Path("/Users/yongho")
ROOT=HOME/"ROUTABL-TechAssets/00_GUIDE"
STATE=HOME/"Library/Logs/ROUTABL-AssetBackup"
LOCAL_SCRIPT=ROOT/"ROUTABL_SelectiveSecureBackup_v2_1.py"
NAS_SCRIPT=ROOT/"ROUTABL_SelectiveNasCopy_v2_1.py"
LOCAL_STATUS=STATE/"last_selective_v21_result.json"
NAS_STATUS=STATE/"last_selective_nas_v21_result.json"
MOUNT=Path("/Volumes/ROUTABL-Secure")

def today():
    return datetime.datetime.now(ZoneInfo("Asia/Seoul")).date().isoformat()

def receipt(path):
    if path.is_symlink() or not path.is_file():
        return {}
    try:
        d=json.loads(path.read_text(encoding="utf-8"))
        return d if isinstance(d,dict) else {}
    except (OSError,ValueError,UnicodeError):
        return {}

def local_date(record):
    try:
        return datetime.datetime.fromisoformat(record["created_at_kst"]).astimezone(
            ZoneInfo("Asia/Seoul")).date().isoformat()
    except (ValueError,KeyError,TypeError):
        return ""

def selector():
    spec=importlib.util.spec_from_file_location("routabl_v21_backup",str(LOCAL_SCRIPT))
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def current_fingerprint():
    scanner=selector()
    entries,rejected,total=scanner.inventory()
    return {
        "manifest_name":scanner.REGISTRY.name,
        "manifest_sha256":scanner.digest(scanner.REGISTRY),
        "selection_sha256":scanner.selection_digest(entries),
        "selection_file_count":len(entries),
        "total_source_bytes":total,
        "approved_registered_assets":sum(item[4]=="registry" for item in entries),
    }

def valid_local(r, current):
    return (r.get("status")=="SUCCESS" and r.get("locked_after_backup") is True
        and r.get("sha256_verified") is True
        and r.get("snapshot_name","").startswith("ASSET_V21_")
        and local_date(r)==today()
        and all(r.get(k)==current.get(k) for k in
            ("manifest_name","manifest_sha256","selection_sha256"))
        and r.get("file_count")==current["selection_file_count"]
        and r.get("source_bytes")==current["total_source_bytes"]
        and bool(r.get("receipt_sha256")))

def valid_nas(nas,local,current):
    return (nas.get("status")=="SUCCESS"
        and nas.get("nas_sha256_verified") is True
        and nas.get("day_kst")==today()
        and nas.get("local_snapshot_name")==local.get("snapshot_name")
        and nas.get("local_receipt_sha256")==local.get("receipt_sha256")
        and all(nas.get(k)==current.get(k) for k in
            ("manifest_sha256","selection_sha256"))
        and bool(nas.get("receipt_sha256")))

def decision(job,current):
    if os.geteuid()==0:
        return "BLOCKED_ROOT"
    if MOUNT.exists():
        return "BLOCKED_ENCRYPTED_IMAGE_ALREADY_MOUNTED"
    local=receipt(LOCAL_STATUS)
    if job=="local":
        return "SKIPPED_CURRENT_SNAPSHOT_VERIFIED" if valid_local(local,current) else "READY_FOR_LOCAL_ONCE"
    if job=="nas":
        if not valid_local(local,current):
            return "BLOCKED_CURRENT_LOCAL_SNAPSHOT_NOT_VERIFIED"
        nas=receipt(NAS_STATUS)
        return ("SKIPPED_NAS_LINKED_TO_CURRENT_LOCAL" if valid_nas(nas,local,current)
                else "READY_FOR_NAS_ONCE")
    raise ValueError("bad job")

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("mode",choices=("check","run"))
    ap.add_argument("job",choices=("local","nas"))
    args=ap.parse_args()
    if not STATE.is_dir() or STATE.is_symlink() or os.geteuid()==0:
        raise RuntimeError("UNSAFE_STATE_OR_USER")
    lockfile=STATE/("selective_v21_gate_"+args.job+".lock")
    fd=os.open(lockfile,os.O_RDWR|os.O_CREAT,0o600)
    try:
        try:fcntl.flock(fd,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError:
            print(json.dumps({"job":args.job,"state":"ALREADY_RUNNING","executed":False}))
            return 0
        current=current_fingerprint()
        state=decision(args.job,current)
        print(json.dumps({"job":args.job,"mode":args.mode,"gate":state,
                          "manifest":current["manifest_name"],
                          "files":current["selection_file_count"],
                          "manifest_sha256":current["manifest_sha256"],
                          "selection_sha256":current["selection_sha256"],
                          "no_work_executed":args.mode=="check" or not state.startswith("READY_")}),flush=True)
        if args.mode=="check" or not state.startswith("READY_"):
            return 0 if state.startswith(("SKIPPED_","READY_")) else 2
        job=LOCAL_SCRIPT if args.job=="local" else NAS_SCRIPT
        argv=["/usr/bin/python3",str(job)]
        if args.job=="local":argv.append("backup")
        # No GUI command, no password prompts or scheduling side effects.
        run=subprocess.run(argv,capture_output=True,text=True,
                           stdin=subprocess.DEVNULL,timeout=900)
        if run.returncode!=0:
            print(json.dumps({"job":args.job,"result":"FAILED_SAFE",
                              "child_returncode":run.returncode}),file=sys.stderr)
            return 3
        after=current_fingerprint()
        if after!=current:
            print(json.dumps({"job":args.job,"result":"CHANGED_DURING_BACKUP"}),file=sys.stderr)
            return 4
        state_after=decision(args.job,current)
        expected=("SKIPPED_CURRENT_SNAPSHOT_VERIFIED" if args.job=="local"
                  else "SKIPPED_NAS_LINKED_TO_CURRENT_LOCAL")
        if state_after!=expected:
            print(json.dumps({"job":args.job,"result":"RECEIPT_CHAIN_NOT_VERIFIED",
                              "observed_gate":state_after}),file=sys.stderr)
            return 5
        print(json.dumps({"job":args.job,"result":"SUCCESS",
                          "receipt_chain_verified":True,
                          "manifest_sha256":current["manifest_sha256"],
                          "selection_sha256":current["selection_sha256"]}),flush=True)
        return 0
    finally:
        os.close(fd)

if __name__=="__main__":
    try:sys.exit(main())
    except Exception as ex:
        print(json.dumps({"result":"FAILED_SAFE","failure_type":type(ex).__name__}),file=sys.stderr)
        sys.exit(9)
