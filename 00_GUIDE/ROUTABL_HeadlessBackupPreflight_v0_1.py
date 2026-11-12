#!/usr/bin/env python3
"""120 ROUTABL: read-only backup safety preflight and synthetic headless test.

Never executes real backup, mounts images, unlocks Keychain, changes launchd,
copies sensitive data or writes to NAS/Google Drive. Reports metadata only.
"""
import argparse
import datetime
import fcntl
import json
import os
import re
import plistlib
import subprocess
import sys
import tempfile
from pathlib import Path
from zoneinfo import ZoneInfo

HOME = Path("/Users/yongho")
ROOT = HOME / "ROUTABL-TechAssets"
EXISTING = ROOT / "00_GUIDE"
STAGE = ROOT / "40_WORKING/BACKUP_HEADLESS_V0_1/proposed_launchagents"
STATE = HOME / "Library/Logs/ROUTABL-AssetBackup"
IMAGE = Path("/Volumes/SSD2TB/ROUTABL-TechAssets-Backup/ROUTABL-SecureBackup.sparsebundle")
ENCRYPTED_VOLUME = Path("/Volumes/ROUTABL-Secure")
NAS = Path("/Volumes/Dev_Assets")
SSD = Path("/Volumes/SSD2TB")
INCLUDED = ("00_GUIDE", "20_ORIGINALS", "30_REGISTRY",
            "50_VERIFIED", "60_AUDIT", "70_EXPORTS")
EXCLUDED = ("10_INBOX", "40_WORKING")
EXPECTED = {
    "local": ("com.routabl.assetbackup.headless.local",
              "ROUTABL_ScheduledBackup_v1_0.py", 4, 30),
    "nas": ("com.routabl.assetbackup.headless.nas",
            "ROUTABL_NASReplication_v1_0.py", 5, 15),
}

def read_state(file):
    p = STATE / file
    if not p.is_file():
        return {"exists": False}
    try:
        record = json.loads(p.read_text(encoding="utf-8"))
        keys = ("status", "day_kst", "checked_at_kst", "file_count",
                "cloud_confirmed", "locked_after_backup", "image_mounted")
        return {key: record[key] for key in keys if key in record}
    except (ValueError, UnicodeError, OSError):
        return {"exists": True, "parse_error": True}

def count_files(directory):
    if not directory.is_dir() or directory.is_symlink():
        return None
    return sum(1 for p in directory.rglob("*") if p.is_file() and not p.is_symlink())

def validate_candidate(name):
    label, script, hour, minute = EXPECTED[name]
    path = STAGE / (label + ".plist")
    if not path.is_file() or path.is_symlink():
        raise RuntimeError("CANDIDATE_UNAVAILABLE_" + name)
    with path.open("rb") as f:
        p = plistlib.load(f)
    if p.get("Label") != label:
        raise RuntimeError("WRONG_LABEL_" + name)
    if p.get("ProgramArguments") != ["/usr/bin/python3", str(EXISTING / script)]:
        raise RuntimeError("GUI_OR_WRONG_COMMAND_" + name)
    if p.get("KeepAlive", False) is not False or p.get("RunAtLoad", False) is not False:
        raise RuntimeError("UNSAFE_AUTO_RESTART_" + name)
    if p.get("StartCalendarInterval") != {"Hour": hour, "Minute": minute}:
        raise RuntimeError("WRONG_SCHEDULE_" + name)
    if p.get("ProcessType") != "Background":
        raise RuntimeError("WRONG_PROCESS_TYPE_" + name)
    if p.get("ThrottleInterval", 0) < 300:
        raise RuntimeError("UNSAFE_RESTART_THROTTLE_" + name)
    if any(word in " ".join(p["ProgramArguments"]).lower()
           for word in ("terminal", ".command", "osascript", "open -a")):
        raise RuntimeError("GUI_INVOCATION_REJECTED_" + name)
    if (HOME / "Library/LaunchAgents" / path.name).exists():
        raise RuntimeError("CANDIDATE_ALREADY_INSTALLED_" + name)
    return {
        "file": str(path), "candidate_valid": True,
        "scheduled": "%02d:%02d KST" % (hour, minute),
        "installed": False, "disabled_prior_jobs_untouched": True,
    }

def asset_coverage():
    registry = ROOT / "30_REGISTRY"
    choices = []
    for p in registry.glob("asset_manifest_v0.*.json"):
        m = re.fullmatch(r"asset_manifest_v0\.(\d+)\.json", p.name)
        if m and not p.is_symlink():
            choices.append((int(m.group(1)), p))
    if not choices:
        raise RuntimeError("ASSET_REGISTER_MISSING")
    number, manifest = max(choices, key=lambda row: row[0])
    data = json.loads(manifest.read_text(encoding="utf-8"))
    entries = data.get("asset_files", [])
    if data.get("schema_version") != "0." + str(number) or len(entries) < 33:
        raise RuntimeError("ASSET_REGISTER_UNEXPECTED")
    forbidden = re.compile(r"(^\\.env($|\\.)|adminsdk|credential|private.?key|secret|token|\\.pem$|\\.p12$|\\.key$)", re.I)
    in_scope = 0
    for row in entries:
        p = Path(row["observed_original_path"])
        try:
            rel = p.relative_to(ROOT)
        except ValueError:
            continue
        if (rel.parts and rel.parts[0] in INCLUDED and p.is_file()
                and not p.is_symlink() and not p.name.startswith(".")
                and not forbidden.search(p.name) and p.stat().st_size <= 100_000_000):
            in_scope += 1
    return {"manifest": manifest.name, "manifest_assets": len(entries),
            "eligible_for_current_backup_scope": in_scope,
            "outside_or_excluded": len(entries) - in_scope,
            "not_a_snapshot_integrity_proof": True}

def check():
    now = datetime.datetime.now(ZoneInfo("Asia/Seoul")).isoformat(timespec="seconds")
    result = {
        "timestamp_kst": now,
        "mode": "READ_ONLY",
        "result": "STAGED_ONLY_DO_NOT_ENABLE",
        "user_id": os.getuid(),
        "mounts": {
            "SSD2TB": os.path.ismount(SSD),
            "Dev_Assets_NAS": os.path.ismount(NAS),
            "encrypted_image_present": IMAGE.is_dir() and not IMAGE.is_symlink(),
            "encrypted_image_closed": not ENCRYPTED_VOLUME.exists(),
        },
        "source_scope": {
            "included": {name: count_files(ROOT / name) for name in INCLUDED},
            "excluded": {name: count_files(ROOT / name) for name in EXCLUDED},
            "search_engine_outside_source_scope": True,
            "studio_projects_outside_source_scope": True,
        },
        "historical_receipts": {
            "local": read_state("last_result.json"),
            "nas": read_state("last_nas_result.json"),
            "drive": read_state("last_drive_result.json"),
        },
        "candidate_launchagents": {n: validate_candidate(n) for n in EXPECTED},
        "registry_coverage": asset_coverage(),
        "limitations": [
            "No backup or restore was performed.",
            "The last historical SUCCESS receipts do not verify current v0.7 assets.",
            "Direct launchd Python access to external volumes and Keychain TCC has not been tested.",
            "Stage files are not installed or enabled.",
            "Google Drive background upload is deferred pending proof of remote integrity.",
        ],
    }
    if result["user_id"] == 0:
        result["result"] = "ROOT_DISALLOWED"
    if not all(result["mounts"].values()):
        result["result"] = "NOT_READY_STORAGE_OR_ENCRYPTED_IMAGE"
    if result["registry_coverage"]["outside_or_excluded"]:
        result["result"] = "HOLD_INCOMPLETE_ASSET_COVERAGE"
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["result"] == "STAGED_ONLY_DO_NOT_ENABLE" else 2

def simulate():
    # Files are created only under an ephemeral temporary directory; no source,
    # Google Drive, launchctl, encryption image or production backup script access.
    check_files = [validate_candidate(n) for n in EXPECTED]
    with tempfile.TemporaryDirectory(prefix="routabl_headless_fake_") as td:
        lock_path = Path(td) / "fake.lock"
        script = Path(td) / "fake-worker.py"
        script.write_text(
            "import fcntl,os,sys\n"
            "with open(sys.argv[1],'a+') as f:\n"
            " try:fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB)\n"
            " except BlockingIOError:raise SystemExit(13)\n"
            " os.write(1,b'SYNTHETIC_CHILD_EXECUTED\\n')\n", encoding="utf-8")
        result = subprocess.run(
            ["/usr/bin/python3", str(script), str(lock_path)],
            capture_output=True, text=True, timeout=8)
        if result.returncode != 0 or result.stdout.strip() != "SYNTHETIC_CHILD_EXECUTED":
            raise RuntimeError("HEADLESS_SYNTHETIC_SUBPROCESS_FAILED")
        with lock_path.open("a+") as f:
            fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
            duplicate = subprocess.run(
                ["/usr/bin/python3", str(script), str(lock_path)],
                capture_output=True, text=True, timeout=8)
            if duplicate.returncode != 13:
                raise RuntimeError("HEADLESS_LOCK_DUPLICATE_NOT_BLOCKED")
        print(json.dumps({
            "mode": "SYNTHETIC_TEST", "status": "SUCCESS",
            "candidate_plists_valid": len(check_files),
            "gui_terminal_opened": False,
            "synthetic_subprocess": True,
            "duplicate_process_rejected": True,
            "real_backup_executed": False,
            "launchd_enabled": False,
            "external_data_copied": False,
        }, ensure_ascii=False))
    return 0

if __name__ == "__main__":
    cli = argparse.ArgumentParser()
    cli.add_argument("mode", choices=("check", "simulate"))
    args = cli.parse_args()
    try:
        raise SystemExit(check() if args.mode == "check" else simulate())
    except Exception as ex:
        print(json.dumps({"status": "FAILED_SAFE",
                          "reason": type(ex).__name__ + ":" + str(ex)[:120]},
                         ensure_ascii=False), file=sys.stderr)
        raise SystemExit(3)
