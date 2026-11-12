#!/usr/bin/env python3
"""ROUTABL NAS content-aware encrypted image retention, experimental v0.1.

A safe baseline *references* an existing, SHA-verified, full NAS sparsebundle
without copying it again. Future snapshots can reuse SHA-identical encrypted
components and write only changed ciphertext bands as immutable hash objects.

No backup pruning, no launchd, no decryption, no keys, no GitHub/Drive calls.
The referenced full NAS anchor must remain undeleted until all dependent
manifests are independently migrated and verified.
"""
from __future__ import annotations
import argparse
import datetime
import fcntl
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from zoneinfo import ZoneInfo

HOME=Path("/Users/yongho")
NAS_BASE=Path("/Volumes/Dev_Assets/ROUTABL-TechAssets-Backup/snapshots")
CAS=NAS_BASE/"ROUTABL-Ciphertext-CAS-v0_1"
MANIFESTS=CAS/"manifests"
BLOBS=CAS/"blobs"
ANCHOR_IMAGE_NAME="ROUTABL-SecureBackup.sparsebundle"
SSD_IMAGE=Path("/Volumes/SSD2TB/ROUTABL-TechAssets-Backup")/ANCHOR_IMAGE_NAME
MOUNT=Path("/Volumes/ROUTABL-Secure")
LOG=HOME/"Library/Logs/ROUTABL-AssetBackup"
LOCAL=LOG/"last_selective_v21_result.json"
NAS=LOG/"last_selective_nas_v21_result.json"
LIMIT_BYTES=19_000_000_000
LIMIT_FILES=10000
DIGEST=re.compile(r"^[0-9a-f]{64}$")

def now():
    return datetime.datetime.now(ZoneInfo("Asia/Seoul")).isoformat(timespec="seconds")

def sha(p):
    h=hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda:f.read(1024*1024),b""):
            h.update(chunk)
    return h.hexdigest()

def receipt(path):
    if not path.is_file() or path.is_symlink():
        raise RuntimeError("RECEIPT_MISSING")
    data=json.loads(path.read_text("utf-8"))
    if not isinstance(data,dict):raise RuntimeError("INVALID_RECEIPT")
    return data

def checked_nas_path(value):
    path=Path(value)
    if path.is_symlink() or path.parent!=NAS_BASE or not path.is_dir():
        raise RuntimeError("INVALID_NAS_ANCHOR")
    if not path.name.startswith("NAS_MANUAL_ASSET_V21_"):
        raise RuntimeError("INVALID_NAS_ANCHOR_NAME")
    return path

def safe_rel(s):
    if not isinstance(s,str) or len(s)>400 or "\x00" in s:
        raise RuntimeError("INVALID_BAND_PATH")
    p=Path(s)
    if p.is_absolute() or any(a in (".","..","") for a in p.parts) or s.startswith("."):
        raise RuntimeError("INVALID_BAND_PATH")
    return p

def validate_environment():
    if os.geteuid()==0:
        raise RuntimeError("ROOT_DISALLOWED")
    if not os.path.ismount("/Volumes/Dev_Assets") or not os.path.ismount("/Volumes/SSD2TB"):
        raise RuntimeError("MOUNT_MISSING")
    if MOUNT.exists():
        raise RuntimeError("LIVE_IMAGE_MOUNTED")
    if CAS.is_symlink() or NAS_BASE.is_symlink():
        raise RuntimeError("UNSAFE_NAS_DIRECTORY")
    info=subprocess.run(["/usr/bin/hdiutil","info"],capture_output=True,text=True,timeout=15)
    if info.returncode!=0 or str(SSD_IMAGE) in info.stdout:
        raise RuntimeError("SOURCE_DISK_IMAGE_NOT_CLOSED")

def nas_baseline():
    local=receipt(LOCAL)
    nas=receipt(NAS)
    if local.get("status")!="SUCCESS" or nas.get("status")!="SUCCESS":
        raise RuntimeError("BACKUP_RECEIPT_NOT_SUCCESS")
    if (nas.get("local_receipt_sha256")!=local.get("receipt_sha256")
        or nas.get("local_snapshot_name")!=local.get("snapshot_name")
        or nas.get("manifest_sha256")!=local.get("manifest_sha256")
        or nas.get("selection_sha256")!=local.get("selection_sha256")):
        raise RuntimeError("BACKUP_LINEAGE_MISMATCH")
    folder=checked_nas_path(nas["nas_snapshot"])
    file=folder/"NAS_ASSET_V21_RECEIPT.json"
    if sha(file)!=nas.get("receipt_sha256"):
        raise RuntimeError("NAS_RECEIPT_HASH_MISMATCH")
    raw=receipt(file)
    if (raw.get("local_v21_receipt_sha256")!=local["receipt_sha256"]
        or raw.get("file_count")!=nas["copied_ciphertext_file_count"]
        or raw.get("ciphertext_bytes")!=nas["copied_ciphertext_bytes"]):
        raise RuntimeError("NAS_RECEIPT_CONTENT_MISMATCH")
    return folder,local,nas,raw

def lock():
    CAS.mkdir(mode=0o700,parents=False,exist_ok=True)
    MANIFESTS.mkdir(mode=0o700,exist_ok=True)
    BLOBS.mkdir(mode=0o700,exist_ok=True)
    fd=os.open(CAS/"writer.lock",os.O_CREAT|os.O_RDWR,0o600)
    fcntl.flock(fd,fcntl.LOCK_EX|fcntl.LOCK_NB)
    return fd

def list_manifests():
    result=[]
    for p in MANIFESTS.glob("CAS_*.json"):
        if p.is_symlink():raise RuntimeError("UNSAFE_MANIFEST_SYMLINK")
        j=receipt(p)
        if j.get("type")!="ROUTABL_CIPHERTEXT_CAS_V01" or not j.get("completed"):
            raise RuntimeError("INVALID_EXISTING_CAS")
        result.append((j["created_kst"],p,j))
    return sorted(result,key=lambda row:(row[0],row[1].name))

def checked_file(root,relative):
    rel=safe_rel(relative)
    path=root/rel
    if path.is_symlink() or not path.is_file():
        raise RuntimeError("CIPHERTEXT_BAND_MISSING")
    if not path.resolve().is_relative_to(root.resolve()):
        raise RuntimeError("CIPHERTEXT_OUTSIDE_ROOT")
    return path

def ref_path(record):
    d=record["sha256"]
    if not isinstance(d,str) or not DIGEST.fullmatch(d):
        raise RuntimeError("INVALID_CIPHER_DIGEST")
    ref=record["reference"]
    if ref["type"]=="anchor":
        root=checked_nas_path(ref["snapshot"])/ANCHOR_IMAGE_NAME
        return checked_file(root,ref["relative_path"])
    if ref["type"]=="blob":
        p=BLOBS/d[:2]/d
        if p.is_symlink() or not p.is_file() or not p.resolve().is_relative_to(BLOBS.resolve()):
            raise RuntimeError("OBJECT_BLOB_MISSING")
        return p
    raise RuntimeError("INVALID_CIPHER_REFERENCE")

def verify_manifest(record, full=True):
    files=record["files"]
    if not isinstance(files,list) or len(files)<1 or len(files)>LIMIT_FILES:
        raise RuntimeError("INVALID_CAS_COUNT")
    names=set()
    total=0
    for row in files:
        name=safe_rel(row["relative_path"]).as_posix()
        if name in names:raise RuntimeError("DUPLICATE_CIPHER_RELATIVE")
        names.add(name)
        if not DIGEST.fullmatch(row["sha256"]):
            raise RuntimeError("INVALID_CIPHER_DIGEST")
        target=ref_path(row)
        if target.stat().st_size!=row["size"]:
            raise RuntimeError("REFERENCED_BAND_SIZE_MISMATCH")
        if full and sha(target)!=row["sha256"]:
            raise RuntimeError("REFERENCED_BAND_SHA_MISMATCH")
        total+=row["size"]
    if total!=record["total_ciphertext_bytes"] or len(files)!=record["components"]:
        raise RuntimeError("CAS_TOTALS_MISMATCH")
    return {"verified_bands":len(files),"referenced_ciphertext_bytes":total,
            "all_bands_sha256_verified":full}

def write_manifest(payload, key):
    if not re.fullmatch(r"ASSET_V21_[0-9A-Za-z_]+",key):
        raise RuntimeError("UNSAFE_SNAPSHOT_ID")
    dest=MANIFESTS/("CAS_"+key+".json")
    if dest.exists():raise RuntimeError("SAME_SNAPSHOT_ALREADY_INDEXED")
    with tempfile.NamedTemporaryFile(mode="w",encoding="utf8",dir=MANIFESTS,
                                     prefix=".draft-cas-",delete=False) as stream:
        tmp=Path(stream.name)
        json.dump(payload,stream,ensure_ascii=False,indent=2)
        stream.write("\n")
    os.chmod(tmp,0o600)
    # NAS SMB shares may reject hard links (os.link), while same-directory
    # rename has been explicitly tested to work. The single-writer lock and
    # destination existence check above prevent our tool from overwriting data.
    os.rename(tmp,dest)
    return dest

def seed():
    validate_environment()
    fd=lock()
    try:
        if list_manifests():raise RuntimeError("CAS_ALREADY_HAS_BASELINE")
        anchor,local,nas,raw=nas_baseline()
        entries=[]
        bytes_total=0
        image=anchor/ANCHOR_IMAGE_NAME
        for item in raw["files"]:
            p=checked_file(image,item["path"])
            if p.stat().st_size!=item["size"] or sha(p)!=item["sha256"]:
                raise RuntimeError("ANCHOR_COMPONENT_HASH_MISMATCH")
            entries.append({
                "relative_path":safe_rel(item["path"]).as_posix(),
                "sha256":item["sha256"],"size":item["size"],
                "reference":{"type":"anchor","snapshot":str(anchor),
                             "relative_path":item["path"]}})
            bytes_total+=item["size"]
        if len(entries)!=nas["copied_ciphertext_file_count"] or bytes_total!=nas["copied_ciphertext_bytes"]:
            raise RuntimeError("BASELINE_BYTECOUNT_MISMATCH")
        payload={
            "type":"ROUTABL_CIPHERTEXT_CAS_V01","completed":True,
            "created_kst":now(),"local_snapshot_name":local["snapshot_name"],
            "local_receipt_sha256":local["receipt_sha256"],
            "manifest_sha256":local["manifest_sha256"],
            "selection_sha256":local["selection_sha256"],
            "source":"verified_existing_nas_v21_full_encrypted_copy",
            "anchor_snapshot":str(anchor),
            "warning_anchor_must_be_retained":True,
            "new_ciphertext_bytes_copied":0,
            "reused_ciphertext_components":len(entries),
            "components":len(entries),"total_ciphertext_bytes":bytes_total,
            "files":entries}
        verified=verify_manifest(payload,full=True)
        output=write_manifest(payload,local["snapshot_name"])
        print(json.dumps({"result":"BASELINE_SEEDED_SHA256_VERIFIED",
            "manifest_path":str(output),"files":verified["verified_bands"],
            "reused_encrypted_bytes":bytes_total,"new_encrypted_bytes":0,
            "previous_nas_full_snapshot_preserved":True,
            "automatic_scheduling_enabled":False},ensure_ascii=False),flush=True)
        return 0
    finally:os.close(fd)

def current_local():
    record=receipt(LOCAL)
    if (record.get("status")!="SUCCESS" or not record.get("locked_after_backup")
        or not record.get("sha256_verified") or
        not str(record.get("snapshot_name","")).startswith("ASSET_V21_")):
        raise RuntimeError("CURRENT_LOCAL_RECEIPT_NOT_VERIFIED")
    return record

def capture():
    validate_environment()
    fd=lock()
    try:
        history=list_manifests()
        if not history:
            raise RuntimeError("SEED_NAS_ANCHOR_FIRST")
        prior=history[-1][2]
        local=current_local()
        if any(j.get("local_snapshot_name")==local["snapshot_name"] for _,_,j in history):
            check=next(j for _,_,j in history if j["local_snapshot_name"]==local["snapshot_name"])
            print(json.dumps({"result":"SNAPSHOT_ALREADY_INDEXED","verification":verify_manifest(check)}))
            return 0
        if local["snapshot_name"]==prior["local_snapshot_name"]:
            raise RuntimeError("SNAPSHOT_IDENTICAL")
        if not SSD_IMAGE.is_dir() or SSD_IMAGE.is_symlink():
            raise RuntimeError("CLOSED_SOURCE_IMAGE_NOT_FOUND")
        disk=subprocess.run(["/usr/sbin/diskutil","image","info",str(SSD_IMAGE)],
                            capture_output=True,text=True,timeout=30)
        if disk.returncode or "Is Encrypted: 1" not in disk.stdout or "Key Size: 256" not in disk.stdout:
            raise RuntimeError("AES256_SOURCE_NOT_VERIFIED")
        files=sorted(p for p in SSD_IMAGE.rglob("*") if p.is_file())
        if not files or len(files)>LIMIT_FILES or any(p.is_symlink() for p in SSD_IMAGE.rglob("*")):
            raise RuntimeError("INVALID_SPARSEBUNDLE_FILES")
        previous={v["relative_path"]:v for v in prior["files"]}
        output=[]
        copied_count=copied_bytes=reused_count=total=0
        for p in files:
            rel=p.relative_to(SSD_IMAGE).as_posix()
            safe_rel(rel)
            before=p.stat()
            size=before.st_size
            total+=size
            if total>LIMIT_BYTES:raise RuntimeError("CAS_EXCEEDS_LIMIT")
            digest=sha(p)
            old=previous.get(rel)
            if old and old["sha256"]==digest and old["size"]==size:
                # Fail closed if baseline or existing stored object disappeared.
                if sha(ref_path(old))!=digest:raise RuntimeError("REUSED_REFERENCE_NO_LONGER_VALID")
                reference=old["reference"]
                reused_count+=1
            else:
                target=BLOBS/digest[:2]/digest
                if target.exists():
                    if target.is_symlink() or target.stat().st_size!=size or sha(target)!=digest:
                        raise RuntimeError("EXISTING_OBJECT_COLLISION")
                else:
                    target.parent.mkdir(mode=0o700,exist_ok=True)
                    with tempfile.NamedTemporaryFile(mode="wb",dir=target.parent,
                                                     prefix=".blob-draft-",delete=False) as o:
                        temp=Path(o.name)
                        with p.open("rb") as inp:
                            shutil.copyfileobj(inp,o,1048576)
                    os.chmod(temp,0o600)
                    if temp.stat().st_size!=size or sha(temp)!=digest:
                        raise RuntimeError("NEW_BLOB_SHA_MISMATCH")
                    try:os.link(temp,target)
                    except FileExistsError:
                        if sha(target)!=digest:raise RuntimeError("OBJECT_CONFLICT")
                    finally:temp.unlink(missing_ok=True)
                    copied_count+=1
                    copied_bytes+=size
                reference={"type":"blob"}
            after=p.stat()
            if after.st_size!=size or after.st_mtime_ns!=before.st_mtime_ns or sha(p)!=digest:
                raise RuntimeError("SOURCE_CHANGED_DURING_ENCRYPTED_COPY")
            output.append({"relative_path":rel,"sha256":digest,"size":size,"reference":reference})
        payload={
            "type":"ROUTABL_CIPHERTEXT_CAS_V01","completed":True,
            "created_kst":now(),"local_snapshot_name":local["snapshot_name"],
            "local_receipt_sha256":local["receipt_sha256"],
            "manifest_sha256":local["manifest_sha256"],
            "selection_sha256":local["selection_sha256"],
            "source":"local_closed_aes256_image_content_aware_incremental",
            "anchor_snapshot":prior["anchor_snapshot"],
            "warning_anchor_must_be_retained":True,
            "new_ciphertext_bytes_copied":copied_bytes,
            "new_ciphertext_components":copied_count,
            "reused_ciphertext_components":reused_count,
            "components":len(output),"total_ciphertext_bytes":total,
            "files":output}
        result=verify_manifest(payload,full=True)
        path=write_manifest(payload,local["snapshot_name"])
        print(json.dumps({"result":"INCREMENTAL_SNAPSHOT_VERIFIED",
                          "new_ciphertext_bytes":copied_bytes,
                          "new_components":copied_count,
                          "reused_components":reused_count,
                          "components":result["verified_bands"],
                          "manifest_path":str(path),
                          "do_not_prune_anchor":True},ensure_ascii=False),flush=True)
        return 0
    finally:os.close(fd)

def verify():
    validate_environment()
    history=list_manifests()
    if not history:raise RuntimeError("NO_CAS_MANIFESTS")
    for _,path,payload in history:
        v=verify_manifest(payload,full=True)
        print(json.dumps({"result":"VERIFIED",
                          "snapshot":payload["local_snapshot_name"],
                          "components":v["verified_bands"],
                          "bytes":v["referenced_ciphertext_bytes"],
                          "new_bytes":payload["new_ciphertext_bytes_copied"]},ensure_ascii=False))
    return 0

def check():
    validate_environment()
    history=list_manifests() if MANIFESTS.is_dir() else []
    print(json.dumps({"mode":"READ_ONLY","seeded":len(history)>0,
                      "manifest_count":len(history),
                      "last_snapshot":history[-1][2]["local_snapshot_name"] if history else None,
                      "existing_anchor_read_only":True,
                      "scheduled_agents_modified":False},ensure_ascii=False))
    return 0

if __name__=="__main__":
    cli=argparse.ArgumentParser()
    cli.add_argument("action",choices=("check","seed","capture","verify"))
    opts=cli.parse_args()
    try:sys.exit(globals()[opts.action]())
    except Exception as e:
        print(json.dumps({"result":"FAILED_SAFE","failure_type":type(e).__name__,
                          "original_snapshots_modified":False},ensure_ascii=False),file=sys.stderr)
        sys.exit(2)
