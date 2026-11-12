"""Isolated evidence adapter. Rooted reads, fixture byte checks, strict wire parser."""
from datetime import datetime
from hashlib import sha256
import json
import os
from pathlib import Path
import re
import stat

from backup_runner_candidate import Inventory, Local, Nas, Step, Stop, SHA, kst, matches

ROOT = Path(__file__).resolve().parent
MANIFEST = re.compile(r"asset_manifest_v0\.([0-9]+)\.json")
TOKEN = re.compile(r"[a-z0-9_-]{1,64}")
LIMIT = 1024 * 1024

def safe(path):
    if not path.is_absolute() or ROOT not in path.parents or path.resolve() != path:
        raise Stop("FAILED_SAFE", "PATH_OUTSIDE_FIXTURE")
    return path

def read(path):
    fd = os.open(safe(path), os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    with os.fdopen(fd, "rb") as handle:
        if not stat.S_ISREG(os.fstat(handle.fileno()).st_mode):
            raise Stop("FAILED_SAFE", "FIXTURE_NOT_REGULAR")
        data = handle.read(LIMIT + 1)
    if len(data) > LIMIT:
        raise Stop("FAILED_SAFE", "FIXTURE_SIZE_LIMIT")
    return data

def digest(path):
    return sha256(read(path)).hexdigest()

def unique(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("Duplicate JSON key")
        result[key] = value
    return result

def decode(data):
    value = json.loads(data, object_pairs_hook=unique)
    if not isinstance(value, dict):
        raise ValueError("Expected JSON object")
    return value

def fixture(name):
    if not matches(TOKEN, name):
        raise Stop("FAILED_SAFE", "INVALID_CASE_NAME")
    path = safe(ROOT / "cases" / name)
    if not path.is_dir():
        raise Stop("FAILED_SAFE", "FIXTURE_NOT_FOUND")
    return path

def inventory(base):
    registry = safe(base / "registry")
    entries = sorted((int(m[1]), p) for p in registry.iterdir()
                     if (m := MANIFEST.fullmatch(p.name)))
    if not entries or len({version for version, _ in entries}) != len(entries):
        raise Stop("FAILED_SAFE", "REGISTRY_AMBIGUOUS")
    manifest = entries[-1][1]
    rows = decode(read(base / "selection.json"))["files"]
    packed = []
    targets = set()
    for row in rows:
        name = row["name"]
        target = row["target"]
        if not matches(TOKEN, name) or not matches(TOKEN, target) or target in targets:
            raise Stop("FAILED_SAFE", "SELECTION_PATH_INVALID")
        if row["category"] not in ("registry", "fixture"):
            raise Stop("FAILED_SAFE", "SELECTION_CATEGORY_INVALID")
        blob = read(base / "assets" / name)
        targets.add(target)
        packed.append([target, sha256(blob).hexdigest(), len(blob), row["category"]])
    canonical = b"".join((json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n").encode()
                         for row in sorted(packed))
    return Inventory(manifest.name, digest(manifest), sha256(canonical).hexdigest(),
                     len(packed), sum(row[2] for row in packed))

def local(base):
    try:
        raw = read(base / "local_receipt.json")
        receipt = decode(raw)
        status = decode(read(base / "local_status.json"))
    except FileNotFoundError:
        return None
    receipt_hash = sha256(raw).hexdigest()
    fields = ("manifest_name", "manifest_sha256", "selection_sha256", "file_count", "source_bytes")
    bound = (status["receipt_sha256"] == receipt_hash
             and status["snapshot_name"] == receipt["snapshot_name"]
             and all(status[key] == receipt[key] for key in fields))
    return Local(Inventory(*(receipt[key] for key in fields)), receipt["snapshot_name"],
                 kst(datetime.fromisoformat(receipt["created_at_kst"])), receipt_hash,
                 bound and status["status"] == "SUCCESS" and status["locked_after_backup"] is True,
                 bound and status["sha256_verified"] is True and receipt["all_snapshot_sha256_verified"] is True)

def nas(base):
    try:
        data = decode(read(base / "nas_receipt.json"))
    except FileNotFoundError:
        return None
    return Nas(data["cas_id"], data["local_snapshot_name"], data["local_receipt_sha256"],
               data["manifest_sha256"], data["selection_sha256"], data["completed"])

def final_chain(base, current, local_record, nas_record):
    raw = decode(read(base / "nas_receipt.json"))
    # The fixture contains one ciphertext stand-in. Recompute its digest.
    blob = read(base / "cas_blob.bin")
    return (local(base) == local_record and nas(base) == nas_record
            and raw["components"] == 1 and raw["ciphertext_sha256"] == sha256(blob).hexdigest()
            and raw["ciphertext_bytes"] == len(blob))

def wire(stdout, code):
    if code != 0:
        return None
    if len(stdout) > 16384:
        return None
    try:
        return [decode(line) for line in stdout.splitlines() if line.strip()]
    except (ValueError, UnicodeError):
        return None

def gate_result(stdout, code, current, load_local):
    rows = wire(stdout, code)
    if not rows or len(rows) > 2:
        return Step("FAILED", code, False)
    first = rows[0]
    if first.get("job") != "local":
        return Step("FAILED", code, False)
    state = first.get("gate")
    if len(rows) == 1 and first.get("state") == "ALREADY_RUNNING" and first.get("executed") is False:
        return Step("LOCK_HELD", code, False)
    if state == "SKIPPED_CURRENT_SNAPSHOT_VERIFIED" and len(rows) == 1 and first.get("no_work_executed") is True:
        return Step("ALREADY_VERIFIED", code, False, load_local())
    if state == "READY_FOR_LOCAL_ONCE" and len(rows) == 1:
        return Step("NO_WORK", code, False)
    if state == "READY_FOR_LOCAL_ONCE" and len(rows) == 2:
        last = rows[1]
        if (first.get("mode") == "run" and first.get("no_work_executed") is False
                and first.get("manifest") == current.manifest_name
                and first.get("files") == current.file_count
                and last.get("job") == "local" and last.get("result") == "SUCCESS"
                and last.get("receipt_chain_verified") is True
                and all(row.get("manifest_sha256") == current.manifest_sha256
                        and row.get("selection_sha256") == current.selection_sha256 for row in rows)):
            return Step("CREATED", code, True, load_local())
    return Step("FAILED", code, False)

def nas_result(stdout, code, load_nas):
    rows = wire(stdout, code)
    if not rows or len(rows) != 1:
        return Step("FAILED", code, False)
    result = rows[0].get("result")
    if result == "INCREMENTAL_SNAPSHOT_VERIFIED":
        return Step("REPLICATED", code, True, load_nas())
    if result == "SNAPSHOT_ALREADY_INDEXED":
        return Step("ALREADY_VERIFIED", code, False, load_nas())
    return Step("FAILED", code, False)
