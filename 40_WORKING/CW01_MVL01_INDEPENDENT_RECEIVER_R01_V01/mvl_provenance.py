"""Local source evidence for the isolated MVL-01 search."""
import hashlib
import json
import os
import re
import sqlite3
import stat
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[1]
PROJECTS = REPO.parent / "StudioProjects"
REGISTRY = REPO / "30_REGISTRY"
LATEST_NAME = "asset_manifest_v0.27.json"
LATEST_SHA = "afe17adb54103952c0e84d296ded42a478fca49f25bd53f1f87dc0c73e1ce244"
SHA = re.compile(r"[a-f0-9]{64}")


def read_evidence(path, keep_bytes=False):
    """Open each component without following symlinks and hash one stable inode."""
    path = Path(path)
    if not path.is_absolute() or ".." in path.parts:
        raise ValueError("INVALID_SOURCE_PATH")
    flags = os.O_RDONLY | os.O_NOFOLLOW
    directory = os.open("/", flags | os.O_DIRECTORY)
    try:
        for part in path.parts[1:-1]:
            child = os.open(part, flags | os.O_DIRECTORY, dir_fd=directory)
            os.close(directory)
            directory = child
        fd = os.open(path.name, flags | os.O_NONBLOCK, dir_fd=directory)
        with os.fdopen(fd, "rb") as source:
            before = os.fstat(source.fileno())
            if not stat.S_ISREG(before.st_mode):
                raise ValueError("SOURCE_NOT_REGULAR")
            digest = hashlib.sha256()
            captured = bytearray()
            size = 0
            for block in iter(lambda: source.read(1024 * 1024), b""):
                digest.update(block)
                size += len(block)
                if keep_bytes:
                    captured.extend(block)
            after = os.fstat(source.fileno())
        named = path.lstat()
        def identity(info):
            return (info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns, info.st_ctime_ns)
        if identity(before) != identity(after) or identity(after) != identity(named) or size != before.st_size:
            raise ValueError("SOURCE_CHANGED_DURING_READ")
        return digest.hexdigest(), size, bytes(captured) if keep_bytes else None
    finally:
        os.close(directory)


def load_registry(directory=REGISTRY):
    found = {}
    for entry in directory.iterdir():
        match = re.fullmatch(r"asset_manifest_v(\d+)\.(\d+)\.json", entry.name)
        if match:
            version = tuple(map(int, match.groups()))
            if version in found:
                raise ValueError("REGISTRY_VERSION_COLLISION")
            found[version] = entry
    if not found or found[max(found)].name != LATEST_NAME:
        raise ValueError("UNPINNED_LATEST_REGISTRY")
    sha, _, raw = read_evidence(found[max(found)], keep_bytes=True)
    if sha != LATEST_SHA:
        raise ValueError("REGISTRY_PIN_MISMATCH")
    data = json.loads(raw)
    if data["schema_version"] != "0.27":
        raise ValueError("REGISTRY_SCHEMA_MISMATCH")
    ids = {}
    for item in data["asset_files"]:
        asset_id = item["asset_id"]
        if asset_id in ids:
            raise ValueError("DUPLICATE_REGISTRY_ID")
        ids[asset_id] = item
    return data, ids


def resolve_crosswalk():
    data, ids = load_registry()
    result = {}
    for item in data["provenance_crosswalk"]:
        path = Path(item["mac_original_path"])
        rel = path.relative_to(PROJECTS).as_posix()
        key = "MAC::StudioProjects/" + rel
        anchor = ids[item["asset_id"]]
        if (key in result or anchor["observed_original_path"] != str(path)
                or anchor["sha256"] != item["mac_sha256"] or not SHA.fullmatch(item["mac_sha256"])):
            raise ValueError("CROSSWALK_REGISTRY_MISMATCH")
        result[key] = {
            "asset_id": item["asset_id"], "sha256": item["mac_sha256"],
            "github_repository": item.get("github_repository"),
            "github_file_path": item.get("github_file_path"),
            "nas_copy": item.get("nas_independent_copy_path"),
            "github_verified": item.get("github_remote_file_verified", "").startswith("YES_"),
            "nas_verified": item.get("nas_status") == "DIRECT_SOURCE_SHA256_MATCH",
        }
    return result


def verify_source(ref, indexed_sha):
    origin = dict(ref, observed_sha256=None, status="UNVERIFIED")
    if indexed_sha != ref["expected_sha256"]:
        origin["status"] = "INDEX_HASH_MISMATCH"
        return origin
    try:
        observed, size, _ = read_evidence(ref["source_path"])
    except FileNotFoundError:
        origin["status"] = "SOURCE_MISSING"
        return origin
    except (ValueError, OSError):
        origin["status"] = "SOURCE_UNAVAILABLE"
        return origin
    origin.update(observed_sha256=observed, observed_size_bytes=size)
    if observed != ref["expected_sha256"] or size != ref["expected_size_bytes"]:
        origin["status"] = "HASH_MISMATCH"
    else:
        origin["status"] = "LOCAL_HASH_MATCH"
    return origin


def make_ref(asset_id, version, path, sha, size, registration):
    official = registration in ("OFFICIAL_ROW", "REGISTRY_DOCUMENT")
    return {"asset_id": asset_id, "source_version": version, "source_path": str(path),
            "expected_sha256": sha, "expected_size_bytes": size, "registration": registration,
            "registry_version": "0.27" if official else None,
            "registry_sha256": LATEST_SHA if official else None}


def overlay_ref_allowed(ref, official):
    path = Path(ref["source_path"])
    asset_id = ref["asset_id"]
    status = ref["registration"]
    if not SHA.fullmatch(ref["expected_sha256"]):
        return False
    if status == "ISOLATED_CANDIDATE":
        if asset_id == "MVL01-FEEDBACK":
            return path == ROOT / "FEEDBACK_CANDIDATE.md"
        return (re.fullmatch(r"MVL-USER-[A-Z0-9][A-Z0-9-]{0,54}", asset_id)
                and path.parent == ROOT / "incoming"
                and re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,100}\.(?:md|txt)", path.name))
    for expected in json.loads((ROOT / "REFERENCES.json").read_bytes()):
        if expected["id"] != asset_id:
            continue
        if (status, ref["source_version"], path, ref["expected_sha256"]) != (
                expected["registration"], expected["version"], REPO / expected["path"], expected["sha256"]):
            return False
        if status != "OFFICIAL_ROW":
            return True
        row = official[asset_id]
        return (row["observed_original_path"], row["sha256"], row["bytes"]) == (
            str(path), ref["expected_sha256"], ref["expected_size_bytes"])
    return False


def attach_origins(db_path, subset):
    _, official = load_registry()
    crosswalk = resolve_crosswalk()
    by_id = {value["asset_id"]: key for key, value in crosswalk.items()}
    with sqlite3.connect(db_path.as_uri() + "?mode=ro", uri=True) as db:
        has_overlay = db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='mvl_sources'").fetchone()
        for result in subset:
            # For deduplicated rows the canonical verified source may differ from the first result path.
            paths = [result["path"]] + [row["path"] for row in result["locations"]]
            provenance = result.get("provenance")
            preferred = by_id.get(provenance["asset_id"]) if provenance else None
            ref = None
            for path in ([preferred] if preferred else []) + paths:
                if path in crosswalk:
                    x = official[crosswalk[path]["asset_id"]]
                    ref = make_ref(x["asset_id"], None, x["observed_original_path"], x["sha256"], x["bytes"], "OFFICIAL_ROW")
                    break
                if has_overlay and path.startswith("MVL/"):
                    row = db.execute("SELECT reference_json FROM mvl_sources WHERE index_path=?", (path,)).fetchone()
                    if row:
                        candidate = json.loads(row[0])
                        if path == "MVL/" + candidate["asset_id"] and overlay_ref_allowed(candidate, official):
                            ref = candidate
                            break
            result["origin"] = verify_source(ref, result["sha256"]) if ref else {"status": "UNVERIFIED", "observed_sha256": None}
