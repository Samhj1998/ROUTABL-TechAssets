#!/usr/bin/env python3
"""ROUTABL AssetSearch v1.2: separate metadata-only Mac source overlay.
Never edits v1.1 engine/database or source files; does not execute indexed code.
"""
import argparse, hashlib, importlib.util, json, os, sqlite3
from pathlib import Path

STORE = Path.home() / "Library/Application Support/ROUTABL-AssetSearch"
OLD_DB = STORE / "assets.sqlite"
NEW_DB = STORE / "assets_v1_2.sqlite"
BASE_SOURCE = STORE / "routabl_assetsearch_v1_1.py"
ROOT = Path.home() / "StudioProjects"
REGISTRY = Path.home() / "ROUTABL-TechAssets/30_REGISTRY/asset_manifest_v0.3.json"
SOURCES = (
    ("TA-CASE-20261102-01", "ROUTIVEL-Firebase-Migration/tools/firebase-migration/cloud_access.py",
     "Firebase 주소록 등록 성공사례", "cloud_access.py TA-CASE-20261102-01 고객등록 이력"),
    ("INTEGRATION-F1", "DISPATCH-One-Android/app/src/main/java/com/routivel/driver/TransportStatusPolicy.kt",
     "기사앱 배차 상태 처리", "TransportStatusPolicy.kt F1 취소상태 상태전환"),
)

def engine():
    spec = importlib.util.spec_from_file_location("routabl_assetsearch_legacy", BASE_SOURCE)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    mod.DB = NEW_DB
    return mod

def file_hash(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()

def build():
    if NEW_DB.exists():
        raise RuntimeError("V1_2_ALREADY_EXISTS: refusing to overwrite the current index")
    if not OLD_DB.is_file() or not REGISTRY.is_file():
        raise RuntimeError("V1_1_DB_OR_REGISTRY_UNAVAILABLE")
    previous = json.loads(REGISTRY.read_text(encoding="utf-8"))
    baseline = {r["asset_id"]: r for r in previous["asset_files"]}
    verified = []
    for asset_id, rel, title, tags in SOURCES:
        p = ROOT / rel
        if p.is_symlink() or not p.is_file():
            raise RuntimeError("MISSING_OR_SYMLINK: " + asset_id)
        before = p.stat()
        if before.st_size > 10_000_000:
            raise RuntimeError("SOURCE_TOO_LARGE: " + asset_id)
        sha = file_hash(p)
        after = p.stat()
        if before.st_size != after.st_size or before.st_mtime_ns != after.st_mtime_ns:
            raise RuntimeError("SOURCE_CHANGED_DURING_HASH: " + asset_id)
        if sha != baseline[asset_id]["sha256"]:
            raise RuntimeError("BASELINE_HASH_MISMATCH: " + asset_id)
        verified.append((asset_id, rel, title, tags, after, sha))
    temporary = STORE / "assets_v1_2.sqlite.building"
    if temporary.exists():
        raise RuntimeError("TEMPORARY_DB_ALREADY_EXISTS")
    try:
        with sqlite3.connect(f"file:{OLD_DB.as_posix()}?mode=ro", uri=True) as original:
            with sqlite3.connect(temporary) as target:
                original.backup(target)
        os.chmod(temporary, 0o600)
        mod = engine()
        with sqlite3.connect(temporary) as db:
            for asset_id, rel, title, tags, st, sha in verified:
                indexed = "MAC::StudioProjects/" + rel
                mod.add(db, indexed, "MAC_STUDIOPROJECTS_EXPLICIT_ALLOWLIST",
                        (ROOT / rel).suffix.lower(), st.st_size, st.st_mtime_ns,
                        sha, "MAC_METADATA_ONLY_SOURCE_NOT_COPIED", title,
                        tags + " Mac 원본 GitHub 동일성 확인", "", 0)
            db.commit()
            check = db.execute("PRAGMA integrity_check").fetchone()[0]
            count = db.execute("SELECT COUNT(*) FROM docs").fetchone()[0]
            indexed = db.execute("SELECT COUNT(*) FROM docs WHERE carrier='MAC_STUDIOPROJECTS_EXPLICIT_ALLOWLIST'").fetchone()[0]
            assert check == "ok" and indexed == len(verified)
        temporary.replace(NEW_DB)
        os.chmod(NEW_DB, 0o600)
    except Exception:
        if temporary.exists():
            temporary.unlink()
        raise
    print(json.dumps({"status": "SUCCESS", "index": str(NEW_DB), "total": count,
                      "new_mac_metadata_entries": indexed, "integrity": check,
                      "source_content_copied": False,
                      "baseline_index_unchanged": True,
                      "allowlist_assets": [x[0] for x in verified]}, ensure_ascii=False))

def query(term):
    engine().query(term)

def stats():
    engine().stats()

def main():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="action", required=True)
    sub.add_parser("build")
    p = sub.add_parser("query")
    p.add_argument("term")
    sub.add_parser("stats")
    a = parser.parse_args()
    if a.action == "build":
        build()
    elif a.action == "query":
        engine().query(a.term)
    else:
        engine().stats()

if __name__ == "__main__":
    main()
