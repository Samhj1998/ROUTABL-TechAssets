"""Digitopia 121 B. Read-only query acceleration with snapshot-local validation."""
import argparse
import json
import math
from pathlib import Path
import re
import runpy
import sqlite3
from time import perf_counter
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
reference = SimpleNamespace(**runpy.run_path(str(ROOT / "input/A_V15_QUERY_REFERENCE.py")))
SCOPE = reference.SCOPE
ALIASES = reference.ALIASES
CROSSWALK = reference.CROSSWALK
kind = reference.kind
relevant = reference.relevant
safe_like = reference.safe_like

COLUMNS = ("path", "title", "tags", "content")
RESULT_COLUMNS = ("path", "title", "tags", "sha", "status", "kind", "carrier", "sz", "mtime_ns")
MANUAL_SQL = "SELECT id,title,tags,path,source_grade,validation_grade,details FROM manual"
FTS_SCHEMA = re.compile(
    r"CREATE\s+VIRTUAL\s+TABLE\s+ft\s+USING\s+fts5\s*"
    r"\(\s*path\s*,\s*tags\s*,\s*content\s*,\s*tokenize\s*=\s*'trigram'\s*\)",
    re.IGNORECASE | re.ASCII,
)


def _predicates(alias, columns, terms):
    expressions = []
    params = []
    for term in terms:
        for column in columns:
            expressions.append(f"{alias}.{column} LIKE ? ESCAPE '!'")
            params.append(safe_like(term))
    return "(" + " OR ".join(expressions) + ")", params


def _quoted_match(term):
    return '"' + term.replace('"', '""') + '"'


def _now_ms(start):
    return (perf_counter() - start) * 1000


def _generation_status(db):
    entry = db.execute(
        "SELECT sql FROM main.sqlite_schema WHERE type='table' AND name='ft'"
    ).fetchone()
    if not entry or not FTS_SCHEMA.fullmatch(entry[0] or ""):
        return "unsupported_fts_schema"

    non_text_or_nul = " OR ".join(
        f"typeof(d.{column}) <> 'text' OR instr(d.{column}, char(0)) > 0"
        for column in COLUMNS
    )
    mismatched = db.execute(
        "SELECT 1 FROM main.docs AS d LEFT JOIN main.ft AS f ON f.rowid=d.rowid "
        "WHERE f.rowid IS NULL OR "
        "(d.path || ' ' || d.title) COLLATE BINARY IS NOT f.path OR "
        "d.tags COLLATE BINARY IS NOT f.tags OR "
        f"d.content COLLATE BINARY IS NOT f.content OR {non_text_or_nul} LIMIT 1"
    ).fetchone()
    if mismatched or db.execute(
        "SELECT 1 FROM main.ft AS f LEFT JOIN main.docs AS d ON d.rowid=f.rowid "
        "WHERE d.rowid IS NULL LIMIT 1"
    ).fetchone():
        return "fts_docs_mismatch"

    # The native check needs a writable connection. Copy only this pinned
    # snapshot into memory, then check the postings there.
    check = sqlite3.connect(":memory:")
    try:
        db.backup(check)
        check.execute("INSERT INTO ft(ft) VALUES('integrity-check')")
    except sqlite3.Error:
        return "fts_integrity_error"
    finally:
        check.close()
    return None


class SearchSnapshot:
    """A validated DB generation. Close and reopen to observe new writes."""

    def __init__(self, db_path):
        self.db_path = Path(db_path).resolve()
        self.db = None
        self.fallback_reason = None
        self.connection_ms = None
        self.validation_ms = None

    def __enter__(self):
        if self.db is not None:
            raise RuntimeError("search snapshot is already open")
        start = perf_counter()
        self.db = sqlite3.connect(self.db_path.as_uri() + "?mode=ro", uri=True, timeout=8)
        self.connection_ms = _now_ms(start)
        self.db.row_factory = sqlite3.Row
        start = perf_counter()
        try:
            self.db.execute("PRAGMA temp_store=MEMORY")
            self.db.execute("BEGIN")
            try:
                self.fallback_reason = _generation_status(self.db)
            except sqlite3.Error:
                self.fallback_reason = "fts_validation_error"
        except BaseException:
            self.db.close()
            self.db = None
            raise
        self.validation_ms = _now_ms(start)
        return self

    def __exit__(self, *exc):
        self.db.close()
        self.db = None

    def _candidate_rows(self, terms):
        predicate, params = _predicates("d", COLUMNS, terms)
        title_predicate, title_params = _predicates("t", ("title",), terms)
        phrase_union = " OR ".join(_quoted_match(term) for term in terms)
        projection = ", ".join("d." + column for column in RESULT_COLUMNS)
        sql = (
            "WITH candidate(rowid) AS ("
            "SELECT rowid FROM main.ft WHERE ft MATCH ? UNION "
            f"SELECT t.rowid FROM main.docs AS t WHERE {title_predicate}) "
            f"SELECT c.rowid AS candidate_rowid, {projection} "
            f"FROM candidate AS c LEFT JOIN main.docs AS d ON d.rowid=c.rowid AND {predicate}"
        )
        return self.db.execute(sql, [phrase_union, *title_params, *params]).fetchall()

    def _legacy_rows(self, terms):
        predicate, params = _predicates("d", COLUMNS, terms)
        projection = ", ".join("d." + column for column in RESULT_COLUMNS)
        sql = f"SELECT d.rowid AS candidate_rowid, {projection} FROM main.docs AS d WHERE {predicate}"
        return self.db.execute(sql, params).fetchall()

    def query(self, term, page=1, scope="all", page_size=12, *, metrics=None, audit=False):
        if self.db is None:
            raise RuntimeError("search snapshot is closed")
        term = str(term).strip()
        if not 2 <= len(term) <= 80:
            raise ValueError("검색어는 2~80자로 입력하세요.")
        if scope not in SCOPE:
            raise ValueError("검색 범위가 올바르지 않습니다.")
        page = max(1, min(int(page), 1000))
        page_size = max(1, min(int(page_size), 20))
        terms = [term] + [t for t in ALIASES.get(term, ()) if t.casefold() != term.casefold()]

        fallback = self.fallback_reason
        if any("\0" in term for term in terms):
            fallback = "nul_term"
        elif any(len(term) < 3 for term in terms):
            fallback = "short_term"
        start = perf_counter()
        if fallback is None:
            try:
                raw = self._candidate_rows(terms)
            except sqlite3.Error:
                fallback = "match_error"
        if fallback is not None:
            raw = self._legacy_rows(terms)
        manual_raw = self.db.execute(MANUAL_SQL).fetchall()
        sqlite_ms = _now_ms(start)

        start = perf_counter()
        rows = [{column: row[column] for column in RESULT_COLUMNS}
                for row in raw if row["path"] is not None]
        manual = []
        folded = [term.casefold() for term in terms]
        for row in manual_raw:
            info = dict(row)
            compare = " ".join(str(value) for value in info.values()).casefold()
            if any(term in compare for term in folded):
                manual.append(info)
        result = _finalize(term, terms, page, scope, page_size, rows, manual)
        postprocess_ms = _now_ms(start)

        if metrics is not None:
            metrics.update(
                candidate_count=len(raw),
                matched_before_scope=len(rows),
                accelerated=fallback is None,
                fallback_reason=fallback,
                sqlite_fetch_ms=sqlite_ms,
                postprocess_ms=postprocess_ms,
                connection_ms=self.connection_ms,
                generation_validation_ms=self.validation_ms,
            )
            if audit:
                metrics.update(
                    candidate_rowids=tuple(row["candidate_rowid"] for row in raw),
                    matched_rowids=tuple(row["candidate_rowid"] for row in raw if row["path"] is not None),
                )
        return result


def query(term, page=1, scope="all", page_size=12, *, db_path, metrics=None, audit=False):
    """One-shot query. Use SearchSnapshot to reuse a validated read snapshot."""
    with SearchSnapshot(db_path) as snapshot:
        return snapshot.query(term, page, scope, page_size, metrics=metrics, audit=audit)


def _finalize(term, terms, page, scope, page_size, rows, manual):
    scored = []
    for row in rows:
        category, label = kind(row["path"])
        if scope == "main" and category not in ("main", "test"):
            continue
        if scope == "variants" and category != "variant":
            continue
        if scope == "nas" and category not in ("nas", "zip"):
            continue
        scored.append((relevant(row, terms), row, category, label))
    # Sort all candidates, not just the arbitrary first 500.
    scored.sort(key=lambda x: (-x[0], x[1]["path"]))
    grouped = {}
    for score, row, category, label in scored:
        key = "sha:" + row["sha"] if row["sha"] and len(row["sha"]) == 64 else "path:" + row["path"]
        loc = {"path": row["path"], "category": category, "label": label, "status": row["status"]}
        if key not in grouped:
            matched = row["path"] in CROSSWALK and CROSSWALK[row["path"]]["sha256"] == row["sha"]
            provenance = CROSSWALK[row["path"]] if matched else None
            grouped[key] = {
                "title": row["title"], "path": row["path"], "status": row["status"],
                "score": score, "kind": category, "label": label, "sha256": row["sha"],
                "size_bytes": row["sz"], "locations": [loc], "duplicate_count": 1,
                "provenance": provenance,
                "can_reveal": category in ("main", "test", "variant"),
            }
        else:
            grouped[key]["locations"].append(loc)
            grouped[key]["duplicate_count"] += 1
            if grouped[key]["provenance"] is None and row["path"] in CROSSWALK:
                evidence = CROSSWALK[row["path"]]
                if evidence["sha256"] == row["sha"]:
                    grouped[key]["provenance"] = evidence
    found = list(grouped.values())
    result_count = len(found)
    pages = max(1, math.ceil(result_count / page_size))
    page = min(page, pages)
    subset = found[(page - 1) * page_size:page * page_size]
    # Trim alternate locations in returned JSON, but report the full total.
    for record in subset:
        record["locations"] = record["locations"][:25]
        p = record.get("provenance")
        if p:
            # Do not leak unverified GitHub/NAS links; only known proven references.
            p = dict(p)
            if not p["github_verified"]:
                p["github_repository"] = None
                p["github_file_path"] = None
            if not p["nas_verified"]:
                p["nas_copy"] = None
            record["provenance"] = p
    return {"term": term, "terms": terms, "scope": scope, "page": page,
            "page_size": page_size, "pages": pages, "match_count": len(scored),
            "group_count": result_count, "manual": manual, "results": subset}



def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("db_path", type=Path)
    parser.add_argument("term")
    parser.add_argument("--page", type=int, default=1)
    parser.add_argument("--page-size", type=int, default=12)
    parser.add_argument("--scope", choices=sorted(SCOPE), default="all")
    options = parser.parse_args()
    metrics = {}
    result = query(options.term, options.page, options.scope, options.page_size,
                   db_path=options.db_path, metrics=metrics)
    print(json.dumps({"result": result, "metrics": metrics}, ensure_ascii=False))


if __name__ == "__main__":
    main()
