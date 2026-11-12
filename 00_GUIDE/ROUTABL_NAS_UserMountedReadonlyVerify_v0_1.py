#!/usr/bin/env python3
"""Verify full contents of NAS-reconstructed AES image after USER read-only mount.

Does NOT mount/detach, unlock Keychain, ask for passwords, modify source, install
launchd, or copy decrypted files. Returns blocked if staging image not mounted
as read-only. Requires real hdiutil attachment source == the NAS CAS restore stage.
"""
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
import hashlib
import json
import os
import plistlib
import subprocess
import sys

HOME=Path("/Users/yongho")
ROOT=HOME/"ROUTABL-TechAssets"
STATUS=HOME/"Library/Logs/ROUTABL-AssetBackup/last_selective_v21_result.json"
SNAPSHOT="ASSET_V21_20261104_000342_KST_26699"
BASEDIR=Path("/Volumes/SSD2TB/ROUTABL-TechAssets-Backup/RestoreVerificationV2")
STAGED=BASEDIR/("USER_READONLY_MOUNT_"+SNAPSHOT)/"ROUTABL-SecureBackup.sparsebundle"
RECEIPT_PATH=ROOT/"60_AUDIT/NAS_DECRYPTED_READONLY_INTERNAL_VERIFICATION_20261104.json"

def sha(file):
    h=hashlib.sha256()
    with file.open("rb") as stream:
        for part in iter(lambda: stream.read(1024*1024),b""):
            h.update(part)
    return h.hexdigest()

def find_only_exact_image_mount():
    p=subprocess.run(["/usr/bin/hdiutil","info","-plist"],capture_output=True,
                     stdin=subprocess.DEVNULL,timeout=15)
    if p.returncode!=0:raise RuntimeError("IMAGE_MOUNT_METADATA_UNAVAILABLE")
    data=plistlib.loads(p.stdout)
    found=[]
    for img in data.get("images",[]):
        path=img.get("image-path","")
        if path==str(STAGED) or (path and Path(path).resolve()==STAGED.resolve()):
            points=[e["mount-point"] for e in img.get("system-entities",[])
                    if e.get("mount-point")]
            found.extend(points)
    if len(found)!=1:raise RuntimeError("STAGED_NAS_IMAGE_NOT_MOUNTED_EXACTLY_ONCE")
    mp=Path(found[0])
    if not mp.is_dir() or not os.path.ismount(mp):
        raise RuntimeError("IMAGE_MOUNTPOINT_NOT_VALID")
    # Verified current filesystems expose ST_RDONLY in statvfs flags.
    readonly_flag=getattr(os,"ST_RDONLY",None)
    if readonly_flag is None or not (os.statvfs(mp).f_flag & readonly_flag):
        raise RuntimeError("MOUNT_IS_NOT_READ_ONLY")
    return mp

def main():
    if os.geteuid()!=501:raise RuntimeError("USER_CONTEXT_UNEXPECTED")
    if not STAGED.is_dir() or STAGED.is_symlink():
        raise RuntimeError("NAS_RESTORED_IMAGE_STAGING_MISSING")
    if RECEIPT_PATH.exists():
        raise RuntimeError("REFUSE_OVERWRITE_PREVIOUS_VERIFICATION")
    mp=find_only_exact_image_mount()
    status=json.loads(STATUS.read_text("utf8"))
    if (status.get("status")!="SUCCESS" or status.get("snapshot_name")!=SNAPSHOT
        or status.get("file_count")!=3308):
        raise RuntimeError("LOCAL_VERIFIED_RECEIPT_MISMATCH")
    folder=mp/"snapshots"/SNAPSHOT
    inner=folder/"snapshot_receipt.json"
    if not inner.is_file() or inner.is_symlink() or sha(inner)!=status["receipt_sha256"]:
        raise RuntimeError("INSIDE_IMAGE_RECEIPT_SHA_MISMATCH")
    rec=json.loads(inner.read_text("utf8"))
    rows=rec.get("records",[])
    if len(rows)!=3308 or rec.get("source_manifest")!="asset_manifest_v0.13.json":
        raise RuntimeError("INSIDE_IMAGE_EXPECTED_FILE_COUNT_MISMATCH")
    verified=0
    total=0
    for row in rows:
        rel=Path(row["relative_path"])
        if rel.is_absolute() or ".." in rel.parts or str(rel).startswith("."):
            raise RuntimeError("INVALID_INNER_RELATIVE_PATH")
        src=folder/rel
        if src.is_symlink() or not src.is_file():
            raise RuntimeError("INNER_FILE_MISSING_OR_LINK")
        if not src.resolve().is_relative_to(folder.resolve()):
            raise RuntimeError("INNER_FILE_OUTSIDE_SNAPSHOT")
        if src.stat().st_size!=row["size"] or sha(src)!=row["sha256"]:
            raise RuntimeError("INNER_FILE_HASH_MISMATCH")
        verified+=1
        total+=row["size"]
    record={
        "status":"PASS_NAS_DECRYPTED_READONLY_FULL_INTERNAL_SHA",
        "checked_at_kst":datetime.now(ZoneInfo("Asia/Seoul")).isoformat(timespec="seconds"),
        "source":"NAS_CAS_268_BANDS_RECONSTRUCTED_AES_IMAGE",
        "reconstruction_source":str(STAGED),
        "snapshot":SNAPSHOT,
        "local_receipt_sha256":status["receipt_sha256"],
        "files_verified_sha256":verified,
        "plaintext_bytes_read_without_export":total,
        "image_readonly_mount_confirmed":True,
        "inner_receipt_sha256_confirmed":True,
        "credential_read_or_saved":False,
        "encrypted_image_mounted_by_verifier":False,
        "user_responsible_for_manual_detach":True
    }
    with RECEIPT_PATH.open("x",encoding="utf8") as out:
        json.dump(record,out,ensure_ascii=False,indent=2);out.write("\n")
    os.chmod(RECEIPT_PATH,0o600)
    print(json.dumps({"status":record["status"],"files_verified":verified,
                      "image_readonly":True,"password_never_requested":True},ensure_ascii=False))
    return 0

if __name__=="__main__":
    try:sys.exit(main())
    except Exception as e:
        print(json.dumps({"status":"BLOCKED_OR_FAILED_SAFE",
                          "failure_type":type(e).__name__,
                          "full_restore_not_claimed":True},ensure_ascii=False),file=sys.stderr)
        sys.exit(2)
