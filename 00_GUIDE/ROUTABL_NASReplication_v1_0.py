#!/usr/bin/env python3
"""NAS mirror of a *closed*, AES-256 encrypted ROUTABL sparsebundle.
No secret retrieval, destructive operations, or snapshot pruning."""
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
import fcntl
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile

HOME = Path("/Users/yongho")
SSD = Path("/Volumes/SSD2TB")
NAS = Path("/Volumes/Dev_Assets")
IMAGE = SSD / "ROUTABL-TechAssets-Backup/ROUTABL-SecureBackup.sparsebundle"
ACTIVE = Path("/Volumes/ROUTABL-Secure")
DEST = NAS / "ROUTABL-TechAssets-Backup/snapshots"
STATE = HOME / "Library/Logs/ROUTABL-AssetBackup"
LOCAL_STATUS = STATE / "last_result.json"
NAS_STATUS = STATE / "last_nas_result.json"
LOCK = STATE / "nas_copy.lock"
MAX_BYTES = 2_000_000_000

def sha256(path):
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def now():
    return datetime.now(ZoneInfo("Asia/Seoul"))

def report(payload):
    payload["checked_at_kst"] = now().isoformat()
    fd, temp = tempfile.mkstemp(prefix=".nas-result-", dir=str(STATE))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as out:
            json.dump(payload, out, indent=2, ensure_ascii=False)
            out.write("\n")
        os.chmod(temp, 0o600)
        os.replace(temp, NAS_STATUS)
    finally:
        if os.path.exists(temp):
            os.unlink(temp)
    print(json.dumps(payload, ensure_ascii=False), flush=True)

def run():
    os.umask(0o077)
    if os.geteuid() == 0 or not STATE.is_dir() or STATE.is_symlink():
        raise RuntimeError("unsafe_user_or_state")
    with LOCK.open("a+") as lock:
        os.chmod(LOCK, 0o600)
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            print(json.dumps({"status": "SKIPPED_ALREADY_RUNNING"}))
            return 0
        today = now().date().isoformat()
        if NAS_STATUS.is_file():
            try:
                prior = json.loads(NAS_STATUS.read_text(encoding="utf-8"))
                if prior.get("status") == "SUCCESS" and prior.get("day_kst") == today:
                    print(json.dumps({"status": "SKIPPED_ALREADY_SUCCEEDED_TODAY", "day_kst": today}))
                    return 0
            except (OSError, ValueError):
                pass
        if not LOCAL_STATUS.is_file():
            raise RuntimeError("local_backup_receipt_missing")
        local = json.loads(LOCAL_STATUS.read_text(encoding="utf-8"))
        if (local.get("status") != "SUCCESS" or local.get("day_kst") != today
                or not local.get("locked_after_backup", False)):
            raise RuntimeError("local_backup_not_verified_today")
        completed = datetime.fromisoformat(local["checked_at_kst"]).astimezone(ZoneInfo("Asia/Seoul"))
        if completed.hour < 4 or (completed.hour == 4 and completed.minute < 30):
            raise RuntimeError("local_backup_too_early_for_daily_cycle")
        if (not os.path.ismount(NAS) or not os.path.ismount(SSD)
                or not IMAGE.is_dir() or IMAGE.is_symlink()
                or ACTIVE.exists()):
            raise RuntimeError("nas_offline_image_missing_or_mounted")
        info = subprocess.run(["/usr/sbin/diskutil", "image", "info", str(IMAGE)],
                              capture_output=True, text=True, timeout=40)
        if info.returncode or "Is Encrypted: 1" not in info.stdout or "Key Size: 256" not in info.stdout:
            raise RuntimeError("source_encryption_unverified")
        attached = subprocess.run(["/usr/bin/hdiutil", "info"],
                                  capture_output=True, text=True, timeout=20)
        if attached.returncode or str(IMAGE) in attached.stdout:
            raise RuntimeError("source_image_attached")
        files = sorted(p for p in IMAGE.rglob("*") if p.is_file())
        if not files or any(p.is_symlink() for p in IMAGE.rglob("*")):
            raise RuntimeError("empty_or_symlink_source")
        if sum(p.stat().st_size for p in files) > MAX_BYTES:
            raise RuntimeError("source_exceeds_2gb_per_copy_safety_limit")
        before = {p.relative_to(IMAGE).as_posix():
                  {"size": p.stat().st_size, "mtime_ns": p.stat().st_mtime_ns,
                   "sha256": sha256(p)} for p in files}
        timestamp = now().strftime("%Y%m%d_%H%M%S_KST")
        snapshot = DEST / ("NAS_AUTO_" + timestamp)
        copied = snapshot / IMAGE.name
        if snapshot.exists():
            raise RuntimeError("destination_collision")
        copied.mkdir(parents=True, exist_ok=False, mode=0o700)
        members = []
        for source in files:
            relative = source.relative_to(IMAGE)
            target = copied / relative
            target.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
            with source.open("rb") as reader, target.open("xb") as writer:
                shutil.copyfileobj(reader, writer, 1024 * 1024)
            os.chmod(target, 0o600)
            expected = before[relative.as_posix()]
            if sha256(target) != expected["sha256"] or target.stat().st_size != expected["size"]:
                raise RuntimeError("nas_copy_hash_mismatch_" + relative.as_posix())
            members.append({"path": relative.as_posix(), "size": expected["size"],
                            "sha256": expected["sha256"]})
        if ACTIVE.exists():
            raise RuntimeError("image_mounted_during_nas_copy")
        for source in files:
            relative = source.relative_to(IMAGE).as_posix()
            stat = source.stat()
            old = before[relative]
            if (stat.st_size != old["size"] or stat.st_mtime_ns != old["mtime_ns"]
                    or sha256(source) != old["sha256"]):
                raise RuntimeError("source_changed_during_nas_copy")
        receipt = {"day_kst": today, "created_at_kst": now().isoformat(),
                   "source": str(IMAGE), "destination": str(copied),
                   "type": "ROUTABL_ENCRYPTED_NAS_SNAPSHOT",
                   "file_count": len(members), "verified": True,
                   "source_closed": True, "source_hash_unchanged": True,
                   "files": members, "originals_not_modified": True}
        receipt_path = snapshot / "NAS_ENCRYPTED_BACKUP_RECEIPT.json"
        with receipt_path.open("x", encoding="utf-8") as out:
            json.dump(receipt, out, indent=2, ensure_ascii=False)
        os.chmod(receipt_path, 0o600)
        report({"status": "SUCCESS", "day_kst": today,
                "nas_snapshot": str(snapshot), "file_count": len(members),
                "receipt_sha256": sha256(receipt_path), "image_mounted": False})
        return 0

if __name__ == "__main__":
    try:
        sys.exit(run())
    except Exception as ex:
        reason = str(ex)[:180]
        try:
            report({"status": "FAILED", "day_kst": now().date().isoformat(),
                    "reason": reason})
        except Exception:
            print(json.dumps({"status": "FAILED", "reason": reason}), file=sys.stderr)
        sys.exit(1)
