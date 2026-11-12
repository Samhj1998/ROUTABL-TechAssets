#!/usr/bin/env python3
"""ROUTABL AssetSearch v1.7 scanner: current Mac projects + TechAssets guide/audit docs.
Derived from v1.3 (unchanged). Retired 2026-11-11 worktrees are no longer required.
Never runs source code, sends network requests, writes original files, or follows symlinks.
New independent DB; prior v1.1/v1.2 scripts/databases remain unchanged.
"""
import argparse, collections, hashlib, importlib.util, json, os, re, sqlite3
from pathlib import Path

STORE = Path.home() / "Library/Application Support/ROUTABL-AssetSearch"
ROOT = Path.home() / "StudioProjects"
PREVIOUS = STORE / "assets_v1_2.sqlite"
INDEX = STORE / "assets_v1_7_scanner_output.sqlite"
TA_ROOT = Path.home() / "ROUTABL-TechAssets"
TA_DIRS = ("00_GUIDE", "60_AUDIT")
TA_EXT = {".md", ".txt"}
TA_CARRIER = "TECHASSETS_DOCS_ALLOWLIST_V1_7"
LEGACY_ENGINE = STORE / "routabl_assetsearch_v1_1.py"
PROJECTS = (
    "DISPATCH-One-Android",          # 기사앱 (고객앱은 customer-android 하위)
    "ROUTABL-Senior-Driver",
    "DailyInspection-Android",
    "ROUTIVEL-Firebase-Migration",
    "ROUTABL-Analytics-Android",     # v1.6 추가
    "ROUTABL-CustomerRegistration-Android",  # v1.7 추가 (고객등록앱)
)
# 2026-11-11 정리로 삭제·패치 보관된 옛 작업본. v1.6은 더 이상 요구하지 않음.
RETIRED_PROJECTS = ("ROUTIVEL-Customer-Android", "ROUTABL-Control-Public-20261020",
                    "ROUTABL-Integration-Audit-20261019", "ROUTABL-Dispatch-Search-20261019")
SKIP_DIRS = {
    ".git", ".gradle", ".idea", ".kotlin", "build", "node_modules", "dist",
    "target", ".venv", "venv", "__pycache__", ".next", ".expo", "coverage",
    "out", "vendor", "Generated", "generated", ".cache", ".tox", "logs",
}
TEXT_EXT = {".kt", ".java", ".py", ".js", ".jsx", ".ts", ".tsx", ".swift",
            ".dart", ".md", ".txt", ".html", ".css", ".sql", ".sh"}
META_EXT = {".xml", ".json", ".yaml", ".yml", ".gradle", ".kts", ".properties"}
ALLOWED_EXT = TEXT_EXT | META_EXT
MAX_INDEX_BYTES = 1_000_000
CONTENT_LIMIT = 350_000

PRIVATE_PATH = re.compile(
    r"(^|[/_.-])(adminsdk|service.?account|credential|secret|secrets|token|"
    r"password|passwd|private.?key|keystore|id_rsa|google-services|"
    r"google.?service.?account|oauth|certificate|certificates)([/_.-]|$)", re.I)
SECRET_CONTENT = re.compile(
    r"-----BEGIN [^-\n]*PRIVATE KEY-----|"
    r"\b(?:AIza[\w-]{20,}|ya29\.[\w-]{12,}|sk-[\w-]{15,}|"
    r"gh[pousr]_[\w]{20,}|github_pat_[\w]{15,}|AKIA[A-Z0-9]{16}|"
    r"xox[baprs]-[\w-]{12,})\b|"
    r"(?:client_secret|private_key|api[_-]?key|auth[_-]?token|access[_-]?token)"
    r"\s*[:=]\s*[\"'][^\"'\n]{8,}[\"']", re.I)
EMAIL = re.compile(r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}")
PHONE = re.compile(r"(?<!\d)01[0-9]-?\d{3,4}-?\d{4}(?!\d)")
PERSONAL = re.compile(r"\b\d{6}-[1-8]\d{6}\b")
# Baseline metadata-only verified entries must be preserved, not replaced.
PROTECTED_BASELINE = {
    "MAC::StudioProjects/ROUTIVEL-Firebase-Migration/tools/firebase-migration/cloud_access.py",
    "MAC::StudioProjects/DISPATCH-One-Android/app/src/main/java/com/routivel/driver/TransportStatusPolicy.kt",
}

def engine():
    spec = importlib.util.spec_from_file_location("routabl_legacy_engine", LEGACY_ENGINE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.DB = INDEX
    return module

def digest(path):
    h = hashlib.sha256()
    with path.open("rb") as inp:
        for part in iter(lambda: inp.read(1024 * 1024), b""):
            h.update(part)
    return h.hexdigest()

def protect_or_redact(path, extension, size):
    if extension not in TEXT_EXT or size > CONTENT_LIMIT:
        return "MAC_METADATA_ONLY", "", "P2"
    try:
        raw = path.read_bytes()
        if b"\x00" in raw:
            return "MAC_METADATA_ONLY_BINARY_LIKE", "", "P2"
        value = raw.decode("utf-8-sig")
        if SECRET_CONTENT.search(value):
            return "MAC_PROTECTED_CONTENT_NOT_INDEXED", "", "P1"
        value = PERSONAL.sub("[IDENTIFIER]", PHONE.sub("[PHONE]", EMAIL.sub("[EMAIL]", value)))
        return "MAC_REDACTED_TEXT", value, "P3"
    except (OSError, UnicodeError):
        return "MAC_METADATA_ONLY_UNREADABLE", "", "P2"

def build():
    if INDEX.exists():
        raise RuntimeError("V1_7_EXISTS_REFUSE_OVERWRITE")
    if not PREVIOUS.is_file() or not LEGACY_ENGINE.is_file():
        raise RuntimeError("PREVIOUS_INDEX_OR_ENGINE_UNAVAILABLE")
    temp = STORE / "assets_v1_7.sqlite.building"
    if temp.exists():
        raise RuntimeError("V1_7_TEMP_EXISTS_REFUSE_OVERWRITE")
    project_paths = []
    for name in PROJECTS:
        p = ROOT / name
        if not p.is_dir() or p.is_symlink():
            raise RuntimeError("SOURCE_PROJECT_UNAVAILABLE:" + name)
        project_paths.append(p)
    with sqlite3.connect("file:" + str(PREVIOUS) + "?mode=ro", uri=True) as source:
        previous_rows = source.execute("select count(*) from docs").fetchone()[0]
        if previous_rows != 2272:
            raise RuntimeError("UNEXPECTED_PREVIOUS_DB_ROWS")
        with sqlite3.connect(temp) as target:
            source.backup(target)
    os.chmod(temp, 0o600)
    legacy = engine()
    total = collections.Counter()
    by_project = {}
    try:
        with sqlite3.connect(temp) as db:
            for project in project_paths:
                count = collections.Counter()
                for folder, dirs, filenames in os.walk(project, followlinks=False):
                    dirs[:] = sorted(x for x in dirs if x not in SKIP_DIRS
                                     and not x.startswith(".")
                                     and not (Path(folder) / x).is_symlink())
                    for filename in sorted(filenames):
                        fp = Path(folder) / filename
                        if fp.is_symlink() or not fp.is_file():
                            count["skipped_symlink_or_nonfile"] += 1
                            continue
                        rel = fp.relative_to(ROOT).as_posix()
                        if PRIVATE_PATH.search("/" + rel) or filename.startswith("."):
                            count["excluded_sensitive_path"] += 1
                            continue
                        ext = fp.suffix.lower()
                        if ext not in ALLOWED_EXT:
                            count["excluded_other_extension"] += 1
                            continue
                        try:
                            before = fp.stat()
                            if before.st_size > MAX_INDEX_BYTES:
                                count["excluded_large"] += 1
                                continue
                            source_status, content, grade = protect_or_redact(fp, ext, before.st_size)
                            checksum = digest(fp)
                            after = fp.stat()
                            if before.st_size != after.st_size or before.st_mtime_ns != after.st_mtime_ns:
                                count["skipped_changed_during_scan"] += 1
                                continue
                        except (OSError, PermissionError):
                            count["skipped_read_error"] += 1
                            continue
                        key = "MAC::StudioProjects/" + rel
                        if key in PROTECTED_BASELINE:
                            old = db.execute("SELECT sha FROM docs WHERE path=?", (key,)).fetchone()
                            if old is None or old[0] != checksum:
                                raise RuntimeError("VERIFIED_BASELINE_CHANGED")
                            count["existing_verified_baseline_kept"] += 1
                            continue
                        classification = "TECH_PUBLIC_TO_OWNER" if grade == "P3" else "TECH_RESTRICTED_METADATA"
                        title = fp.stem[:150]
                        tags = (project.name + " " + title + " " + grade + " " + classification +
                                " " + legacy.tag_of(rel))
                        legacy.add(db, key, "MAC_PROJECTS_ALLOWLIST_V1_3", ext, after.st_size,
                                   after.st_mtime_ns, checksum, source_status, title, tags,
                                   content, 0)
                        count["indexed"] += 1
                        count["content_indexed" if content else "metadata_only"] += 1
                        count["class_" + grade] += 1
                by_project[project.name] = dict(count)
                total.update(count)
            ta_count = collections.Counter()
            for sub in TA_DIRS:
                base = TA_ROOT / sub
                if not base.is_dir() or base.is_symlink():
                    ta_count["missing_dir"] += 1
                    continue
                for folder, dirs, filenames in os.walk(base, followlinks=False):
                    dirs[:] = sorted(x for x in dirs if not x.startswith(".")
                                     and not (Path(folder) / x).is_symlink())
                    for filename in sorted(filenames):
                        fp = Path(folder) / filename
                        if fp.is_symlink() or not fp.is_file() or filename.startswith("."):
                            continue
                        rel = fp.relative_to(TA_ROOT).as_posix()
                        ext = fp.suffix.lower()
                        if ext not in TA_EXT:
                            ta_count["excluded_other_extension"] += 1
                            continue
                        if PRIVATE_PATH.search("/" + rel):
                            ta_count["excluded_sensitive_path"] += 1
                            continue
                        try:
                            before = fp.stat()
                            if before.st_size > MAX_INDEX_BYTES:
                                ta_count["excluded_large"] += 1
                                continue
                            source_status, content, grade = protect_or_redact(fp, ext, before.st_size)
                            checksum = digest(fp)
                            after = fp.stat()
                            if before.st_size != after.st_size or before.st_mtime_ns != after.st_mtime_ns:
                                ta_count["skipped_changed_during_scan"] += 1
                                continue
                        except (OSError, PermissionError):
                            ta_count["skipped_read_error"] += 1
                            continue
                        title = fp.stem[:150]
                        tags = ("ROUTABL-TechAssets " + sub + " 기술자산 문서 " + title + " " + grade)
                        legacy.add(db, "TA::" + rel, TA_CARRIER, ext, after.st_size,
                                   after.st_mtime_ns, checksum, source_status, title, tags, content, 0)
                        ta_count["indexed"] += 1
            ta_actual = db.execute("SELECT COUNT(*) FROM docs WHERE carrier=?", (TA_CARRIER,)).fetchone()[0]
            if ta_actual != ta_count["indexed"]:
                raise RuntimeError("TA_INDEX_COUNT_INVARIANT")
            by_project["ROUTABL-TechAssets(00_GUIDE,60_AUDIT)"] = dict(ta_count)
            actual = db.execute("SELECT COUNT(*) FROM docs WHERE carrier='MAC_PROJECTS_ALLOWLIST_V1_3'").fetchone()[0]
            expected = total["indexed"]
            verified = db.execute("SELECT COUNT(*) FROM docs WHERE carrier='MAC_STUDIOPROJECTS_EXPLICIT_ALLOWLIST'").fetchone()[0]
            rows = db.execute("SELECT COUNT(*) FROM docs").fetchone()[0]
            if actual != expected or verified != 2 or rows != previous_rows + expected + ta_actual:
                raise RuntimeError("INDEX_COUNT_INVARIANT")
            if db.execute("PRAGMA quick_check").fetchone()[0] != "ok":
                raise RuntimeError("INDEX_INTEGRITY_FAILED")
            # Explicitly ensure the index contains no unredacted direct PII
            for content, in db.execute("SELECT content FROM docs WHERE carrier IN ('MAC_PROJECTS_ALLOWLIST_V1_3', ?)", (TA_CARRIER,)):
                if EMAIL.search(content) or PHONE.search(content) or PERSONAL.search(content) or SECRET_CONTENT.search(content):
                    raise RuntimeError("SOURCE_INDEX_SENSITIVE_CONTENT_DETECTED")
            db.commit()
        temp.replace(INDEX)
        os.chmod(INDEX, 0o600)
    except Exception:
        if temp.exists(): temp.unlink()
        raise
    print(json.dumps({"result": "SUCCESS", "version": "1.7", "techassets_doc_rows": ta_actual, "previous_rows": previous_rows,
                      "total_rows": rows, "mac_new_rows": expected,
                      "mac_prior_verified_rows": verified,
                      "scan_summary": dict(total), "project_counts": by_project,
                      "index_path": str(INDEX), "source_modified": False,
                      "secrets_written_to_index": False,
                      "sqlite_integrity": "ok"}, ensure_ascii=False))

def query(term):
    engine().query(term)

def stats():
    engine().stats()

def main():
    a = argparse.ArgumentParser()
    sub = a.add_subparsers(dest="action", required=True)
    sub.add_parser("build")
    p = sub.add_parser("query"); p.add_argument("term")
    sub.add_parser("stats")
    args = a.parse_args()
    if args.action == "build": build()
    elif args.action == "query": query(args.term)
    else: stats()

if __name__ == "__main__":
    main()
