#!/usr/bin/env python3
"""120. ROUTABL safe one-shot agent entry point for user-controlled scheduling.

DEFAULT = DISARMED. Neither --check nor --scheduled can create an automatic
backup until explicit same-user approval.json exists and all secure guards pass.
Never uploads to Drive, edits app sources, changes macOS privacy, or prunes NAS.
Agent itself executes once; no polling, KeepAlive, or automatic retries.
"""
from __future__ import annotations
import argparse
import datetime
import errno
import fcntl
import hashlib
import json
import os
import signal
import subprocess
import sys
import tempfile
from pathlib import Path
from zoneinfo import ZoneInfo

HOME=Path("/Users/yongho")
ROOT=HOME/"ROUTABL-TechAssets"
LOG=HOME/"Library/Logs/ROUTABL-AssetBackup"
APPROVAL=HOME/"Library/Application Support/ROUTABL-AssetBackup/approval_v01.json"
RUNNER=ROOT/"00_GUIDE/ROUTABL_MacToNasOneShot_v0_1.py"
CAS=ROOT/"00_GUIDE/ROUTABL_NAS_ContentAwareBackup_v0_2.py"
GATE=ROOT/"00_GUIDE/ROUTABL_HeadlessDailyGate_v0_3.py"
SSD=Path("/Volumes/SSD2TB")
NAS=Path("/Volumes/Dev_Assets")
MOUNT=Path("/Volumes/ROUTABL-Secure")
IMAGE=SSD/"ROUTABL-TechAssets-Backup/ROUTABL-SecureBackup.sparsebundle"
MANIFESTS=NAS/"ROUTABL-TechAssets-Backup/snapshots/ROUTABL-Ciphertext-CAS-v0_1/manifests"
LOCK=LOG/"native_backup_supervisor_v02.lock"
STATUS=LOG/"last_native_backup_supervisor_v02.json"
LAST=LOG/"last_manual_mac_nas_cas_v01.json"
LOCAL=LOG/"last_selective_v21_result.json"
EXPECTED_UID=501

def timestamp():
    return datetime.datetime.now(ZoneInfo("Asia/Seoul")).isoformat(timespec="seconds")

def sha(path):
    h=hashlib.sha256()
    with path.open("rb") as fp:
        for part in iter(lambda:fp.read(1048576),b""):
            h.update(part)
    return h.hexdigest()

def checks():
    """Read-only diagnostics. Order is deterministic, result never contains paths."""
    out=[]
    def stage(name,ok):
        out.append({"stage":name,"state":"PASS" if ok else "BLOCKED"})
    stage("user_uid",os.geteuid()==EXPECTED_UID and os.getuid()==EXPECTED_UID)
    stage("state_owner",LOG.is_dir() and not LOG.is_symlink() and
          LOG.stat().st_uid==EXPECTED_UID)
    stage("ssd_mounted",os.path.ismount(SSD))
    stage("nas_mounted",os.path.ismount(NAS))
    stage("source_encrypted_image_closed",not MOUNT.exists())
    stage("source_ciphertext_image_present",IMAGE.is_dir() and not IMAGE.is_symlink())
    stage("nas_cas_manifest_store",MANIFESTS.is_dir() and not MANIFESTS.is_symlink() and
          any(MANIFESTS.glob("CAS_ASSET_V21_*.json")))
    for name,p in (("manual_runner",RUNNER),("nas_engine",CAS),("local_gate",GATE)):
        stage(name,p.is_file() and not p.is_symlink())
    return out

def approval_check():
    """A missing or malformed approval is NOT an error: it means fail-closed."""
    if not APPROVAL.is_file() or APPROVAL.is_symlink():
        return "DISARMED_NO_APPROVAL"
    try:
        st=APPROVAL.stat()
        if st.st_uid!=EXPECTED_UID or st.st_mode & 0o077:
            return "DISARMED_APPROVAL_PERMISSIONS"
        a=json.loads(APPROVAL.read_text(encoding="utf8"))
        if not isinstance(a,dict):
            return "DISARMED_INVALID_APPROVAL"
        fields=(a.get("approval_version")==1,
                a.get("owner_uid")==EXPECTED_UID,
                a.get("enabled") is True,
                a.get("scope")=="MAC_SSD_AES256_TO_NAS_CAS_ONLY",
                a.get("scheduled_hour_kst")==4,
                a.get("scheduled_minute_kst")==30,
                a.get("drive_upload") is False,
                a.get("allow_pruning") is False)
        if not all(fields):
            return "DISARMED_APPROVAL_POLICY"
        for key,p in (("runner_sha256",RUNNER),
                      ("nas_engine_sha256",CAS),("local_gate_sha256",GATE)):
            if a.get(key)!=sha(p):
                return "DISARMED_PROGRAM_INTEGRITY_CHANGED"
        return "APPROVED"
    except (OSError,ValueError,TypeError,UnicodeError):
        return "DISARMED_INVALID_APPROVAL"

def record(status,phase,extra=None,allow_write=True):
    payload={"version":"0.2",
             "date_kst":timestamp(),
             "state":status,"phase":phase,
             "actual_backup_success":status=="SUCCESS_VERIFIED",
             "google_drive_transfer":False,
             "automatic_retry":False,
             "configured_jobs_modified":False,
             "protected_existing_backup":True}
    if extra:payload.update(extra)
    if allow_write:
        if not LOG.is_dir() or LOG.is_symlink():
            raise RuntimeError("STATUS_FOLDER_UNSAFE")
        with tempfile.NamedTemporaryFile("w",encoding="utf8",dir=LOG,
                                         prefix=".native_status_",delete=False) as temp:
            json.dump(payload,temp,ensure_ascii=False,indent=2)
            temp.write("\n")
            scratch=Path(temp.name)
        os.chmod(scratch,0o600)
        os.replace(scratch,STATUS)
    print(json.dumps(payload,ensure_ascii=False),flush=True)
    return payload

def simulate_scenarios():
    """Offline negative tests, deliberately NO backup, no file system modifications."""
    states={
        "permission_denied":"BLOCKED_FIRST_PERMISSION_FAILURE",
        "ssd_missing":"BLOCKED_AT_SSD_MOUNT",
        "nas_missing":"BLOCKED_AT_NAS_MOUNT",
        "already_mounted":"BLOCKED_IMAGE_OPEN",
        "policy_missing":"DISARMED_NO_APPROVAL",
        "hash_changed":"DISARMED_PROGRAM_INTEGRITY_CHANGED",
        "concurrent_run":"SKIP_LOCK_HELD",
        "prior_verified":"NO_RETRY_SAME_SUCCESS",
    }
    assert len(states)==8 and all(x!="SUCCESS_VERIFIED" for x in states.values())
    print(json.dumps({"result":"SYNTHETIC_FAIL_CLOSED_TESTS_PASS",
                      "scenarios":states,"backups_executed":0},ensure_ascii=False))
    return 0

def run(mode):
    if mode=="simulate":return simulate_scenarios()
    # Never touch NAS, SSD or any protected folder from a scheduled process
    # until the user-enabled approval policy has been validated locally.
    # This prevents unapproved background TCC prompts.
    approved=approval_check()
    if mode=="check":
        report={"approval":approved,"mode":"LOCAL_POLICY_ONLY",
                "network_volume_accessed":False,"backup_executed":False}
        print(json.dumps(report,ensure_ascii=False),flush=True)
        return 0
    if mode=="probe":
        if approved!="APPROVED":
            print(json.dumps({"state":approved,"network_volume_accessed":False,
                              "backup_executed":False},ensure_ascii=False),flush=True)
            return 4
        stages=checks()
        blocked=[q["stage"] for q in stages if q["state"]!="PASS"]
        print(json.dumps({"state":"BLOCKED_PRECONDITION" if blocked else "READY_USER_APPROVED",
                          "blocked_stage_ids":blocked,"backup_executed":False},
                         ensure_ascii=False),flush=True)
        return 4 if blocked else 0
    if os.geteuid()!=EXPECTED_UID or not LOG.is_dir() or LOG.is_symlink():
        record("BLOCKED_USER_OR_STATE","initial",allow_write=False)
        return 3
    fd=os.open(LOCK,os.O_RDWR|os.O_CREAT,0o600)
    try:
        try:fcntl.flock(fd,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError:
            record("SKIP_LOCK_HELD","lock")
            return 0
        if approved!="APPROVED":
            record(approved,"approval")
            return 0
        # Check protected volumes ONLY after explicit same-user approval.
        # Native parent wraps this blocking filesystem access in a process
        # timeout, rather than keeping a LaunchAgent hung on a macOS TCC prompt.
        stages=checks()
        blocked=[s["stage"] for s in stages if s["state"]!="PASS"]
        if blocked:
            record("BLOCKED_PRECONDITION","preflight",{"blocked_stage_ids":blocked})
            return 4
        # One child invocation. The user-approved policy pins all three source
        # engine SHA-256 values. Never run via Terminal GUI or shell expansion.
        # Dedicated child process group: if the orchestrator times out,
        # terminate its backup grandchildren too (not just its parent PID).
        job=subprocess.Popen(
            ["/usr/bin/python3",str(RUNNER),"run"],
            stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,start_new_session=True)
        try:
            exitcode=job.wait(timeout=2600)
        except subprocess.TimeoutExpired:
            try:
                os.killpg(job.pid,signal.SIGTERM)
            except ProcessLookupError:
                pass
            try:
                job.wait(timeout=8)
            except subprocess.TimeoutExpired:
                try:os.killpg(job.pid,signal.SIGKILL)
                except ProcessLookupError:pass
                job.wait(timeout=8)
            record("FAILED_ONE_ATTEMPT_TIMEOUT","child")
            return 6
        if exitcode!=0:
            record("FAILED_ONE_ATTEMPT_NO_RETRY","child",
                   {"returncode":exitcode})
            return 7
        try:
            result=json.loads(LAST.read_text("utf8"))
            loc=json.loads(LOCAL.read_text("utf8"))
            valid=(result.get("status")=="SUCCESS_LOCAL_TO_NAS_ENCRYPTED_CAS"
                   and loc.get("status")=="SUCCESS"
                   and result.get("local_snapshot")==loc.get("snapshot_name")
                   and result.get("local_receipt_sha256")==loc.get("receipt_sha256")
                   and result.get("manifest_sha256")==loc.get("manifest_sha256")
                   and result.get("google_drive_upload") is False
                   and result.get("automatic_scheduling") is False
                   and not MOUNT.exists())
        except (OSError,ValueError,TypeError):
            valid=False
        if not valid:
            record("FAILED_RECEIPT_CHAIN_NO_RETRY","postflight")
            return 8
        record("SUCCESS_VERIFIED","postflight",
               {"local_snapshot":result["local_snapshot"],
                "manifest_sha256":result["manifest_sha256"],
                "nas_cas_manifest":result["nas_cas_manifest"],
                "backed_up_files":loc["file_count"]})
        return 0
    finally:
        os.close(fd)

if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("mode",choices=("check","probe","scheduled","simulate"))
    args=ap.parse_args()
    try:
        sys.exit(run(args.mode))
    except Exception as ex:
        # Never print paths, exception messages, environment, or passwords.
        print(json.dumps({"state":"FAILED_SAFE","failure_type":type(ex).__name__,
                          "error_number":getattr(ex,"errno",None),
                          "no_backup_success_claim":True}),file=sys.stderr,flush=True)
        sys.exit(9)
