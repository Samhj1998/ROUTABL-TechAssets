#!/usr/bin/env python3
"""ROUTABL technical-asset selective AES snapshot v2.1.

Manual one-off command, not launchd. Reads a fixed v0.8 registry and eight allowlisted
Mac project trees; no network, no source modification, no credentials, no pruning.
A new snapshot is appended to an existing locked AES-256 disk image.
"""
from __future__ import annotations
import argparse
import collections
import datetime
import fcntl
import hashlib
import json
import os
import plistlib
import re
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path
from zoneinfo import ZoneInfo

HOME = Path(os.environ.get("ROUTABL_HOME", "/Users/yongho"))   # v2.2: 시험용 덮어쓰기 (Mac에서는 기본값)
ENGINE = "SelectiveSecureBackup v2.2 (2026-11-12 draft)"
_PATH_MAP = os.environ.get("ROUTABL_PATH_MAP", "")              # 시험용 "원래접두=>실제접두"

def local_path(p):
    p = str(p)
    if "=>" in _PATH_MAP:
        a, b = _PATH_MAP.split("=>", 1)
        if p.startswith(a):
            p = b + p[len(a):]
    return Path(p)
ROOT = HOME / "ROUTABL-TechAssets"
STUDIO = HOME / "StudioProjects"
def latest_registry():
    # v2.2: 기준 등록부 하나(asset_manifest.json, P2 2026-11-12)를 우선. 없으면 가장 높은 v0.N
    canonical = ROOT / "30_REGISTRY" / "asset_manifest.json"
    if canonical.is_file() and not canonical.is_symlink():
        return canonical
    choices=[]
    for p in (ROOT / "30_REGISTRY").glob("asset_manifest_v0.*.json"):
        match=re.fullmatch(r"asset_manifest_v0\.(\d+)\.json",p.name)
        if match and not p.is_symlink() and p.is_file():
            choices.append((int(match.group(1)),p))
    if not choices:
        raise RuntimeError("REGISTRY_NOT_FOUND")
    return max(choices)[1]

REGISTRY = latest_registry()
IMAGE = Path("/Volumes/SSD2TB/ROUTABL-TechAssets-Backup/ROUTABL-SecureBackup.sparsebundle")
VOLUME = Path("/Volumes/ROUTABL-Secure")
STATE = HOME / "Library/Logs/ROUTABL-AssetBackup"
LOCK = STATE / "selective_v21.lock"
STATUS = STATE / "last_selective_v21_result.json"
PROJECTS = (   # v2.2: 2026-11-11 정리로 사라진 옛 프로젝트 4개 제외, 현재 주요 앱 6개
    "DISPATCH-One-Android", "ROUTABL-Senior-Driver", "DailyInspection-Android",
    "ROUTIVEL-Firebase-Migration", "ROUTABL-Analytics-Android",
    "ROUTABL-CustomerRegistration-Android",
)
SKIP_DIRS = {
    ".git", ".gradle", ".idea", ".kotlin", "build", "node_modules", "dist",
    "target", ".venv", "venv", "__pycache__", ".next", ".expo",
    "coverage", "out", "vendor", "generated", ".cache", "logs", "Pods",
}
TEXT_EXT = {".kt", ".java", ".py", ".js", ".jsx", ".ts", ".tsx", ".swift",
            ".dart", ".md", ".txt", ".html", ".css", ".sql", ".sh",
            ".xml", ".yaml", ".yml", ".json", ".gradle", ".kts", ".properties"}
META_EXT = {".plist", ".command", ".zip", ".pdf", ".sqlite"}
ALLOW_EXT = TEXT_EXT | META_EXT
SKIP_NAME = re.compile(
    r"(^|[._/-])(adminsdk|service.?account|credential|secret|secrets|token|"
    r"password|passwd|private.?key|keystore|id_rsa|google-services|oauth|"
    r"certificate|certificates|\.env|\.pem|\.p12|\.key)([._/-]|$)", re.I)
KEY_MATERIAL = re.compile(
    r"-----BEGIN [^-\\n]*PRIVATE KEY-----|"
    r"(?:AIza[\w-]{20,}|ya29\.[\w-]{12,}|sk-(?:proj-)?[\w-]{18,}|"
    r"gh[pousr]_[A-Za-z0-9_]{20,}|github_pat_[A-Za-z0-9_]{20,}|"
    r"AKIA[A-Z0-9]{16}|xox[baprs]-[\w-]{16,})|"
    r"(?:client_secret|private_key|api[_-]?key|access[_-]?token|auth[_-]?token)"
    r"\s*[:=]\s*[\"'][^\"'\n]{12,}[\"']", re.I)
CUSTOMER = re.compile(r"(?<!\d)01[0-9]-?\d{3,4}-?\d{4}(?!\d)|\b\d{6}-[1-8]\d{6}\b")
LIMIT_TOTAL = 1_100_000_000
LIMIT_PER = 105_000_000
SKIP_CONTENT_AFTER = 3_000_000


def now():
    return datetime.datetime.now(ZoneInfo("Asia/Seoul"))

def digest(path):
    h = hashlib.sha256()
    with path.open("rb") as inp:
        for part in iter(lambda: inp.read(1024 * 1024), b""):
            h.update(part)
    return h.hexdigest()

def selection_digest(entries):
    h = hashlib.sha256()
    for src,target,expected,size,category in sorted(entries,key=lambda row:row[1]):
        h.update(json.dumps([target,expected,size,category],ensure_ascii=False,
                            separators=(",",":")).encode("utf-8"))
        h.update(b"\n")
    return h.hexdigest()

def safe_source_file(p, counters):
    if not p.is_file() or p.is_symlink():
        counters["missing_or_symlink"] += 1
        return False
    if any(SKIP_NAME.search(x) for x in p.parts):
        counters["secret_named_path"] += 1
        return False
    stat = p.stat()
    if stat.st_size > LIMIT_PER:
        counters["over_single_file_limit"] += 1
        return False
    if p.suffix.lower() in TEXT_EXT and stat.st_size <= SKIP_CONTENT_AFTER:
        try:
            text = p.read_text(encoding="utf-8-sig")
            if KEY_MATERIAL.search(text):
                counters["candidate_secret_value"] += 1
                return False
            # Customer lists belong to the production database and not the
            # technical asset backup. Skip source docs containing direct identifiers.
            if CUSTOMER.search(text):
                counters["direct_customer_identifier"] += 1
                return False
        except (UnicodeError, OSError):
            counters["not_plain_utf8"] += 1
            return False
    elif p.suffix.lower() == ".zip":
        try:
            with zipfile.ZipFile(p) as archive:
                for member in archive.infolist():
                    if SKIP_NAME.search(member.filename) or member.file_size > LIMIT_PER:
                        counters["zip_contains_sensitive_or_oversized_member"] += 1
                        return False
                if archive.testzip() is not None:
                    counters["zip_integrity_failure"] += 1
                    return False
        except (zipfile.BadZipFile, OSError):
            counters["zip_integrity_failure"] += 1
            return False
    elif p.suffix.lower() == ".sqlite":
        try:
            with sqlite3.connect("file:" + str(p) + "?mode=ro", uri=True, timeout=5) as db:
                if db.execute("PRAGMA quick_check").fetchone()[0] != "ok":
                    counters["sqlite_integrity_failure"] += 1
                    return False
        except sqlite3.Error:
            counters["sqlite_integrity_failure"] += 1
            return False
    return True

REGISTRY_REPORT = {}

def inventory():
    if REGISTRY.is_symlink() or not REGISTRY.is_file():
        raise RuntimeError("LATEST_REGISTRY_UNAVAILABLE")
    record = json.loads(REGISTRY.read_text(encoding="utf-8"))
    expected = None if REGISTRY.name == "asset_manifest.json" else "0." + REGISTRY.stem.split("v0.")[-1]
    if (expected and record.get("schema_version") != expected) or not str(record.get("schema_version", "")).startswith("0.") \
            or len(record.get("asset_files", [])) < 40:
        raise RuntimeError("LATEST_REGISTRY_MISMATCH")
    entries = []
    rejected = collections.Counter()
    seen_originals = set()
    registered = 0
    # v2.2: 등록부는 살아 있는 파일을 가리킨다. 바뀌었거나 사라진 자산 때문에 백업 전체를 멈추지 않고
    #       지금 파일을 백업하며 차이는 ID로만 기록한다 (경로는 기록하지 않음)
    REGISTRY_REPORT.update(drift=[], missing=[], rejected=[], same_path_superseded=0)
    for item in record["asset_files"]:
        src = local_path(item["observed_original_path"])
        if not src.exists():
            REGISTRY_REPORT["missing"].append(item["asset_id"])
            continue
        if str(src.resolve()) in seen_originals:
            REGISTRY_REPORT["same_path_superseded"] += 1
            continue
        if not safe_source_file(src, rejected):
            rejected["registry_asset_rejected"] += 1
            REGISTRY_REPORT["rejected"].append(item["asset_id"])
            continue
        size, sha = src.stat().st_size, digest(src)
        if size != item["bytes"] or sha != item["sha256"]:
            REGISTRY_REPORT["drift"].append(item["asset_id"])
        target = "registered_assets/" + item["asset_id"] + "/" + src.name
        entries.append((src, target, sha, size, "registry"))
        seen_originals.add(str(src.resolve()))
        registered += 1
    if registered < 40:
        raise RuntimeError("TOO_FEW_REGISTERED_ASSETS_AVAILABLE")
    for project in PROJECTS:
        root = STUDIO / project
        if root.is_symlink() or not root.is_dir():
            raise RuntimeError("PROJECT_MISSING_OR_SYMLINK")
        for folder, directories, names in os.walk(root, followlinks=False):
            directories[:] = sorted(
                x for x in directories
                if x not in SKIP_DIRS and not x.startswith(".") and
                not (Path(folder) / x).is_symlink())
            for name in sorted(names):
                p = Path(folder) / name
                if p.suffix.lower() not in TEXT_EXT or name.startswith("."):
                    rejected["non_technical_extension"] += 1
                    continue
                if str(p.resolve()) in seen_originals:
                    rejected["already_in_registry"] += 1
                    continue
                if not safe_source_file(p, rejected):
                    continue
                rel = p.relative_to(root)
                target = "project_sources/" + project + "/" + rel.as_posix()
                entries.append((p, target, digest(p), p.stat().st_size, "project"))
                seen_originals.add(str(p.resolve()))
    # Preserve the newest registry and the new manual backup script, plus
    # policy/audit notes omitted from the selected current asset register.
    for folder_name in ("00_GUIDE", "20_ORIGINALS", "30_REGISTRY", "60_AUDIT", "70_EXPORTS"):
        root = ROOT / folder_name
        if not root.is_dir() or root.is_symlink():
            raise RuntimeError("MANAGED_SOURCE_MISSING")
        for folder, dirs, filenames in os.walk(root, followlinks=False):
            dirs[:] = sorted(x for x in dirs if not x.startswith(".") and
                             not (Path(folder) / x).is_symlink())
            for filename in sorted(filenames):
                p = Path(folder) / filename
                if p.suffix.lower() not in ALLOW_EXT or filename.startswith("."):
                    rejected["other_managed_extension"] += 1
                    continue
                if str(p.resolve()) in seen_originals:
                    continue
                if not safe_source_file(p, rejected):
                    continue
                target = "managed_records/" + p.relative_to(ROOT).as_posix()
                entries.append((p, target, digest(p), p.stat().st_size, "managed"))
                seen_originals.add(str(p.resolve()))
    target_paths = [x[1] for x in entries]
    if len(target_paths) != len(set(target_paths)):
        raise RuntimeError("DUPLICATE_DESTINATION_PATH")
    size = sum(x[3] for x in entries)
    if size > LIMIT_TOTAL:
        raise RuntimeError("DATA_SIZE_LIMIT_EXCEEDED")
    return entries, rejected, size


def preflight_image():
    if os.geteuid() == 0:
        raise RuntimeError("ROOT_EXECUTION_FORBIDDEN")
    if not os.path.ismount("/Volumes/SSD2TB"):
        raise RuntimeError("EXTERNAL_SSD_NOT_MOUNTED")
    if not IMAGE.is_dir() or IMAGE.is_symlink() or VOLUME.exists():
        raise RuntimeError("ENCRYPTED_IMAGE_UNAVAILABLE_OR_ALREADY_MOUNTED")
    disk = subprocess.run(
        ["/usr/sbin/diskutil", "image", "info", str(IMAGE)],
        capture_output=True, text=True, timeout=20)
    if disk.returncode != 0 or "Is Encrypted: 1" not in disk.stdout or "Key Size: 256" not in disk.stdout:
        raise RuntimeError("AES256_ENCRYPTION_NOT_VERIFIED")
    mounts = subprocess.run(
        ["/usr/bin/hdiutil", "info"], capture_output=True, text=True, timeout=15)
    if mounts.returncode or str(IMAGE) in mounts.stdout:
        raise RuntimeError("IMAGE_ALREADY_ATTACHED")
    if not STATE.is_dir() or STATE.is_symlink() or STATE.stat().st_uid != os.getuid():
        raise RuntimeError("UNSAFE_STATE_DIRECTORY")


def result_summary(entries, rejected, nbytes):
    return {
        "registry_assets_approved": sum(x[4] == "registry" for x in entries),
        "manifest_name": REGISTRY.name,
        "manifest_sha256": digest(REGISTRY),
        "selection_sha256": selection_digest(entries),
        "project_source_files": sum(x[4] == "project" for x in entries),
        "managed_extra_files": sum(x[4] == "managed" for x in entries),
        "total_files": len(entries),
        "total_source_bytes": nbytes,
        "rejection_counts_no_sensitive_paths": dict(rejected),
        "image": "EXISTING_AES256_SPARSEBUNDLE",
        "engine": ENGINE,
        "registry_drift_asset_ids": REGISTRY_REPORT.get("drift", []),
        "registry_missing_asset_ids": REGISTRY_REPORT.get("missing", []),
        "registry_rejected_asset_ids": REGISTRY_REPORT.get("rejected", []),
        "registry_same_path_superseded": REGISTRY_REPORT.get("same_path_superseded", 0),
        "source_code_executed": False,
        "archive_contains_credentials_by_known_patterns": False,
        "secret_detection_is_not_complete_guarantee": True,
    }

def mount():
    attached = subprocess.run([
        "/usr/bin/hdiutil", "attach", "-quiet", "-nobrowse", "-noautoopen", str(IMAGE)],
        capture_output=True, text=True, timeout=25)
    if attached.returncode or not VOLUME.is_dir():
        raise RuntimeError("KEYCHAIN_OR_DISK_IMAGE_MOUNT_FAILED")
    check = subprocess.run(["/usr/bin/hdiutil", "info"],
                           capture_output=True, text=True, timeout=15)
    if check.returncode != 0 or str(IMAGE) not in check.stdout:
        raise RuntimeError("ATTACHED_IMAGE_IDENTITY_NOT_CONFIRMED")


def detach():
    d = subprocess.run(["/usr/bin/hdiutil", "detach", str(VOLUME)],
                       capture_output=True, text=True, timeout=25)
    if d.returncode != 0 or VOLUME.exists():
        raise RuntimeError("SECURE_IMAGE_DETACH_FAILED")


def safe_receipt(path, payload):
    if path.exists():
        raise RuntimeError("REFUSE_OVERWRITE_RECEIPT")
    with path.open("x", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
        f.write("\n")
    os.chmod(path, 0o600)


def backup_once():
    entries, skipped, total = inventory()
    preflight_image()
    fd = os.open(LOCK, os.O_RDWR | os.O_CREAT, 0o600)
    attached = False
    snapshot_path = None
    report = None
    try:
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        try:
            mount()
        finally:
            # Image may already be mounted if identity inspection failed after attach.
            # The preflight confirmed this mount point was absent before our attempt.
            attached = VOLUME.exists()
        stamp = now().strftime("%Y%m%d_%H%M%S_KST")
        snapshot_path = VOLUME / "snapshots" / ("ASSET_V21_" + stamp + "_" + str(os.getpid()))
        if snapshot_path.exists():
            raise RuntimeError("SNAPSHOT_PATH_COLLISION")
        snapshot_path.mkdir(parents=True, mode=0o700)
        stored = []
        for src, target, expected, size, category in entries:
            dest = snapshot_path / target
            dest.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
            source_before = src.stat()
            if source_before.st_size != size:
                raise RuntimeError("SOURCE_SIZE_CHANGED_BEFORE_COPY")
            h = hashlib.sha256()
            with src.open("rb") as inp, dest.open("xb") as out:
                for chunk in iter(lambda: inp.read(1024 * 1024), b""):
                    out.write(chunk)
                    h.update(chunk)
            os.chmod(dest, 0o600)
            after = src.stat()
            if (h.hexdigest() != expected or after.st_size != source_before.st_size or
                after.st_mtime_ns != source_before.st_mtime_ns or
                digest(src) != expected or digest(dest) != expected):
                raise RuntimeError("SOURCE_CHANGED_OR_SNAPSHOT_SHA_MISMATCH")
            stored.append({"relative_path": target, "sha256": expected,
                           "size": size, "category": category})
        # Independent read verification on all selected saved files.
        for row in stored:
            actual = snapshot_path / row["relative_path"]
            if digest(actual) != row["sha256"] or actual.stat().st_size != row["size"]:
                raise RuntimeError("SNAPSHOT_FINAL_READ_VERIFICATION_FAILED")
        # Restore small non-sensitive samples to isolated temporary storage,
        # verify hash, then immediately remove scratch.
        samples = [r for r in stored if r["size"] < 80_000 and
                   r["category"] in ("registry", "project", "managed")][:15]
        if len(samples) < 8:
            raise RuntimeError("INSUFFICIENT_INDEPENDENT_RESTORE_SAMPLES")
        with tempfile.TemporaryDirectory(prefix="routabl_isolated_restore_") as temp:
            scratch = Path(temp)
            os.chmod(scratch, 0o700)
            for index, row in enumerate(samples):
                dest = scratch / ("%02d.recovered" % index)
                with (snapshot_path / row["relative_path"]).open("rb") as inp, dest.open("xb") as out:
                    shutil.copyfileobj(inp, out, 1024 * 1024)
                if digest(dest) != row["sha256"]:
                    raise RuntimeError("ISOLATED_RESTORE_SAMPLE_SHA_MISMATCH")
        summary = result_summary(entries, skipped, total)
        receipt = {
            "created_at_kst": now().isoformat(),
            "type": "ROUTABL_ASSET_V21_AES256_SELECTIVE_SNAPSHOT",
            "snapshot_name": snapshot_path.name,
            "manifest_name": REGISTRY.name,
            "manifest_sha256": digest(REGISTRY),
            "selection_sha256": selection_digest(entries),
            "source_manifest": REGISTRY.name,
            "source_manifest_sha256": digest(REGISTRY),
            "selection_sha256": selection_digest(entries),
            "encrypted_vault": str(IMAGE),
            "file_count": len(stored),
            "all_snapshot_sha256_verified": True,
            "isolated_restore_samples": len(samples),
            "isolated_restore_samples_verified": True,
            "records": stored,
            "summary": summary,
            "source_files_modified": False,
            "snapshot_pruned_or_overwritten": False,
        }
        receipt_path = snapshot_path / "snapshot_receipt.json"
        safe_receipt(receipt_path, receipt)
        report = {
            "status": "SUCCESS_PENDING_EJECT",
            "snapshot_name": snapshot_path.name,
            "manifest_name": REGISTRY.name,
            "manifest_sha256": digest(REGISTRY),
            "selection_sha256": selection_digest(entries),
            "snapshot_path": str(snapshot_path),
            "file_count": len(stored),
            "source_bytes": total,
            "receipt_sha256": digest(receipt_path),
            "isolated_restore_samples": len(samples),
            "sha256_verified": True,
            "created_at_kst": now().isoformat(),
        }
    finally:
        if attached:
            try:
                detach()
            except Exception as err:
                # Never pretend the image is locked when it is still attached.
                print(json.dumps({"status": "FAILED_NEEDS_MANUAL_EJECT",
                                  "reason": type(err).__name__,
                                  "snapshot_created": bool(snapshot_path)}, ensure_ascii=False),
                      file=sys.stderr, flush=True)
                raise
        os.close(fd)
    if report is None or VOLUME.exists():
        raise RuntimeError("NO_VERIFIED_CLOSED_SNAPSHOT")
    report["status"] = "SUCCESS"
    report["locked_after_backup"] = True
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=STATE,
                                     prefix=".selective-v2-", delete=False) as out:
        temporary = Path(out.name)
        json.dump(report, out, ensure_ascii=False, indent=2)
    os.chmod(temporary, 0o600)
    os.replace(temporary, STATUS)
    print(json.dumps(report, ensure_ascii=False))
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("action", choices=("plan", "backup"))
    args = ap.parse_args()
    try:
        entries, rejected, total = inventory()
        summary = result_summary(entries, rejected, total)
        if args.action == "plan":
            print(json.dumps({"status": "DRY_RUN_ONLY",
                              "source_manifest": REGISTRY.name,
                              **summary}, ensure_ascii=False, indent=2))
            return 0
        return backup_once()
    except Exception as e:
        # Exception messages are never printed because they might include sensitive paths.
        print(json.dumps({"status": "FAILED_SAFE", "failure_type": type(e).__name__,
                          "secure_volume_mounted": VOLUME.exists(),
                          "no_backup_success_claimed": True}, ensure_ascii=False),
              file=sys.stderr)
        return 2

if __name__ == "__main__":
    sys.exit(main())
