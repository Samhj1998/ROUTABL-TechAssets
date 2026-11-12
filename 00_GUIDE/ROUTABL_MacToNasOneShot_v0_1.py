#!/usr/bin/env python3
"""ROUTABL Mac Studio -> encrypted SSD -> NAS content-addressed snapshot.

Manual, single-invocation orchestrator. Never schedules itself, never opens Terminal
or Google Drive, never changes system privacy settings, and never deletes snapshots.
"""
from __future__ import annotations
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
ROOT=HOME/"ROUTABL-TechAssets"
GUIDE=ROOT/"00_GUIDE"
LOG=HOME/"Library/Logs/ROUTABL-AssetBackup"
GATE=GUIDE/"ROUTABL_HeadlessDailyGate_v0_3.py"
CAS=GUIDE/"ROUTABL_NAS_ContentAwareBackup_v0_2.py"
LOCK=LOG/"manual_mac_to_nas_cas_v01.lock"
STATUS=LOG/"last_manual_mac_nas_cas_v01.json"
LOCAL=LOG/"last_selective_v21_result.json"
MOUNT=Path("/Volumes/ROUTABL-Secure")
SSD=Path("/Volumes/SSD2TB")
NAS=Path("/Volumes/Dev_Assets")
CAS_MANIFESTS=NAS/"ROUTABL-TechAssets-Backup/snapshots/ROUTABL-Ciphertext-CAS-v0_1/manifests"

def sha(path):
    h=hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda:stream.read(1048576),b""):
            h.update(chunk)
    return h.hexdigest()

def read_json(p):
    if p.is_symlink() or not p.is_file():raise RuntimeError("RECEIPT_MISSING")
    d=json.loads(p.read_text("utf8"))
    if not isinstance(d,dict):raise RuntimeError("RECEIPT_INVALID")
    return d

def preflight():
    if os.geteuid()!=501 or not LOG.is_dir() or LOG.is_symlink():
        raise RuntimeError("UNSAFE_EXECUTION_CONTEXT")
    if not os.path.ismount(SSD) or not os.path.ismount(NAS) or MOUNT.exists():
        raise RuntimeError("STORAGE_OFFLINE_OR_IMAGE_UNLOCKED")
    if any(not x.is_file() or x.is_symlink() for x in (GATE,CAS)):
        raise RuntimeError("BACKUP_PROGRAM_NOT_TRUSTED")
    if not CAS_MANIFESTS.is_dir() or CAS_MANIFESTS.is_symlink():
        raise RuntimeError("CAS_NOT_SEEDED")
    if not list(CAS_MANIFESTS.glob("CAS_ASSET_V21_*.json")):
        raise RuntimeError("NAS_CAS_ANCHOR_MISSING")

def run_child(args,phase):
    try:
        job=subprocess.run(["/usr/bin/python3",*args],capture_output=True,text=True,
                           stdin=subprocess.DEVNULL,timeout=1000)
    except subprocess.TimeoutExpired:
        raise RuntimeError("PHASE_TIMEOUT_"+phase)
    if job.returncode!=0:
        # Child stdout/stderr may contain sensitive system messages. Never echo.
        raise RuntimeError("PHASE_NONZERO_"+phase)
    return job.stdout

def verify_current_nas():
    local=read_json(LOCAL)
    if local.get("status")!="SUCCESS" or not local.get("locked_after_backup") or not local.get("sha256_verified"):
        raise RuntimeError("CURRENT_LOCAL_RECEIPT_NOT_SUCCESS")
    p=CAS_MANIFESTS/("CAS_"+str(local.get("snapshot_name",""))+".json")
    j=read_json(p)
    if (j.get("local_snapshot_name")!=local["snapshot_name"]
        or j.get("local_receipt_sha256")!=local["receipt_sha256"]
        or j.get("manifest_sha256")!=local.get("manifest_sha256")
        or j.get("selection_sha256")!=local.get("selection_sha256")):
        raise RuntimeError("NAS_CAS_LINEAGE_MISMATCH")
    spec=importlib.util.spec_from_file_location("cas_verify",str(CAS))
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    result=module.verify_manifest(j,full=True)
    if not result["all_bands_sha256_verified"]:
        raise RuntimeError("NAS_CAS_HASHES_NOT_VERIFIED")
    if MOUNT.exists():
        raise RuntimeError("IMAGE_NOT_LOCKED_AFTER_BACKUP")
    return local,j,p

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("action",choices=("check","run"))
    mode=parser.parse_args().action
    preflight()
    fd=os.open(LOCK,os.O_RDWR|os.O_CREAT,0o600)
    try:
        try:fcntl.flock(fd,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError:
            print(json.dumps({"status":"ALREADY_RUNNING_SAFELY_SKIPPED",
                              "backup_executed":False}))
            return 0
        if mode=="check":
            print(json.dumps({"status":"READY_FOR_MANUAL_ONE_SHOT",
                              "target":"ENCRYPTED_LOCAL_AND_NAS_CAS",
                              "google_drive_enabled":False,
                              "schedule_installed":False,
                              "originals_to_be_deleted":0}))
            return 0
        run_child([str(GATE),"run","local"],"LOCAL")
        local=read_json(LOCAL)
        if local.get("status")!="SUCCESS":
            raise RuntimeError("LOCAL_BACKUP_RECEIPT_NOT_SUCCESS")
        run_child([str(CAS),"capture"],"NAS_CAS")
        local,cas,path=verify_current_nas()
        output={
            "status":"SUCCESS_LOCAL_TO_NAS_ENCRYPTED_CAS",
            "verified_at_kst":datetime.datetime.now(ZoneInfo("Asia/Seoul")).isoformat(timespec="seconds"),
            "local_snapshot":local["snapshot_name"],
            "local_file_count":local["file_count"],
            "manifest_name":local["manifest_name"],
            "manifest_sha256":local["manifest_sha256"],
            "selection_sha256":local["selection_sha256"],
            "local_receipt_sha256":local["receipt_sha256"],
            "nas_cas_manifest":path.name,
            "cas_components":cas["components"],
            "cas_new_ciphertext_bytes":cas["new_ciphertext_bytes_copied"],
            "cas_reused_components":cas["reused_ciphertext_components"],
            "google_drive_upload":False,
            "automatic_scheduling":False,
            "existing_snapshots_pruned":False,
            "aes_image_detached":True,
        }
        tmp=STATUS.with_suffix(".json.partial")
        if tmp.exists():raise RuntimeError("STATUS_TEMP_EXISTS")
        with tmp.open("x",encoding="utf8") as f:
            json.dump(output,f,ensure_ascii=False,indent=2)
            f.write("\n")
        os.chmod(tmp,0o600)
        os.replace(tmp,STATUS)
        print(json.dumps(output,ensure_ascii=False),flush=True)
        return 0
    finally:
        os.close(fd)

if __name__=="__main__":
    try:sys.exit(main())
    except Exception as e:
        print(json.dumps({"status":"FAILED_SAFE","failure_type":type(e).__name__,
                          "backups_not_claimed_complete":True}),file=sys.stderr,flush=True)
        sys.exit(2)
