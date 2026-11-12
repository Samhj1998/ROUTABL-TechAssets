#!/usr/bin/env python3
"""ROUTABL technical asset backup health check. Read-only, no credentials."""
import datetime
import hashlib
import json
import os
from pathlib import Path
from zoneinfo import ZoneInfo

HOME=Path("/Users/yongho")
ROOT=HOME/"ROUTABL-TechAssets"
LOG=HOME/"Library/Logs/ROUTABL-AssetBackup"
SSD=Path("/Volumes/SSD2TB")
NAS=Path("/Volumes/Dev_Assets")
CAS=NAS/"ROUTABL-TechAssets-Backup/snapshots/ROUTABL-Ciphertext-CAS-v0_1/manifests"
POLICY=HOME/"Library/Application Support/ROUTABL-AssetBackup/approval_v01.json"
MIN_FREE=5*(1024**3)

def load(p):
    if p.is_symlink() or not p.is_file():raise ValueError("MISSING_EVIDENCE")
    obj=json.loads(p.read_text("utf8"))
    if not isinstance(obj,dict):raise ValueError("INVALID_EVIDENCE")
    return obj

def sha(p):
    d=hashlib.sha256()
    with p.open("rb") as f:
        for c in iter(lambda:f.read(1048576),b""):d.update(c)
    return d.hexdigest()

def current_registry():
    candidates=[]
    for p in (ROOT/"30_REGISTRY").glob("asset_manifest_v0.*.json"):
        try:candidates.append((int(p.stem.split("v0.")[1]),p))
        except (ValueError,IndexError):pass
    if not candidates:raise ValueError("MISSING_REGISTRY")
    return max(candidates)[1]

def status():
    issues=[]
    report={
        "kind":"ROUTABL_BACKUP_HEALTH_READONLY_V01",
        "at_kst":datetime.datetime.now(ZoneInfo("Asia/Seoul")).isoformat(timespec="seconds"),
        "backup_executed":False,
        "drive_used":False,
        "launch_agent_modified":False,
        "permission_changed":False,
        "issues":issues
    }
    for label,path in (("ssd",SSD),("nas",NAS)):
        mounted=os.path.ismount(path)
        report[label+"_mounted"]=mounted
        if not mounted:
            issues.append(label.upper()+"_UNMOUNTED")
        else:
            st=os.statvfs(path)
            remaining=st.f_bavail*st.f_frsize
            report[label+"_free_gib"]=round(remaining/1024**3,2)
            if remaining<MIN_FREE:issues.append(label.upper()+"_LOW_FREE_SPACE")
    report["backup_image_in_use"]=Path("/Volumes/ROUTABL-Secure").exists()
    if report["backup_image_in_use"]:
        issues.append("RESTORE_IMAGE_MOUNTED_BACKUP_MUST_NOT_START")
    report["automatic_backup_approval_present"]=POLICY.is_file()
    if POLICY.is_file():issues.append("AUTOMATIC_POLICY_PRESENT_REQUIRES_MANUAL_REVIEW")
    try:
        reg=current_registry()
        j=load(reg)
        report["registry"]=reg.name
        report["registry_assets"]=len(j.get("asset_files",[]))
        report["registry_sha256"]=sha(reg)
        local=load(LOG/"last_selective_v21_result.json")
        one=load(LOG/"last_manual_mac_nas_cas_v01.json")
        report["latest_verified_snapshot"]=one.get("local_snapshot")
        report["latest_verified_files"]=local.get("file_count")
        report["last_snapshot_at_kst"]=local.get("created_at_kst")
        valid=(local.get("status")=="SUCCESS" and one.get("status")=="SUCCESS_LOCAL_TO_NAS_ENCRYPTED_CAS"
               and local.get("snapshot_name")==one.get("local_snapshot")
               and local.get("receipt_sha256")==one.get("local_receipt_sha256")
               and one.get("manifest_sha256")==local.get("manifest_sha256"))
        if valid and NAS.is_dir():
            path=CAS/("CAS_"+str(one["local_snapshot"])+".json")
            jcas=load(path)
            valid=(jcas.get("local_snapshot_name")==one["local_snapshot"]
                   and jcas.get("local_receipt_sha256")==local.get("receipt_sha256"))
        report["last_receipts_and_nas_index_linked"]=valid
        if not valid:issues.append("LAST_VERIFIED_BACKUP_CHAIN_UNAVAILABLE")
        report["latest_registry_in_last_verified_backup"]=(local.get("manifest_sha256")==report["registry_sha256"])
        if not report["latest_registry_in_last_verified_backup"]:
            issues.append("LATEST_REGISTRY_ADDED_AFTER_LAST_BACKUP")
        when=datetime.datetime.fromisoformat(local["created_at_kst"])
        age=(datetime.datetime.now(ZoneInfo("Asia/Seoul"))-when).total_seconds()/3600
        report["last_backup_age_hours"]=round(age,2)
        if age>48:issues.append("LAST_BACKUP_OLDER_THAN_48H")
    except (OSError,KeyError,TypeError,ValueError,IndexError) as e:
        issues.append("BACKUP_RECEIPT_OR_REGISTRY_INVALID")
        report["evidence_error_class"]=type(e).__name__
    report["result"]="HEALTHY_EVIDENCE" if not issues else "REVIEW_REQUIRED"
    return report

if __name__=="__main__":
    print(json.dumps(status(),ensure_ascii=False,indent=2))
