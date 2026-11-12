#!/usr/bin/env python3
"""ROUTABL secure snapshot v1.0. Safe local backup; no stored or requested password."""
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys

SOURCE = Path("/Users/yongho/ROUTABL-TechAssets")
DISK = Path("/Volumes/SSD2TB")
IMAGE = DISK / "ROUTABL-TechAssets-Backup/ROUTABL-SecureBackup.sparsebundle"
VOLUME = Path("/Volumes/ROUTABL-Secure")
INCLUDE = ("00_GUIDE", "20_ORIGINALS", "30_REGISTRY", "50_VERIFIED", "60_AUDIT", "70_EXPORTS")
FORBIDDEN = re.compile(r"(^\.env($|\.)|adminsdk|credential|private.?key|secret|token|\.pem$|\.p12$|\.key$)", re.I)
MAX_FILE = 100_000_000
MAX_TOTAL = 1_000_000_000

def sha256(p):
    h = hashlib.sha256()
    with p.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()

def call(args, timeout=35):
    return subprocess.run(args, capture_output=True, text=True, timeout=timeout)

def make_snapshot():
    if os.geteuid() == 0:
        raise RuntimeError("Refusing root execution")
    if not os.path.ismount(DISK) or not IMAGE.is_dir() or IMAGE.is_symlink():
        raise RuntimeError("SSD/image unavailable or unsafe")
    if VOLUME.exists():
        raise RuntimeError("Encrypted image already mounted: do not interfere with another session")
    info = call(["/usr/sbin/diskutil", "image", "info", str(IMAGE)])
    if info.returncode or "Is Encrypted: 1" not in info.stdout or "Key Size: 256" not in info.stdout:
        raise RuntimeError("Image AES-256 verification failed")
    files = []
    for part in INCLUDE:
        folder = SOURCE / part
        if not folder.is_dir() or folder.is_symlink():
            raise RuntimeError("Missing or unsafe source directory: " + part)
        for p in folder.rglob("*"):
            if p.is_symlink():
                raise RuntimeError("Refuse symlink in approved source tree: " + part)
            if not p.is_file() or p.name.startswith(".") or FORBIDDEN.search(p.name):
                continue
            if p.stat().st_size > MAX_FILE:
                raise RuntimeError("Source too large; needs approval: " + str(p.relative_to(SOURCE)))
            files.append(p)
    files.sort()
    if sum(p.stat().st_size for p in files) > MAX_TOTAL:
        raise RuntimeError("Backup exceeds 1GB safety limit")
    stamp = datetime.now(ZoneInfo("Asia/Seoul")).strftime("%Y%m%d_%H%M%S_KST")
    # Use dedicated image only; never modify source files.
    attached = False
    try:
        r = call(["/usr/bin/hdiutil", "attach", "-quiet", "-nobrowse", "-noautoopen", str(IMAGE)], timeout=20)
        if r.returncode or not VOLUME.is_dir():
            raise RuntimeError("Could not unlock with Keychain. Login/Keychain may need attention")
        attached = True
        info = call(["/usr/bin/hdiutil", "info"], timeout=15)
        if info.returncode or str(IMAGE) not in info.stdout:
            raise RuntimeError("Mounted volume not verified as expected image")
        root = VOLUME / "snapshots" / ("AUTO_" + stamp)
        if root.exists():
            raise RuntimeError("Snapshot name collision; refusing overwrite")
        target = root / "ROUTABL-TechAssets"
        target.mkdir(parents=True, mode=0o700)
        rows = []
        for p in files:
            rel = p.relative_to(SOURCE)
            target_file = target / rel
            target_file.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
            before = sha256(p)
            with p.open("rb") as src, target_file.open("xb") as out:
                shutil.copyfileobj(src, out)
            os.chmod(target_file, 0o700 if p.suffix == ".command" else 0o600)
            if before != sha256(p) or before != sha256(target_file):
                raise RuntimeError("Source changed or backup hash mismatch; partial snapshot remains")
            rows.append({"relative_path": rel.as_posix(), "bytes": target_file.stat().st_size, "sha256": before})
        receipt = {"created_at_kst": stamp, "type": "ROUTABL_AES256_SNAPSHOT",
                   "source": str(SOURCE), "target": str(target), "file_count": len(rows),
                   "all_sha256_verified": True, "encrypted_image": str(IMAGE),
                   "files": rows, "not_included": ["10_INBOX", "40_WORKING", "Firebase live DB", "ChatGPT entire Library"]}
        output = root / "snapshot_receipt.json"
        with output.open("x", encoding="utf-8") as f:
            json.dump(receipt, f, indent=2, ensure_ascii=False)
        os.chmod(output, 0o600)
        result = {"snapshot": str(root), "file_count": len(rows),
                  "sha256_verified": True, "receipt_sha256": sha256(output)}
        return result
    finally:
        if attached:
            call(["/usr/bin/hdiutil", "detach", str(VOLUME)], timeout=20)
            if VOLUME.exists():
                raise RuntimeError("WARNING: encrypted volume not ejected; manually eject in Finder")

if __name__ == "__main__":
    try:
        print(json.dumps(make_snapshot(), ensure_ascii=False))
    except Exception as ex:
        print(json.dumps({"status": "FAILED", "reason": str(ex)}, ensure_ascii=False), file=sys.stderr)
        sys.exit(1)
