#!/usr/bin/env python3
"""Prepare manual-only approval after actual TCC and unattended probe validation.

This tool is NOT used by LaunchAgent; never invokes backup or changes TCC.
The 'review' mode is read-only. The 'approve' mode is interactive and must be
run by the account owner ONLY after signed app / background permission test.
"""
import argparse
import hashlib
import json
import os
import plistlib
import subprocess
import sys
from pathlib import Path

HOME=Path("/Users/yongho")
ROOT=HOME/"ROUTABL-TechAssets"
GUIDE=ROOT/"00_GUIDE"
APP=HOME/"Applications/라우터블 백업 권한·안전관리 v0.3.app"
PLIST=APP/"Contents/Library/LaunchAgents/com.routabl.assetbackup.native.safe.plist"
INFO=APP/"Contents/Info.plist"
APPROVAL=HOME/"Library/Application Support/ROUTABL-AssetBackup/approval_v01.json"
FILES={
    "runner_sha256":GUIDE/"ROUTABL_MacToNasOneShot_v0_1.py",
    "nas_engine_sha256":GUIDE/"ROUTABL_NAS_ContentAwareBackup_v0_2.py",
    "local_gate_sha256":GUIDE/"ROUTABL_HeadlessDailyGate_v0_3.py"
}
EXPECTED_UID=501

def sha(path):
    h=hashlib.sha256()
    with path.open("rb") as fp:
        for piece in iter(lambda:fp.read(1048576),b""):
            h.update(piece)
    return h.hexdigest()

def plan():
    if os.geteuid()!=EXPECTED_UID:
        raise RuntimeError("OWNER_UID_REQUIRED")
    if not APP.is_dir() or APP.is_symlink():
        raise RuntimeError("FINAL_APP_MISSING")
    if not PLIST.is_file() or not INFO.is_file():
        raise RuntimeError("BUNDLE_METADATA_UNAVAILABLE")
    plist=plistlib.loads(PLIST.read_bytes())
    info=plistlib.loads(INFO.read_bytes())
    if not (plist["StartCalendarInterval"]=={"Hour":4,"Minute":30}
            and plist["KeepAlive"] is False and plist["RunAtLoad"] is False
            and info["CFBundleIdentifier"]=="com.routabl.assetbackup.manager.safe"
            and all(info.get(k) for k in
                    ("NSNetworkVolumesUsageDescription","NSRemovableVolumesUsageDescription"))):
        raise RuntimeError("BUNDLE_SECURITY_POLICY_MISMATCH")
    verify=subprocess.run(["/usr/bin/codesign","--verify","--deep","--strict",str(APP)],
                          capture_output=True,timeout=20)
    if verify.returncode!=0:
        raise RuntimeError("UNSIGNED_OR_CHANGED_BUNDLE")
    signatures={}
    for k,path in FILES.items():
        if not path.is_file() or path.is_symlink():
            raise RuntimeError("PROGRAM_MISSING")
        signatures[k]=sha(path)
    ready={
        "status":"REVIEW_ONLY_NOT_AUTHORIZATION",
        "approval_already_present":APPROVAL.is_file(),
        "bundle_signature_valid":True,
        "bundle_id":info["CFBundleIdentifier"],
        "run_local_time":"04:30 Asia/Seoul",
        "google_drive_upload":False,
        "automatic_nas_pruning":False,
        "permissions_confirmed":False,
        "background_agent_execution_confirmed":False,
        "developer_id_signature_present":False,
        "signed_program_hashes_computed":True,
    }
    payload={"approval_version":1,"owner_uid":EXPECTED_UID,"enabled":True,
             "scope":"MAC_SSD_AES256_TO_NAS_CAS_ONLY",
             "scheduled_hour_kst":4,"scheduled_minute_kst":30,
             "drive_upload":False,"allow_pruning":False}
    payload.update(signatures)
    return ready,payload

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("mode",choices=("review","approve"))
    args=ap.parse_args()
    meta,payload=plan()
    if args.mode=="review":
        print(json.dumps(meta,ensure_ascii=False,indent=2))
        return 0
    if not sys.stdin.isatty():
        raise RuntimeError("INTERACTIVE_TERMINAL_REQUIRED")
    if meta["approval_already_present"] or APPROVAL.exists() or APPROVAL.is_symlink():
        raise RuntimeError("REFUSE_EXISTING_APPROVAL")
    print("주의: 이후 04:30에 Mac→AES SSD→NAS 자동 백업이 활성화됩니다.")
    print("macOS 앱 권한·무인 진단·재부팅 후 NAS 연결이 검증되었을 때만 승인하세요.")
    print("승인하지 않으면 Enter만 누르거나 종료하세요.")
    answer=input("동의 시 'ROUTABL ENABLE BACKUP' 입력: ")
    if answer!="ROUTABL ENABLE BACKUP":
        print("APPROVAL_NOT_CREATED")
        return 0
    parent=APPROVAL.parent
    if parent.exists() and (not parent.is_dir() or parent.is_symlink()):
        raise RuntimeError("APPROVAL_DIRECTORY_UNSAFE")
    parent.mkdir(parents=True,exist_ok=True,mode=0o700)
    old=os.umask(0o077)
    try:
        fd=os.open(APPROVAL,os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600)
        with os.fdopen(fd,"w",encoding="utf8") as stream:
            json.dump(payload,stream,ensure_ascii=False,indent=2)
            stream.write("\n")
    finally:
        os.umask(old)
    print("APPROVAL_CREATED_BY_INTERACTIVE_OWNER_NO_BACKUP_EXECUTED")
    return 0

if __name__=="__main__":
    try:sys.exit(main())
    except Exception as ex:
        print(json.dumps({"status":"NO_APPROVAL_GRANTED","class":type(ex).__name__},
                         ensure_ascii=False),file=sys.stderr)
        sys.exit(2)
