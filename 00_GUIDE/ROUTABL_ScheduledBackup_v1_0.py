#!/usr/bin/env python3
"""Local launchd wrapper for ROUTABL AES-256 backup. No secret retrieval or deletion."""
import datetime
import fcntl
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from zoneinfo import ZoneInfo

USER = "/Users/yongho"
SCRIPT = Path(USER + "/ROUTABL-TechAssets/00_GUIDE/ROUTABL_SecureBackup_v1_0.py")
STATE = Path(USER + "/Library/Logs/ROUTABL-AssetBackup")
LOCK = STATE / "backup.lock"
STATUS = STATE / "last_result.json"
IMAGE = "/Volumes/SSD2TB/ROUTABL-TechAssets-Backup/ROUTABL-SecureBackup.sparsebundle"
MOUNT = Path("/Volumes/ROUTABL-Secure")

def record(report):
    report["checked_at_kst"] = datetime.datetime.now(ZoneInfo("Asia/Seoul")).isoformat()
    fd, temp = tempfile.mkstemp(prefix=".result-", dir=STATE)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
            f.write("\n")
        os.chmod(temp, 0o600)
        os.replace(temp, STATUS)
    finally:
        if os.path.exists(temp):
            os.unlink(temp)
    print(json.dumps(report, ensure_ascii=False), flush=True)

def try_eject_after_timeout():
    if not MOUNT.is_dir():
        return "already_unmounted"
    info = subprocess.run(["/usr/bin/hdiutil", "info"],
                          capture_output=True, text=True, timeout=20)
    if info.returncode or IMAGE not in info.stdout:
        return "mount_requires_manual_review"
    detached = subprocess.run(["/usr/bin/hdiutil", "detach", str(MOUNT)],
                              capture_output=True, timeout=30)
    return "ejected" if detached.returncode == 0 and not MOUNT.exists() else "eject_failed"

def main():
    os.umask(0o077)
    if os.geteuid() == 0:
        print("Do not run as root", file=sys.stderr)
        return 1
    STATE.mkdir(parents=True, exist_ok=True, mode=0o700)
    if STATE.is_symlink() or STATE.stat().st_uid != os.getuid():
        print("Unsafe state directory", file=sys.stderr)
        return 1
    os.chmod(STATE, 0o700)
    with LOCK.open("a+") as lock_file:
        os.chmod(LOCK, 0o600)
        try:
            fcntl.flock(lock_file, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            print(json.dumps({"status": "SKIPPED_ALREADY_RUNNING"}))
            return 0
        today = datetime.datetime.now(ZoneInfo("Asia/Seoul")).date().isoformat()
        if STATUS.is_file():
            try:
                prior = json.loads(STATUS.read_text(encoding="utf-8"))
                if prior.get("status") == "SUCCESS" and prior.get("day_kst") == today:
                    print(json.dumps({"status": "SKIPPED_ALREADY_SUCCEEDED_TODAY", "day_kst": today}))
                    return 0
            except (OSError, ValueError):
                pass
        if not SCRIPT.is_file() or SCRIPT.is_symlink():
            record({"status": "FAILED", "day_kst": today, "reason": "backup_script_missing"})
            return 2
        try:
            proc = subprocess.run(["/usr/bin/python3", str(SCRIPT)],
                                  capture_output=True, text=True, timeout=600)
            if proc.returncode == 0:
                data = json.loads(proc.stdout)
                if data.get("sha256_verified") is True and not MOUNT.exists():
                    record({"status": "SUCCESS", "day_kst": today,
                            "file_count": data.get("file_count"),
                            "snapshot": data.get("snapshot"),
                            "receipt_sha256": data.get("receipt_sha256"),
                            "locked_after_backup": True})
                    return 0
                record({"status": "FAILED", "day_kst": today,
                        "reason": "verification_or_eject_not_confirmed"})
                return 3
            reason = "underlying_backup_error"
            try:
                response = json.loads(proc.stderr)
                reason = str(response.get("reason", reason))[:200]
            except (ValueError, TypeError):
                pass
            record({"status": "FAILED", "day_kst": today, "reason": reason,
                    "secure_volume_mounted": MOUNT.exists()})
            return 3
        except subprocess.TimeoutExpired:
            try:
                detach = try_eject_after_timeout()
            except Exception:
                detach = "manual_review"
            record({"status": "FAILED", "day_kst": today,
                    "reason": "backup_timeout", "eject_after_timeout": detach})
            return 4
        except Exception as ex:
            record({"status": "FAILED", "day_kst": today,
                    "reason": "runner_error_" + type(ex).__name__})
            return 5

if __name__ == "__main__":
    raise SystemExit(main())
