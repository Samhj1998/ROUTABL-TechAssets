#!/usr/bin/env python3
"""ROUTABL 120: non-destructive, phase-labelled background-access diagnostics.

Checks existing files and candidate configuration only. Never registers a launch
agent, mounts AES image, unlocks Keychain, copies data, runs backup or changes TCC.
All error output is category/errno only: no secret/file path disclosure.
"""
from __future__ import annotations
import argparse
import datetime
import errno
import json
import os
import plistlib
import re
import subprocess
import sys
from pathlib import Path
from zoneinfo import ZoneInfo

HOME = Path("/Users/yongho")
ROOT = HOME / "ROUTABL-TechAssets"
LOGS = HOME / "Library/Logs/ROUTABL-AssetBackup"
STUDIO = HOME / "StudioProjects"
SEARCH = HOME / "Library/Application Support/ROUTABL-AssetSearch"
AGENTS = HOME / "Library/LaunchAgents"
DRAFTS = ROOT / "40_WORKING/BACKUP_HEADLESS_V0_3/proposed_launchagents"
NAS = Path("/Volumes/Dev_Assets")
SSD = Path("/Volumes/SSD2TB")
IMAGE = SSD / "ROUTABL-TechAssets-Backup/ROUTABL-SecureBackup.sparsebundle"
BASELINE = NAS / "ROUTABL-TechAssets-Backup/snapshots/ROUTABL-Ciphertext-CAS-v0_1/manifests/CAS_ASSET_V21_20261103_214028_KST_24533.json"
PROBE_VERSION = "0.1"


def read_json(path):
    if path.is_symlink() or not path.is_file():
        raise RuntimeError("SOURCE_MISSING_OR_LINK")
    with path.open("r", encoding="utf8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise RuntimeError("JSON_OBJECT_EXPECTED")
    return data


def latest_registry():
    candidates = []
    for path in (ROOT / "30_REGISTRY").glob("asset_manifest_v0.*.json"):
        m = re.fullmatch(r"asset_manifest_v0\.(\d+)\.json", path.name)
        if m and not path.is_symlink() and path.is_file():
            candidates.append((int(m.group(1)), path))
    if not candidates:
        raise RuntimeError("REGISTRY_MISSING")
    _, file = max(candidates)
    data = read_json(file)
    if data.get("schema_version") != "0." + file.stem.split("v0.")[-1]:
        raise RuntimeError("REGISTRY_SCHEMA_MISMATCH")
    return data


def check_identity():
    if os.geteuid() != 501:
        raise RuntimeError("UNEXPECTED_USER_CONTEXT")
    return {"uid_matches": True}


def check_state_root():
    if LOGS.is_symlink() or not LOGS.is_dir():
        raise RuntimeError("STATE_DIRECTORY_UNAVAILABLE")
    st = LOGS.stat()
    if st.st_uid != os.geteuid():
        raise RuntimeError("STATE_DIRECTORY_OWNER_MISMATCH")
    return {"owner_matches": True, "mode": oct(st.st_mode & 0o777)}


def check_state_receipts():
    local = read_json(LOGS / "last_selective_v21_result.json")
    nas = read_json(LOGS / "last_selective_nas_v21_result.json")
    if local.get("status") != "SUCCESS" or nas.get("status") != "SUCCESS":
        raise RuntimeError("VERIFIED_RECEIPT_STATUS_MISSING")
    return {"local_success_receipt": True, "nas_success_receipt": True}


def check_source_manifest():
    data = latest_registry()
    records = data.get("asset_files", [])
    if len(records) < 61:
        raise RuntimeError("REGISTRY_RECORD_COUNT_TOO_LOW")
    return {"asset_count": len(records), "schema": data.get("schema_version")}


def check_registered_path_metadata():
    data = latest_registry()
    count = 0
    for row in data["asset_files"]:
        path = Path(row["observed_original_path"])
        if path.is_symlink() or not path.is_file():
            raise RuntimeError("REGISTRY_ORIGINAL_MISSING_OR_LINK")
        if path.stat().st_size != row["bytes"]:
            raise RuntimeError("REGISTRY_SIZE_CHANGED")
        count += 1
    return {"metadata_accessible_files": count, "full_contents_not_read": True}


def check_backup_scripts_readable():
    names = ("ROUTABL_HeadlessDailyGate_v0_3.py",
             "ROUTABL_SelectiveSecureBackup_v2_1.py",
             "ROUTABL_SelectiveNasCopy_v2_1.py")
    for name in names:
        p = ROOT / "00_GUIDE" / name
        if p.is_symlink():
            raise RuntimeError("SCRIPT_SYMLINK")
        with p.open("rb") as f:
            if not f.read(8):
                raise RuntimeError("SCRIPT_EMPTY")
    return {"script_count": len(names)}


def check_studio_root():
    if STUDIO.is_symlink() or not STUDIO.is_dir():
        raise RuntimeError("STUDIO_PROJECTS_PATH_UNAVAILABLE")
    # Directory names only. No source execution or content read.
    dirs = sum(1 for p in STUDIO.iterdir() if p.is_dir() and not p.is_symlink())
    if dirs < 8:
        raise RuntimeError("PROJECT_TREE_UNEXPECTED")
    return {"directories_visible": dirs}


def check_external_ssd():
    if not os.path.ismount(SSD) or not IMAGE.is_dir() or IMAGE.is_symlink():
        raise RuntimeError("SSD_OR_LOCKED_IMAGE_UNAVAILABLE")
    return {"ssd_online": True, "aes_image_folder_present": True}


def check_nas_access():
    if not os.path.ismount(NAS):
        raise RuntimeError("NAS_VOLUME_NOT_MOUNTED")
    root = NAS / "ROUTABL-TechAssets-Backup/snapshots"
    if not root.is_dir():
        raise RuntimeError("NAS_SNAPSHOTS_UNAVAILABLE")
    return {"nas_online": True}


def check_nas_reference_metadata():
    rec = read_json(BASELINE)
    if rec.get("components") != 141 or not rec.get("warning_anchor_must_be_retained"):
        raise RuntimeError("CAS_ANCHOR_UNEXPECTED")
    return {"cas_anchor_verified_in_previous_audit": True,
            "reference_count": rec["components"]}


def check_search_storage():
    if SEARCH.is_symlink() or not SEARCH.is_dir():
        raise RuntimeError("SEARCH_STORAGE_UNAVAILABLE")
    p = SEARCH / "assets_v1_5.sqlite"
    if not p.is_file():
        raise RuntimeError("SEARCH_INDEX_MISSING")
    return {"index_present": True}


def check_launchagent_drafts():
    if DRAFTS.is_symlink() or not DRAFTS.is_dir():
        raise RuntimeError("PLIST_DRAFTS_MISSING")
    for job, hour, minute in (("local", 4, 30), ("nas", 5, 15)):
        name = "com.routabl.assetbackup.v21.headless." + job + ".plist"
        path = DRAFTS / name
        if path.is_symlink():
            raise RuntimeError("UNTRUSTED_DRAFT_SYMLINK")
        with path.open("rb") as f:
            p = plistlib.load(f)
        if (p.get("KeepAlive") is not False or
            p.get("RunAtLoad") is not False or
            p.get("ProcessType") != "Background" or
            p.get("StartCalendarInterval") != {"Hour": hour, "Minute": minute} or
            p.get("ThrottleInterval", 0) < 300 or
            p.get("ProgramArguments") != [
                "/usr/bin/python3",
                str(ROOT / "00_GUIDE/ROUTABL_HeadlessDailyGate_v0_3.py"),
                "run", job]):
            raise RuntimeError("UNSAFE_LAUNCHAGENT_DRAFT")
        if (AGENTS / name).exists():
            raise RuntimeError("UNEXPECTED_SCHEDULED_AGENT_INSTALLED")
    return {"safe_uninstalled_candidate_count": 2}


def check_readonly_disk_image_metadata():
    p = subprocess.run(
        ["/usr/sbin/diskutil", "image", "info", str(IMAGE)],
        capture_output=True, text=True, timeout=15, stdin=subprocess.DEVNULL)
    if p.returncode != 0 or "Is Encrypted: 1" not in p.stdout or "Key Size: 256" not in p.stdout:
        raise RuntimeError("READONLY_AES_METADATA_UNAVAILABLE")
    if Path("/Volumes/ROUTABL-Secure").exists():
        raise RuntimeError("ENCRYPTED_IMAGE_IS_MOUNTED")
    return {"aes_256_metadata_verified": True, "image_not_mounted": True}


STAGES = (
    ("user_identity", check_identity),
    ("state_folder", check_state_root),
    ("state_receipts_read", check_state_receipts),
    ("latest_registry_read", check_source_manifest),
    ("registered_asset_metadata", check_registered_path_metadata),
    ("backup_scripts_read", check_backup_scripts_readable),
    ("studio_projects_directory", check_studio_root),
    ("ssd_mount_and_image", check_external_ssd),
    ("nas_mount_access", check_nas_access),
    ("nas_cas_anchor_read", check_nas_reference_metadata),
    ("search_index_metadata", check_search_storage),
    ("candidate_plist_static_validation", check_launchagent_drafts),
    ("image_encryption_metadata_only", check_readonly_disk_image_metadata),
)


def run(mode, simulated_stage=None):
    result = {
        "version": PROBE_VERSION,
        "observed_at_kst": datetime.datetime.now(ZoneInfo("Asia/Seoul")).isoformat(timespec="seconds"),
        "mode": mode, "permission_denial_simulated": simulated_stage is not None,
        "launchctl_called": False, "backup_run": False,
        "image_mounted": False, "keychain_queried": False,
        "macos_security_permissions_changed": False,
        "phase_results": [], "overall": "UNVERIFIED_BACKGROUND_CONTEXT",
    }
    for stage, probe in STAGES:
        try:
            if simulated_stage == stage:
                raise PermissionError(errno.EACCES, "synthetic")
            detail = probe()
            result["phase_results"].append({"stage": stage, "result": "PASS", "detail": detail})
        except (PermissionError, OSError, ValueError, RuntimeError, subprocess.TimeoutExpired) as err:
            # Fail on the FIRST error, output its phase and errno only.
            # No file paths, error strings, private contents, passwords or tokens.
            result["phase_results"].append({
                "stage": stage, "result": "FAIL_CLOSED",
                "exception": type(err).__name__,
                "errno": getattr(err, "errno", None),
            })
            result["overall"] = "BLOCKED_AT_FIRST_FAILURE"
            print(json.dumps(result, ensure_ascii=False, indent=2), flush=True)
            return 21
    result["overall"] = (
        "SYNTHETIC_DENIAL_NOT_TRIGGERED" if simulated_stage is not None else
        "MANUAL_CONTEXT_ACCESS_OK__LAUNCHD_TCC_NOT_PROVEN"
    )
    print(json.dumps(result, ensure_ascii=False, indent=2), flush=True)
    return 0 if simulated_stage is None else 22


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=("check", "simulate-denial"))
    parser.add_argument("--stage", choices=[v[0] for v in STAGES], default="studio_projects_directory")
    args = parser.parse_args()
    sys.exit(run(args.action, args.stage if args.action == "simulate-denial" else None))
