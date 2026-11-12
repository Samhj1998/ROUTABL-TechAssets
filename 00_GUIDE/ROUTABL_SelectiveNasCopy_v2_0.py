#!/usr/bin/env python3
"""ROUTABL manual NAS copy of *closed* AES-256 sparsebundle after v2 snapshot.

Append-only and non-destructive. No Terminal GUI/launchd, no secret usage, no data
decryption, no pruning, and no Google Drive calls.
"""
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
IMAGE = Path("/Volumes/SSD2TB/ROUTABL-TechAssets-Backup/ROUTABL-SecureBackup.sparsebundle")
NAS = Path("/Volumes/Dev_Assets/ROUTABL-TechAssets-Backup/snapshots")
MOUNT = Path("/Volumes/ROUTABL-Secure")
LOG = HOME / "Library/Logs/ROUTABL-AssetBackup"
LOCAL = LOG / "last_selective_v2_result.json"
STATUS = LOG / "last_selective_nas_v2_result.json"
LOCK = LOG / "selective_nas_v2.lock"
MAX_IMAGE_BYTES = 1_500_000_000


def sha256(p):
    h = hashlib.sha256()
    with p.open("rb") as stream:
        for part in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(part)
    return h.hexdigest()


def preflight():
    if os.geteuid() == 0:
        raise RuntimeError("ROOT_DISALLOWED")
    if not os.path.ismount("/Volumes/SSD2TB") or not os.path.ismount("/Volumes/Dev_Assets"):
        raise RuntimeError("STORAGE_OFFLINE")
    if not IMAGE.is_dir() or IMAGE.is_symlink() or MOUNT.exists() or NAS.is_symlink():
        raise RuntimeError("SOURCE_IMAGE_NOT_CLOSED")
    if not NAS.is_dir() or not LOG.is_dir() or LOG.is_symlink():
        raise RuntimeError("SAFE_DESTINATION_UNAVAILABLE")
    if not LOCAL.is_file():
        raise RuntimeError("LOCAL_V2_RECEIPT_MISSING")
    record = json.loads(LOCAL.read_text("utf-8"))
    if (record.get("status") != "SUCCESS" or not record.get("locked_after_backup")
        or not record.get("sha256_verified")
        or record.get("file_count", 0) < 40
        or not record.get("snapshot_name", "").startswith("ASSET_V2_")):
        raise RuntimeError("LOCAL_V2_SNAPSHOT_NOT_VERIFIED")
    i = subprocess.run(["/usr/bin/hdiutil", "info"],
                       capture_output=True, text=True, timeout=15)
    if i.returncode or str(IMAGE) in i.stdout:
        raise RuntimeError("IMAGE_MOUNTED")
    d = subprocess.run(["/usr/sbin/diskutil", "image", "info", str(IMAGE)],
                       capture_output=True, text=True, timeout=20)
    if d.returncode or "Is Encrypted: 1" not in d.stdout or "Key Size: 256" not in d.stdout:
        raise RuntimeError("ENCRYPTION_NOT_VERIFIED")
    files = sorted(p for p in IMAGE.rglob("*") if p.is_file())
    if not files or any(p.is_symlink() for p in IMAGE.rglob("*")):
        raise RuntimeError("SYMLINK_OR_MISSING_SOURCE")
    size = sum(p.stat().st_size for p in files)
    if size > MAX_IMAGE_BYTES:
        raise RuntimeError("IMAGE_EXCEEDS_APPROVED_SIZE")
    fs = os.statvfs(NAS)
    if fs.f_bavail * fs.f_frsize < size * 2 + 250_000_000:
        raise RuntimeError("NAS_INSUFFICIENT_FREE_SPACE")
    return files, size, record


def run():
    files, nbytes, local = preflight()
    fd = os.open(LOCK, os.O_RDWR | os.O_CREAT, 0o600)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        original = {}
        for p in files:
            key = p.relative_to(IMAGE).as_posix()
            st = p.stat()
            original[key] = {"sha256": sha256(p), "bytes": st.st_size, "mtime_ns": st.st_mtime_ns}
        stamp = datetime.now(ZoneInfo("Asia/Seoul")).strftime("%Y%m%d_%H%M%S_KST")
        folder = NAS / ("NAS_MANUAL_ASSET_V2_" + stamp + "_" + str(os.getpid()))
        if folder.exists():
            raise RuntimeError("DESTINATION_COLLISION")
        target = folder / IMAGE.name
        target.mkdir(parents=True, exist_ok=False, mode=0o700)
        rows = []
        for p in files:
            rel = p.relative_to(IMAGE)
            path = target / rel
            path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
            with p.open("rb") as inp, path.open("xb") as out:
                shutil.copyfileobj(inp, out, 1024 * 1024)
            os.chmod(path, 0o600)
            expected = original[rel.as_posix()]
            if path.stat().st_size != expected["bytes"] or sha256(path) != expected["sha256"]:
                raise RuntimeError("NAS_COPIED_FILE_SHA256_MISMATCH")
            rows.append({"path": rel.as_posix(), "size": expected["bytes"],
                         "sha256": expected["sha256"]})
        if MOUNT.exists():
            raise RuntimeError("ENCRYPTED_IMAGE_WAS_MOUNTED_DURING_COPY")
        for p in files:
            rel = p.relative_to(IMAGE).as_posix()
            before = original[rel]
            st = p.stat()
            if st.st_size != before["bytes"] or st.st_mtime_ns != before["mtime_ns"] or sha256(p) != before["sha256"]:
                raise RuntimeError("ENCRYPTED_IMAGE_CHANGED_DURING_COPY")
        # Restore a few already-encrypted package bands, verify, and delete
        # the temporary samples. This never exposes decrypted technical source.
        sample = sorted(rows, key=lambda x: (x["size"], x["path"]))[:8]
        with tempfile.TemporaryDirectory(prefix="routabl_nas_cipher_restore_") as scratch:
            os.chmod(scratch, 0o700)
            for n, row in enumerate(sample):
                recovered = Path(scratch) / ("%02d.part" % n)
                with (target / row["path"]).open("rb") as inp, recovered.open("xb") as out:
                    shutil.copyfileobj(inp, out, 1024 * 1024)
                if sha256(recovered) != row["sha256"]:
                    raise RuntimeError("NAS_RESTORED_CIPHERTEXT_SHA_MISMATCH")
        receipt = {
            "type": "ROUTABL_ASSET_V2_CLOSED_AES256_NAS_IMAGE_COPY",
            "created_at_kst": datetime.now(ZoneInfo("Asia/Seoul")).isoformat(),
            "local_v2_snapshot_name": local["snapshot_name"],
            "local_v2_receipt_sha256": local["receipt_sha256"],
            "source_image_closed": True,
            "aes256_checked": True,
            "source_hashes_unchanged_after_copy": True,
            "destination": str(target),
            "file_count": len(rows),
            "ciphertext_bytes": nbytes,
            "all_ciphertext_file_sha256_verified": True,
            "isolated_ciphertext_restore_samples_verified": len(sample),
            "source_files_modified": False,
            "previous_nas_snapshots_modified": False,
            "files": rows,
        }
        receipt_path = folder / "NAS_ASSET_V2_RECEIPT.json"
        with receipt_path.open("x", encoding="utf-8") as output:
            json.dump(receipt, output, ensure_ascii=False, indent=2)
            output.write("\n")
        os.chmod(receipt_path, 0o600)
        latest = {
            "status": "SUCCESS", "day_kst": datetime.now(ZoneInfo("Asia/Seoul")).date().isoformat(),
            "nas_snapshot": str(folder),
            "copied_ciphertext_file_count": len(rows),
            "copied_ciphertext_bytes": nbytes,
            "receipt_sha256": sha256(receipt_path),
            "source_image_mounted": False,
            "nas_sha256_verified": True,
            "restored_ciphertext_samples": len(sample),
        }
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=LOG,
                                         prefix=".nas-selective-", delete=False) as out:
            tmp = Path(out.name)
            json.dump(latest, out, ensure_ascii=False, indent=2)
        os.chmod(tmp, 0o600)
        os.replace(tmp, STATUS)
        print(json.dumps(latest, ensure_ascii=False))
        return 0
    finally:
        os.close(fd)


if __name__ == "__main__":
    try:
        sys.exit(run())
    except Exception as e:
        print(json.dumps({"status": "FAILED_SAFE",
                          "failure_type": type(e).__name__,
                          "no_success_claimed": True}, ensure_ascii=False), file=sys.stderr)
        sys.exit(2)
