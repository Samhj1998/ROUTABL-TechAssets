"""ASSET-SEARCH-01 v1.5 candidate C: FTS5 trigram candidate extraction.

Only the document *candidate extraction* differs from A v1.5. Validation, alias
expansion, manual matching, scope filter, scoring, sorting, SHA grouping,
locations, provenance and paging are A's code, with A's module globals
(ALIASES/CROSSWALK/INDEX) turned into engine bindings.

Accelerated path (only on a verified index generation):
  1. ft MATCH '"t1" OR "t2" ...' -> candidate rowids (no rank, no LIMIT)
  2. docs rows WHERE rowid IN candidates AND <A's exact LIKE ... ESCAPE '!' OR-expression>
Otherwise A's full LIKE scan runs (fallback), in the same read snapshot.
"""
import json
import math
import os
import sqlite3
import threading
import time
from pathlib import Path

# ---------------------------------------------------------------------------
# A v1.5 constants and helpers (verbatim; relevant() takes crosswalk as a binding)

MAIN_PROJECTS = ("DISPATCH-One-Android", "ROUTABL-Senior-Driver",
                 "ROUTIVEL-Customer-Android", "DailyInspection-Android",
                 "ROUTIVEL-Firebase-Migration")


SCOPE = {"all", "main", "variants", "nas"}


def kind(path):
    if path.startswith("MAC::StudioProjects/"):
        rel = path.removeprefix("MAC::StudioProjects/")
        project = rel.split("/", 1)[0]
        if project in MAIN_PROJECTS:
            if "/src/test/" in rel or "/src/androidTest/" in rel:
                return "test", "테스트 코드"
            return "main", "개발 원본"
        return "variant", "과거/파생 작업본"
    if "::" in path:
        return "zip", "ZIP 내부 목록"
    if path.startswith("ROUTABL_Whitepaper_Archive_") or path.startswith("00_") or path.startswith("02_"):
        return "nas", "NAS 보관자료"
    return "nas", "기술자산 보관본"


def safe_like(value):
    return "%" + value.replace("!", "!!").replace("%", "!%").replace("_", "!_") + "%"


def basename(path):
    name = path.split("::")[-1].rsplit("/", 1)[-1]
    return name


def relevant(row, terms, CROSSWALK):
    path = row["path"].casefold()
    title = row["title"].casefold()
    file_name = basename(row["path"]).casefold()
    tags = row["tags"].casefold()
    category, _ = kind(row["path"])
    score = 0
    for idx, term in enumerate(terms):
        t = term.casefold()
        weight = 1.0 if idx == 0 else 0.65
        hits = 0
        if file_name == t or file_name.rsplit(".", 1)[0] == t:
            hits += 125
        elif file_name.startswith(t):
            hits += 94
        elif t in file_name:
            hits += 68
        if title == t:
            hits += 64
        elif title.startswith(t):
            hits += 46
        elif t in title:
            hits += 33
        if t in path:
            hits += 18
        if t in tags:
            hits += 13
        score += int(weight * hits)
    if category == "main":
        score += 42
    elif category == "test":
        score += 8
    elif category == "variant":
        score -= 12
    elif category == "nas":
        direct = any(t.casefold() in path or t.casefold() in title for t in terms)
        if direct and path.startswith("02_핵심기술/"):
            score += 85
        elif path.startswith("00_인계와기준/"):
            score -= 14
        elif path.startswith("ROUTABL_Whitepaper_Archive_"):
            score -= 18
    elif category == "zip":
        score -= 135
    if row["path"] in CROSSWALK and CROSSWALK[row["path"]]["sha256"] == row["sha"]:
        score += 160
    if row["status"] == "OK":
        score += 7
    if "/src/test/" in path or "/src/androidtest/" in path:
        score -= 24
    if "v0.4" in file_name:
        score += 3
    return score


def _normalize_args(term, page, scope, page_size, ALIASES):
    # A v1.5 query() prologue, verbatim order of checks and messages.
    term = str(term).strip()
    if not 2 <= len(term) <= 80:
        raise ValueError("검색어는 2~80자로 입력하세요.")
    if scope not in SCOPE:
        raise ValueError("검색 범위가 올바르지 않습니다.")
    page = max(1, min(int(page), 1000))
    page_size = max(1, min(int(page_size), 20))
    terms = [term] + [t for t in ALIASES.get(term, ()) if t.casefold() != term.casefold()]
    return term, page, scope, page_size, terms


def _like_where(terms):
    # A v1.5 WHERE construction, verbatim.
    expressions = []
    params = []
    for t in terms:
        for col in ("path", "title", "tags", "content"):
            expressions.append(col + " LIKE ? ESCAPE '!'")
            params.append(safe_like(t))
    return " OR ".join(expressions), params


DOC_COLUMNS = "path,title,tags,sha,status,kind,carrier,sz,mtime_ns"


def _manual_rows(db, terms):
    # A v1.5 manual matching, verbatim.
    manual = []
    for row in db.execute("SELECT id,title,tags,path,source_grade,validation_grade,details FROM manual"):
        info = dict(row)
        compare = " ".join(str(v) for v in info.values()).casefold()
        if any(t.casefold() in compare for t in terms):
            manual.append(info)
    return manual


def _assemble(term, terms, scope, page, page_size, rows, manual, CROSSWALK):
    # A v1.5 post-processing after the DB block, verbatim.
    scored = []
    for row in rows:
        category, label = kind(row["path"])
        if scope == "main" and category not in ("main", "test"):
            continue
        if scope == "variants" and category != "variant":
            continue
        if scope == "nas" and category not in ("nas", "zip"):
            continue
        scored.append((relevant(row, terms, CROSSWALK), row, category, label))
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
    for record in subset:
        record["locations"] = record["locations"][:25]
        p = record.get("provenance")
        if p:
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


def reference_query(index, ALIASES, CROSSWALK, term, page=1, scope="all", page_size=12):
    """A v1.5 query() with INDEX/ALIASES/CROSSWALK as arguments. Last-resort fallback."""
    term, page, scope, page_size, terms = _normalize_args(term, page, scope, page_size, ALIASES)
    where, params = _like_where(terms)
    sql = "SELECT " + DOC_COLUMNS + " FROM docs WHERE " + where
    with sqlite3.connect("file:" + str(index) + "?mode=ro", uri=True, timeout=8) as db:
        db.row_factory = sqlite3.Row
        rows = [dict(row) for row in db.execute(sql, params)]
        manual = _manual_rows(db, terms)
    return _assemble(term, terms, scope, page, page_size, rows, manual, CROSSWALK)


# ---------------------------------------------------------------------------
# Candidate C: verified-generation FTS5 acceleration

# The only FTS layout this candidate understands: internal content, columns
# (path,tags,content) where path = docs.path || ' ' || docs.title, trigram
# tokenizer with defaults (case_sensitive=0, remove_diacritics=0).
EXPECTED_FT_SQL = "CREATE VIRTUAL TABLE ft USING fts5(path,tags,content,tokenize='trigram')"
EXPECTED_FT_CONFIG_VERSION = 4
REQUIRED_DOC_COLUMNS = ("path", "carrier", "kind", "sz", "mtime_ns", "sha", "status",
                        "title", "tags", "content")
MIN_TRIGRAM_CHARS = 3


class IndexUnverified(Exception):
    pass


def _ms(ns):
    return round(ns / 1e6, 4)


def fts_phrase_expression(terms):
    """OR of quoted FTS5 phrases; quotes doubled, so every term is literal text."""
    return " OR ".join('"' + t.replace('"', '""') + '"' for t in terms)


def verify_generation(db):
    """Prove, inside the caller's read snapshot, that ft exactly mirrors docs.

    Raises IndexUnverified(reason). Three independent checks:
      schema  : ft DDL/config is the supported layout, docs is a rowid table.
      linkage : bijection docs.rowid <-> ft rowid, with ft.path = path||' '||title,
                ft.tags = tags, ft.content = content (binary equality). This is
                what FTS integrity-check does NOT cover (it never reads docs).
      fts     : PRAGMA integrity_check(ft) -> FTS5 index matches its own content.
    """
    master = {name: (typ, sql) for typ, name, sql in
              db.execute("SELECT type,name,sql FROM sqlite_master WHERE name IN "
                         "('docs','ft','ft_content','ft_data','ft_idx','ft_docsize','ft_config')")}
    ft = master.get("ft")
    if ft is None:
        raise IndexUnverified("unsupported_fts_schema:ft_missing")
    if " ".join((ft[1] or "").split()) != EXPECTED_FT_SQL:
        raise IndexUnverified("unsupported_fts_schema:ft_ddl")
    for shadow in ("ft_content", "ft_data", "ft_idx", "ft_docsize", "ft_config"):
        if shadow not in master:
            raise IndexUnverified("unsupported_fts_schema:" + shadow + "_missing")
    version = db.execute("SELECT v FROM ft_config WHERE k='version'").fetchone()
    if version is None or version[0] != EXPECTED_FT_CONFIG_VERSION:
        raise IndexUnverified("unsupported_fts_schema:ft_config_version")
    docs = master.get("docs")
    if docs is None or docs[0] != "table" or "WITHOUT ROWID" in (docs[1] or "").upper():
        raise IndexUnverified("unsupported_docs_schema")
    cols = {r[1] for r in db.execute("PRAGMA table_info(docs)")}
    if not set(REQUIRED_DOC_COLUMNS) <= cols:
        raise IndexUnverified("unsupported_docs_schema:columns")
    n_docs, n_ft, n_same = db.execute(
        "SELECT (SELECT count(*) FROM docs), (SELECT count(*) FROM ft_content),"
        " (SELECT count(*) FROM docs d JOIN ft_content c ON c.id = d.rowid"
        "   WHERE c.c0 = d.path || ' ' || d.title AND c.c1 = d.tags AND c.c2 = d.content)"
    ).fetchone()
    if not (n_docs == n_ft == n_same):
        raise IndexUnverified("docs_ft_mismatch:docs=%d,ft=%d,identical=%d" % (n_docs, n_ft, n_same))
    check = [r[0] for r in db.execute("PRAGMA integrity_check(ft)")]
    if check != ["ok"]:
        raise IndexUnverified("fts_integrity:" + "; ".join(str(c) for c in check[:3]))


class SearchEngine:
    """Keeps one read-only connection so PRAGMA data_version can prove that the
    verified generation is still the one being read."""

    def __init__(self, index, aliases, crosswalk):
        self.index = str(index)
        self.aliases = aliases
        self.crosswalk = crosswalk
        self._lock = threading.RLock()
        self._db = None
        self._ident = None
        self._serial = 0
        self._fts_touched = False   # this connection has instantiated/used the ft vtab
        self._verified = {}   # generation token -> (ok, reason, verify_ms)
        self.last_metrics = None

    # -- connection / generation -------------------------------------------
    def close(self):
        with self._lock:
            if self._db is not None:
                self._db.close()
            self._db = None
            self._ident = None
            self._verified.clear()

    def _ensure_connection(self, metrics):
        st = os.stat(self.index)
        ident = (st.st_dev, st.st_ino)
        if self._db is not None and ident != self._ident:
            # File replaced (rename/copy to new inode): old connection would read a stale file.
            metrics["reconnect_reason"] = "file_replaced"
            self.close()
        if self._db is None:
            self._db = sqlite3.connect("file:" + self.index + "?mode=ro", uri=True, timeout=8,
                                       isolation_level=None, check_same_thread=False)
            self._db.row_factory = sqlite3.Row
            self._ident = ident
            self._serial += 1
            self._fts_touched = False
            self._verified.clear()
            metrics["connection_reused"] = False
        else:
            metrics["connection_reused"] = True
        return self._db

    def _generation_token(self, db):
        # Must run inside BEGIN: schema_version starts the read transaction, so
        # data_version afterwards describes exactly this snapshot.
        schema_version = db.execute("PRAGMA schema_version").fetchone()[0]
        data_version = db.execute("PRAGMA data_version").fetchone()[0]
        return (self._serial, self._ident, schema_version, data_version)

    def _generation_status(self, db, token, metrics):
        cached = self._verified.get(token)
        if cached is None:
            t0 = time.perf_counter_ns()
            try:
                verify_generation(db)
                ok, reason = True, None
            except IndexUnverified as exc:
                ok, reason = False, str(exc)
            except sqlite3.Error as exc:
                ok, reason = False, "verify_error:" + type(exc).__name__ + ":" + str(exc)
            cached = (ok, reason, _ms(time.perf_counter_ns() - t0))
            self._verified = {token: cached}
            metrics["verify_performed"] = True
            metrics["verify_ms"] = cached[2]
        metrics["generation_verified"] = cached[0]
        return cached

    # -- query ----------------------------------------------------------------
    def query(self, term, page=1, scope="all", page_size=12):
        return self.query_with_metrics(term, page, scope, page_size)[0]

    def query_with_metrics(self, term, page=1, scope="all", page_size=12, debug=False):
        t_start = time.perf_counter_ns()
        term, page, scope, page_size, terms = _normalize_args(term, page, scope, page_size, self.aliases)
        m = {"term_count": len(terms), "accelerated": False, "fallback_reason": None,
             "fts_candidates": None, "confirmed_rows": None, "false_candidates_removed": None,
             "verify_performed": False, "verify_ms": 0.0, "generation_verified": None,
             "connection_reused": None, "reconnect_reason": None,
             "t_connect_ms": 0.0, "t_generation_ms": 0.0, "t_fts_ms": 0.0, "t_docs_ms": 0.0,
             "t_manual_ms": 0.0, "t_sql_total_ms": 0.0, "t_post_ms": 0.0, "t_total_ms": 0.0}
        reason = None
        if any("\x00" in t for t in terms):
            reason = "nul_in_term"
        elif len(terms[0]) < MIN_TRIGRAM_CHARS:
            reason = "short_term"
        elif any(len(t) < MIN_TRIGRAM_CHARS for t in terms):
            reason = "short_alias"
        try:
            with self._lock:
                rows, manual, reason, dbg = self._fetch(terms, reason, m)
        except Exception as exc:  # engine trouble: run A exactly as A would (same errors).
            self.close()
            m["fallback_reason"] = "engine_error:" + type(exc).__name__
            m["accelerated"] = False
            t0 = time.perf_counter_ns()
            result = reference_query(self.index, self.aliases, self.crosswalk, term, page, scope, page_size)
            m["t_sql_total_ms"] = _ms(time.perf_counter_ns() - t0)
            m["t_total_ms"] = _ms(time.perf_counter_ns() - t_start)
            self.last_metrics = m
            return result, m
        m["fallback_reason"] = reason
        m["accelerated"] = reason is None
        t0 = time.perf_counter_ns()
        result = _assemble(term, terms, scope, page, page_size, rows, manual, self.crosswalk)
        t1 = time.perf_counter_ns()
        m["t_post_ms"] = _ms(t1 - t0)
        m["t_total_ms"] = _ms(t1 - t_start)
        m["match_count"] = result["match_count"]
        m["group_count"] = result["group_count"]
        if debug:
            m.update(dbg)
        self.last_metrics = m
        return result, m

    def _fetch(self, terms, reason, m):
        dbg = {}
        t0 = time.perf_counter_ns()
        db = self._ensure_connection(m)
        t1 = time.perf_counter_ns()
        m["t_connect_ms"] = _ms(t1 - t0)
        db.execute("BEGIN")
        try:
            token = self._generation_token(db)
            if reason is None and token not in self._verified and self._fts_touched:
                # Fix after dev run 1: an ft vtab that was used in an older generation keeps a
                # stale segment structure, and PRAGMA integrity_check(ft) on it reports a false
                # "checksum mismatch". Verify a new generation on a fresh connection instead;
                # verification and the query then share that connection's single snapshot.
                db.execute("COMMIT")
                self.close()
                db = self._ensure_connection(m)
                m["reconnect_reason"] = "fresh_fts_state_for_verify"
                db.execute("BEGIN")
                token = self._generation_token(db)
            if reason is None:
                self._fts_touched = True
                ok, why, _ = self._generation_status(db, token, m)
                if not ok:
                    reason = why
            t2 = time.perf_counter_ns()
            m["t_generation_ms"] = _ms(t2 - t1)
            where, params = _like_where(terms)
            rows = None
            if reason is None:
                try:
                    candidates = [r[0] for r in db.execute(
                        "SELECT rowid FROM ft WHERE ft MATCH ?", (self._fts_expression(terms),))]
                except sqlite3.Error as exc:
                    reason = "match_error:" + str(exc)
                t3 = time.perf_counter_ns()
                m["t_fts_ms"] = _ms(t3 - t2)
                t2 = t3
                if reason is None:
                    m["fts_candidates"] = len(candidates)
                    sql = ("SELECT rowid AS _rowid," + DOC_COLUMNS + " FROM docs"
                           " WHERE rowid IN (SELECT value FROM json_each(?)) AND (" + where + ")"
                           " ORDER BY rowid")
                    try:
                        fetched = [dict(r) for r in db.execute(sql, [json.dumps(candidates)] + params)]
                    except sqlite3.Error as exc:
                        reason = "candidate_fetch_error:" + str(exc)
                    else:
                        dbg["candidate_rowids"] = candidates
                        dbg["confirmed_rowids"] = [r["_rowid"] for r in fetched]
                        for r in fetched:
                            del r["_rowid"]
                        rows = fetched
                        m["confirmed_rows"] = len(rows)
                        m["false_candidates_removed"] = len(candidates) - len(rows)
            if rows is None:
                # A path: full LIKE scan, same snapshot.
                sql = "SELECT rowid AS _rowid," + DOC_COLUMNS + " FROM docs WHERE " + where
                rows = [dict(r) for r in db.execute(sql, params)]
                dbg["confirmed_rowids"] = [r.pop("_rowid") for r in rows]
                m["confirmed_rows"] = len(rows)
            t3 = time.perf_counter_ns()
            m["t_docs_ms"] = _ms(t3 - t2)
            manual = _manual_rows(db, terms)
            t4 = time.perf_counter_ns()
            m["t_manual_ms"] = _ms(t4 - t3)
            m["t_sql_total_ms"] = _ms(t4 - t0)
        finally:
            if db.in_transaction:
                db.execute("COMMIT")
        return rows, manual, reason, dbg

    def _fts_expression(self, terms):
        return fts_phrase_expression(terms)


# ---------------------------------------------------------------------------
# Module-level API mirroring A: query(term, page=1, scope="all", page_size=12)

_ROOT = Path(__file__).resolve().parent.parent
_default = None
_default_lock = threading.Lock()


def load_bindings(corpus_path):
    with open(corpus_path, encoding="utf-8") as source:
        fixture = json.load(source)
    return fixture["aliases"], fixture["crosswalk"]


def default_engine():
    global _default
    with _default_lock:
        if _default is None:
            index = os.environ.get("ASSET_SEARCH_INDEX",
                                   str(_ROOT / "input" / "SYNTHETIC_DEV_FIXTURE_V01.sqlite"))
            corpus = os.environ.get("ASSET_SEARCH_CORPUS",
                                    str(_ROOT / "input" / "SYNTHETIC_CORPUS_V01.json"))
            aliases, crosswalk = load_bindings(corpus)
            _default = SearchEngine(index, aliases, crosswalk)
        return _default


def query(term, page=1, scope="all", page_size=12):
    return default_engine().query(term, page, scope, page_size)
