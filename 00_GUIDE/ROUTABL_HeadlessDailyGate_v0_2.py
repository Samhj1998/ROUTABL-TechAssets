#!/usr/bin/env python3
"""ROUTABL headless backup daily gate v0.2.

NOT installed as launchd. Direct Python only. Prevents duplicate same-day backup,
requires today's verified local snapshot before manual NAS replication, and avoids
stale receipt promotion. The real actions run only with explicit "run".
"""
import argparse
import datetime
import fcntl
import json
import os
import subprocess
import sys
from pathlib import Path
from zoneinfo import ZoneInfo

HOME = Path("/Users/yongho")
ROOT = HOME / "ROUTABL-TechAssets/00_GUIDE"
STATE = HOME / "Library/Logs/ROUTABL-AssetBackup"
LOCAL_JOB = ROOT / "ROUTABL_SelectiveSecureBackup_v2_0.py"
NAS_JOB = ROOT / "ROUTABL_SelectiveNasCopy_v2_0.py"
LOCAL_STATUS = STATE / "last_selective_v2_result.json"
NAS_STATUS = STATE / "last_selective_nas_v2_result.json"
IMAGE_MOUNT = Path("/Volumes/ROUTABL-Secure")


def today():
    return datetime.datetime.now(ZoneInfo("Asia/Seoul")).date().isoformat()


def load(path):
    if not path.is_file() or path.is_symlink():
        return {}
    try:
        return json.loads(path.read_text("utf-8"))
    except (ValueError, OSError):
        return {}


def local_day(record):
    if record.get("day_kst"):
        return record["day_kst"]
    t = record.get("created_at_kst")
    if not t:
        return None
    try:
        return datetime.datetime.fromisoformat(t).astimezone(ZoneInfo("Asia/Seoul")).date().isoformat()
    except (TypeError, ValueError):
        return None


def gate(job):
    if os.geteuid() == 0:
        return "BLOCKED_ROOT"
    if IMAGE_MOUNT.exists():
        return "BLOCKED_ENCRYPTED_VOLUME_ALREADY_OPEN"
    local = load(LOCAL_STATUS)
    nas = load(NAS_STATUS)
    valid_local = (
        local.get("status") == "SUCCESS" and
        local.get("locked_after_backup") is True and
        local.get("sha256_verified") is True and
        local_day(local) == today()
    )
    if job == "local":
        return "SKIPPED_ALREADY_SUCCESS_TODAY" if valid_local else "ELIGIBLE_MANUAL_BACKUP"
    if job == "nas":
        if not valid_local:
            return "BLOCKED_LOCAL_VERIFIED_SNAPSHOT_NOT_TODAY"
        if (nas.get("status") == "SUCCESS" and nas.get("day_kst") == today()
            and nas.get("nas_sha256_verified") is True):
            return "SKIPPED_ALREADY_SUCCESS_TODAY"
        return "ELIGIBLE_MANUAL_NAS_COPY"
    raise ValueError("unknown job")


def run(job, execute):
    if os.geteuid() == 0 or not STATE.is_dir() or STATE.is_symlink():
        raise RuntimeError("unsafe user or state")
    path = STATE / ("selective_headless_v2_" + job + ".lock")
    with path.open("a+") as f:
        os.chmod(path, 0o600)
        try:
            fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            print(json.dumps({"job": job, "result": "SKIPPED_ALREADY_RUNNING"}))
            return 0
        state = gate(job)
        if not execute or not state.startswith("ELIGIBLE_"):
            print(json.dumps({"job": job, "mode": "NO_EXECUTION" if not execute else "GUARDED",
                              "result": state, "real_job_started": False}))
            return 0 if state.startswith("SKIPPED_") or not execute else 2
        script = LOCAL_JOB if job == "local" else NAS_JOB
        if not script.is_file() or script.is_symlink():
            raise RuntimeError("trusted backup script unavailable")
        proc = subprocess.run(
            ["/usr/bin/python3", str(script), "backup"] if job == "local"
            else ["/usr/bin/python3", str(script)],
            capture_output=True, text=True, timeout=900, stdin=subprocess.DEVNULL)
        expected_file = LOCAL_STATUS if job == "local" else NAS_STATUS
        data = load(expected_file)
        verified = (data.get("status") == "SUCCESS" and
                    local_day(data) == today() if job == "local"
                    else data.get("status") == "SUCCESS" and data.get("day_kst") == today())
        if proc.returncode != 0 or not verified:
            print(json.dumps({"job": job, "result": "FAILED_NO_VERIFIED_SUCCESS",
                              "error_type": "child_failed"}), file=sys.stderr)
            return 3
        print(json.dumps({"job": job, "result": "SUCCESS",
                          "verified_receipt_for_today": True}))
        return 0


if __name__ == "__main__":
    a = argparse.ArgumentParser()
    a.add_argument("mode", choices=("check", "run"))
    a.add_argument("job", choices=("local", "nas"))
    args = a.parse_args()
    try:
        raise SystemExit(run(args.job, execute=args.mode == "run"))
    except Exception as ex:
        print(json.dumps({"job": args.job, "result": "FAILED_SAFE",
                          "error_type": type(ex).__name__}), file=sys.stderr)
        raise SystemExit(4)
