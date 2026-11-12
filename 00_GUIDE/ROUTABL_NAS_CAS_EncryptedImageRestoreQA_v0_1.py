#!/usr/bin/env python3
"""ROUTABL: independent NAS encrypted CAS image reconstruction SHA verification.

Read-only NAS sources; temporary complete reconstructed *encrypted* sparsebundle
on SSD. Never mounts or decrypts, never touches existing snapshots or login.
No automated job installs, credentials, public uploads, or source modifications.
"""
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
import hashlib
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile

HOME=Path("/Users/yongho")
ROOT=HOME/"ROUTABL-TechAssets"
PROGRAM=ROOT/"00_GUIDE/ROUTABL_NAS_ContentAwareBackup_v0_2.py"
STAGING=Path("/Volumes/SSD2TB/ROUTABL-TechAssets-Backup/RestoreVerificationV2")
STATUS=HOME/"Library/Logs/ROUTABL-AssetBackup/last_nas_cas_restore_qa_result.json"
SECURE_MOUNT=Path("/Volumes/ROUTABL-Secure")
PHYSICAL=Path("/Volumes/SSD2TB/ROUTABL-TechAssets-Backup/ROUTABL-SecureBackup.sparsebundle")

def sha(p):
    d=hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda:f.read(1048576),b""):
            d.update(chunk)
    return d.hexdigest()

def restore():
    if os.geteuid()==0:
        raise RuntimeError("ROOT_USER_FORBIDDEN")
    if (not os.path.ismount("/Volumes/SSD2TB") or
        not os.path.ismount("/Volumes/Dev_Assets") or SECURE_MOUNT.exists()):
        raise RuntimeError("STORAGE_UNAVAILABLE_OR_IMAGE_OPEN")
    if not PROGRAM.is_file() or PROGRAM.is_symlink():
        raise RuntimeError("RECONSTRUCTION_LOGIC_UNAVAILABLE")
    spec=importlib.util.spec_from_file_location("cas_encrypted_restore",str(PROGRAM))
    m=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    m.validate_environment()
    history=m.list_manifests()
    if len(history)<2:
        raise RuntimeError("NO_REAL_CHANGE_SNAPSHOT_TO_RECONSTRUCT")
    latest=history[-1][2]
    first=history[0][2]
    if (latest["anchor_snapshot"]!=first["anchor_snapshot"] or
        latest["source"]!="local_closed_aes256_image_content_aware_incremental"):
        raise RuntimeError("UNEXPECTED_CAS_CHAIN")
    linked=m.verify_manifest(latest,full=True)
    if not (linked["all_bands_sha256_verified"] and
            linked["verified_bands"]==latest["components"]):
        raise RuntimeError("CAS_CHAIN_NOT_VERIFIED")
    if not STAGING.is_dir() or STAGING.is_symlink():
        raise RuntimeError("VERIFY_STAGING_DIRECTORY_NOT_READY")
    if not PHYSICAL.is_dir() or PHYSICAL.is_symlink():
        raise RuntimeError("LATEST_CLOSED_LOCAL_IMAGE_MISSING")
    with tempfile.TemporaryDirectory(prefix="RESTORE_CAS_ENCRYPTED_IMAGE_",dir=STAGING) as tmp:
        dirpath=Path(tmp)
        os.chmod(dirpath,0o700)
        restored=dirpath/"ROUTABL-SecureBackup.sparsebundle"
        restored.mkdir(mode=0o700)
        count=0
        copied_bytes=0
        for item in latest["files"]:
            rel=m.safe_rel(item["relative_path"])
            dest=restored/rel
            if not dest.resolve().is_relative_to(restored.resolve()):
                raise RuntimeError("CAS_RESTORE_TRAVERSAL")
            src=m.ref_path(item)
            dest.parent.mkdir(parents=True,exist_ok=True,mode=0o700)
            with src.open("rb") as inp, dest.open("xb") as out:
                shutil.copyfileobj(inp,out,1048576)
            os.chmod(dest,0o600)
            if dest.stat().st_size!=item["size"] or sha(dest)!=item["sha256"]:
                raise RuntimeError("RECONSTRUCTED_COMPONENT_HASH_MISMATCH")
            local=PHYSICAL/rel
            if (not local.is_file() or local.is_symlink() or
                local.stat().st_size!=item["size"] or sha(local)!=item["sha256"]):
                raise RuntimeError("RECONSTRUCTED_IMAGE_DIFFERS_FROM_LOCAL_CLOSED_IMAGE")
            count+=1
            copied_bytes+=item["size"]
        if count!=latest["components"] or copied_bytes!=latest["total_ciphertext_bytes"]:
            raise RuntimeError("RECONSTRUCTED_IMAGE_SIZE_MISMATCH")
        info=subprocess.run(["/usr/sbin/diskutil","image","info",str(restored)],
                            capture_output=True,text=True,stdin=subprocess.DEVNULL,timeout=30)
        if info.returncode or "Is Encrypted: 1" not in info.stdout or "Key Size: 256" not in info.stdout:
            raise RuntimeError("RECONSTRUCTED_IMAGE_AES256_STRUCTURE_INVALID")
        evidence={
            "status":"PASS_CAS_CIPHERTEXT_FULL_RESTORE",
            "checked_at_kst":datetime.now(ZoneInfo("Asia/Seoul")).isoformat(timespec="seconds"),
            "snapshot":latest["local_snapshot_name"],
            "local_receipt_sha256":latest["local_receipt_sha256"],
            "ciphertext_components_reconstructed":count,
            "ciphertext_bytes_reconstructed":copied_bytes,
            "all_components_sha256_pass":True,
            "reconstructed_matches_local_image":True,
            "restored_image_aes256_structure_pass":True,
            "sample_plaintext_extracted":False,
            "image_mounted_or_unlocked":False,
            "existing_nas_snapshot_changed":False,
            "future_anchor_prune_allowed":False,
        }
        print(json.dumps(evidence,ensure_ascii=False),flush=True)
    # Only scratch generated in the context above is deleted. Do not claim
    # clean image lock without a separate confirmation.
    if SECURE_MOUNT.exists():
        raise RuntimeError("SECURE_MOUNT_UNEXPECTED_AFTER_VERIFICATION")
    evidence["isolated_reconstruction_scratch_removed"]=True
    if STATUS.exists():
        raise RuntimeError("REFUSE_TO_OVERWRITE_EVIDENCE")
    with STATUS.open("x",encoding="utf8") as stream:
        json.dump(evidence,stream,ensure_ascii=False,indent=2)
        stream.write("\n")
    os.chmod(STATUS,0o600)
    print(json.dumps({"status":"SAVED_QA_RECEIPT","scratch_removed":True,
                      "components":count,"encrypted_only":True},ensure_ascii=False),flush=True)
    return 0

if __name__=="__main__":
    try:
        sys.exit(restore())
    except Exception as e:
        print(json.dumps({"status":"FAILED_SAFE","failure_type":type(e).__name__,
                          "claim_complete":False},ensure_ascii=False),file=sys.stderr,flush=True)
        sys.exit(3)
