#!/usr/bin/env python3
"""ROUTABL AssetSearch v1.8 — 찾기(find) → 발췌(chunk) 2단계 검색.

목표: 10GB 원본에서 필요한 1~2KB 조각만 빠르게 찾아 짧게 전달 (AI 토큰 최소화).
- 파일을 문서는 제목, 코드는 함수 단위의 1~2KB 조각으로 나눠 SQLite FTS5(trigram)로 색인
- /api/find  : 상위 조각의 위치·제목·한 줄 미리보기만 (1KB 안팎)
- /api/chunk : 고른 조각 원문만 (출처 경로:줄 @SHA 포함)
- /api/lines : 원본 파일의 지정 줄 범위 (조각 경계가 잘렸을 때)
- 비밀값(키·비밀번호·토큰·개인키)은 색인하지 않거나 [SECRET]으로 가림
- 단독 실행: 이전 버전 파일·~/Library에 의존하지 않음. 127.0.0.1 전용. 쉬어도 꺼지지 않음.

사용: python3 routabl_search_v1_8.py serve | index [--budget 초] [--only 소스] | find 검색어 | chunk ID | status
환경변수 ROUTABL_BASE: 원본 폴더들의 부모 (기본: 홈 폴더)
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import secrets
import sqlite3
import subprocess
import sys
import threading
import time
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

VERSION = "1.8"
PORT = 8772
HERE = Path(__file__).resolve().parent
DB = Path(os.environ.get("ROUTABL_DB", str(HERE / "index_v1_8.sqlite")))
BASE = Path(os.environ.get("ROUTABL_BASE", str(Path.home())))
TOKEN = secrets.token_urlsafe(24)
MAX_CHUNK = 1800          # 조각 최대 바이트 (UTF-8)
MIN_MERGE = 500           # 이보다 작은 이웃 조각은 합침
MAX_FILE = 2_000_000      # 일반 텍스트 파일 최대 크기

# ---------------------------------------------------------------- 검색 대상
MAIN_PROJECTS = {"DISPATCH-One-Android", "ROUTABL-Senior-Driver", "DailyInspection-Android",
                 "ROUTIVEL-Firebase-Migration", "ROUTABL-Analytics-Android",
                 "ROUTABL-CustomerRegistration-Android"}
TA_DIRS = ("00_GUIDE", "30_REGISTRY", "40_WORKING", "60_AUDIT", "70_EXPORTS", "20_ORIGINALS/NAS-Imported")
GPT_EXPORT = "ROUTABL-ChatGPT-Archive/2026-11-05/00_EXTRACTED_ORIGINAL"
SKIP_DIRS = {".git", ".gradle", ".idea", ".kotlin", "build", "node_modules", "dist", "out", "target",
             "__pycache__", ".venv", "venv", ".cache", "_to_delete", "80_RUNTIME", ".next", "coverage",
             "generated", "Generated", ".DS_Store", "_archive_versions"}
TEXT_EXT = {".kt", ".kts", ".java", ".js", ".mjs", ".cjs", ".ts", ".tsx", ".jsx", ".py", ".swift", ".sh",
            ".command", ".md", ".txt", ".json", ".xml", ".rules", ".gradle", ".properties", ".html",
            ".css", ".yaml", ".yml", ".toml", ".sql", ".plist", ".csv", ".tsv"}
CODE_EXT = {".kt", ".kts", ".java", ".js", ".mjs", ".cjs", ".ts", ".tsx", ".jsx", ".py", ".swift", ".sh", ".gradle"}
DOC_EXT = {".md", ".txt"}

# ---------------------------------------------------------------- 비밀값 차단
SECRET_NAME = re.compile(
    r"(\.(jks|keystore|p12|pfx|pem|key|der|cer|crt|mobileprovision|p8)$)|(^id_(rsa|ed25519|ecdsa|dsa))"
    r"|(^\.env)|(service[-_]?account.*\.json$)|(credential.*\.json$)|(client_secret.*\.json$)"
    r"|(^keystore\.properties$)|(^local\.properties$)|(token.*\.json$)|(^\.netrc$)|(^\.npmrc$)",
    re.I)
SECRET_VALUE = [
    (re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----.*?-----END [A-Z ]*PRIVATE KEY-----", re.S), "[SECRET:PRIVATE_KEY]"),
    (re.compile(r"AIza[0-9A-Za-z_\-]{35}"), "[SECRET:GOOGLE_API_KEY]"),
    (re.compile(r"\bsk-(?:proj-|ant-)?[A-Za-z0-9_\-]{20,}"), "[SECRET:API_KEY]"),
    (re.compile(r"\b(?:ghp|gho|ghs|ghu|github_pat)_[A-Za-z0-9_]{20,}"), "[SECRET:GITHUB_TOKEN]"),
    (re.compile(r"\bxox[abprs]-[A-Za-z0-9\-]{10,}"), "[SECRET:SLACK_TOKEN]"),
    (re.compile(r"\bAKIA[0-9A-Z]{16}\b"), "[SECRET:AWS_KEY]"),
    (re.compile(r"\bya29\.[0-9A-Za-z_\-]{20,}"), "[SECRET:OAUTH_TOKEN]"),
    (re.compile(r"(?i)((?:store|key)?pass(?:word|wd)?|secret|api[_-]?key|private[_-]?key|access[_-]?token|refresh[_-]?token|client[_-]?secret)"
                r"(\s*[:=]\s*[\"']?)([^\"'\s,;]{6,})"), r"\1\2[SECRET]"),
    # Gradle(Groovy) 문법: storePassword 'xxx' / keyPassword "xxx" (= 없이 공백)
    (re.compile(r"(?i)\b((?:store|key)Password|password|secret)(\s+[\"'])([^\"']{4,})([\"'])"), r"\1\2[SECRET]\4"),
]


def redact(text: str) -> str:
    for rx, rep in SECRET_VALUE:
        text = rx.sub(rep, text)
    return text


# ---------------------------------------------------------------- DB
SCHEMA = """
CREATE TABLE IF NOT EXISTS docs(
  id INTEGER PRIMARY KEY, path TEXT UNIQUE NOT NULL, source TEXT NOT NULL, kind TEXT NOT NULL,
  size INTEGER NOT NULL, mtime INTEGER NOT NULL, sha TEXT NOT NULL, title TEXT NOT NULL,
  dup_of INTEGER, n_chunks INTEGER NOT NULL DEFAULT 0, seen INTEGER NOT NULL DEFAULT 0);
CREATE INDEX IF NOT EXISTS docs_sha ON docs(sha);
CREATE TABLE IF NOT EXISTS chunks(
  id INTEGER PRIMARY KEY, doc_id INTEGER NOT NULL, ord INTEGER NOT NULL,
  start_line INTEGER NOT NULL, end_line INTEGER NOT NULL, heading TEXT NOT NULL, bytes INTEGER NOT NULL);
CREATE INDEX IF NOT EXISTS chunks_doc ON chunks(doc_id);
CREATE VIRTUAL TABLE IF NOT EXISTS fts USING fts5(heading, path, body, tokenize='trigram');
CREATE TABLE IF NOT EXISTS meta(key TEXT PRIMARY KEY, value TEXT NOT NULL);
"""


def connect(readonly=False):
    if readonly:
        db = sqlite3.connect("file:" + str(DB) + "?mode=ro", uri=True, timeout=10, check_same_thread=False)
    else:
        db = sqlite3.connect(str(DB), timeout=30)
        db.executescript(SCHEMA)
    db.row_factory = sqlite3.Row
    return db


# ---------------------------------------------------------------- 조각 나누기
CODE_BOUNDARY = re.compile(
    r"^\s{0,4}(?:@\w+(?:\([^)]*\))?\s+)*(?:(?:public|private|internal|protected|override|suspend|inline|data|sealed|"
    r"abstract|open|export|default|async|static|final|lateinit|const|enum|annotation|companion)\s+)*"
    r"(?:fun|class|object|interface|def|function|func|struct|enum|exports\.\w+\s*=|const\s+\w+\s*=\s*(?:async\s*)?\()")


def _bytes(s):
    return len(s.encode("utf-8"))


def split_lines_capped(lines, start, heading):
    """lines(list[str]) → [(start_line, end_line, heading, text)] 각 MAX_CHUNK 이하."""
    out, buf, bstart, size = [], [], start, 0
    for i, line in enumerate(lines):
        lb = _bytes(line) + 1
        if lb > MAX_CHUNK:                      # 한 줄이 너무 길면 잘라서
            line = line.encode("utf-8")[:MAX_CHUNK - 20].decode("utf-8", "ignore") + " …"
            lb = _bytes(line) + 1
        if buf and size + lb > MAX_CHUNK:
            out.append((bstart, bstart + len(buf) - 1, heading, "\n".join(buf)))
            buf, bstart, size = [], start + i, 0
        buf.append(line)
        size += lb
    if buf and "".join(buf).strip():
        out.append((bstart, bstart + len(buf) - 1, heading, "\n".join(buf)))
    return out


def sections(lines, is_boundary, head_of):
    """경계 줄 기준 구간 → 작은 구간 병합 → 큰 구간 분할."""
    marks = [0] + [i for i, l in enumerate(lines) if i > 0 and is_boundary(l)]
    raw = []
    for a, b in zip(marks, marks[1:] + [len(lines)]):
        raw.append([a, b])
    merged = []
    for a, b in raw:
        if merged and _bytes("\n".join(lines[merged[-1][0]:merged[-1][1]])) < MIN_MERGE and \
                _bytes("\n".join(lines[merged[-1][0]:b])) <= MAX_CHUNK:
            merged[-1][1] = b
        else:
            merged.append([a, b])
    out = []
    for a, b in merged:
        out += split_lines_capped(lines[a:b], a + 1, head_of(lines, a))
    return out


def chunk_text(text, ext):
    lines = text.split("\n")
    if ext in DOC_EXT:
        heads = {}
        cur = ""
        for i, l in enumerate(lines):
            if l.startswith("#"):
                cur = l.lstrip("#").strip()[:100]
            heads[i] = cur

        def hd(ls, a):
            return heads.get(a, "")
        return sections(lines, lambda l: l.startswith("#"), hd)
    if ext in CODE_EXT:
        def hd(ls, a):
            for l in ls[a:a + 6]:
                if CODE_BOUNDARY.match(l):
                    return l.strip()[:100]
            return ls[a].strip()[:100] if a < len(ls) else ""
        return sections(lines, lambda l: bool(CODE_BOUNDARY.match(l)), hd)
    return split_lines_capped(lines, 1, "")


def chunk_manifest(text):
    """등록부 JSON: 자산 1건 = 조각 1개, 최상위 항목 = 조각 1개."""
    data = json.loads(text)
    out = []
    for item in data.get("asset_files", []):
        body = json.dumps(item, ensure_ascii=False, indent=0)
        for piece in split_lines_capped(body.split("\n"), 1, str(item.get("asset_id", "")))[:2]:
            out.append((0, 0, piece[2], piece[3]))
    for k, v in data.items():
        if k == "asset_files":
            continue
        body = k + ": " + json.dumps(v, ensure_ascii=False, indent=0)
        for piece in split_lines_capped(body.split("\n"), 1, k)[:3]:
            out.append((0, 0, k, piece[3]))
    return out


# ---------------------------------------------------------------- 파일 목록
def kind_of(path):
    if path.startswith("GPT::"):
        return "gpt"
    if path.startswith("TA::"):
        return "working" if path.startswith("TA::40_WORKING/") else "docs"
    proj = path.split("/")[1] if path.startswith("MAC::StudioProjects/") else ""
    if proj in MAIN_PROJECTS:
        return "test" if "/src/test/" in path or "/src/androidTest/" in path else "main"
    return "variant"


def walk(root: Path, prefix: str):
    if not root.is_dir():
        return
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = sorted(d for d in dirnames if d not in SKIP_DIRS and not d.startswith("."))
        for f in sorted(filenames):
            p = Path(dirpath) / f
            ext = p.suffix.lower()
            if f.startswith(".") or (ext not in TEXT_EXT and ext != ".pdf"):
                continue
            yield prefix + p.relative_to(root).as_posix(), p, ext


def resolve_path(path):
    if path.startswith("MAC::StudioProjects/"):
        return BASE / "StudioProjects" / path[len("MAC::StudioProjects/"):]
    if path.startswith("TA::"):
        return BASE / "ROUTABL-TechAssets" / path[len("TA::"):]
    return None


def latest_manifest_name(reg: Path):
    if (reg / "asset_manifest.json").is_file():      # P2(2026-11-12): 기준 등록부 하나, 버전은 git 이름표
        return "asset_manifest.json"
    best = None
    for p in reg.glob("asset_manifest_v0.*.json"):
        m = re.fullmatch(r"asset_manifest_v0\.(\d+)\.json", p.name)
        if m and (best is None or int(m.group(1)) > best[0]):
            best = (int(m.group(1)), p.name)
    return best[1] if best else None


def file_sources():
    """(path, file, ext) — 메인 프로젝트 먼저 (중복이면 먼저 나온 쪽이 대표)."""
    sp = BASE / "StudioProjects"
    projects = sorted(p.name for p in sp.iterdir() if p.is_dir()) if sp.is_dir() else []
    for name in sorted(projects, key=lambda n: (n not in MAIN_PROJECTS, n)):
        yield from walk(sp / name, "MAC::StudioProjects/" + name + "/")
    ta = BASE / "ROUTABL-TechAssets"
    latest = latest_manifest_name(ta / "30_REGISTRY")
    for d in TA_DIRS:
        for path, p, ext in walk(ta / d, "TA::" + d + "/"):
            if d == "30_REGISTRY" and p.name.startswith("asset_manifest_v0.") and p.name != latest:
                continue          # 등록부는 최신본만 (옛 버전은 같은 내용의 반복)
            yield path, p, ext


# ---------------------------------------------------------------- 색인
class Indexer:
    def __init__(self, db, budget=None):
        self.db = db
        self.deadline = time.monotonic() + budget if budget else None
        self.stats = {"new": 0, "changed": 0, "unchanged": 0, "dup": 0, "secret_skipped": 0,
                      "removed": 0, "chunks": 0, "errors": 0, "timed_out": False}
        self.epoch = int(time.time())

    def out_of_time(self):
        if self.deadline and time.monotonic() > self.deadline:
            self.stats["timed_out"] = True
            return True
        return False

    def drop_chunks(self, doc_id):
        ids = [r[0] for r in self.db.execute("SELECT id FROM chunks WHERE doc_id=?", (doc_id,))]
        self.db.executemany("DELETE FROM fts WHERE rowid=?", [(i,) for i in ids])
        self.db.execute("DELETE FROM chunks WHERE doc_id=?", (doc_id,))

    def upsert_doc(self, path, source, size, mtime, sha, title):
        row = self.db.execute("SELECT id FROM docs WHERE path=?", (path,)).fetchone()
        if row:
            self.drop_chunks(row[0])
            self.db.execute("UPDATE docs SET source=?,kind=?,size=?,mtime=?,sha=?,title=?,dup_of=NULL,n_chunks=0,seen=? WHERE id=?",
                            (source, kind_of(path), size, mtime, sha, title, self.epoch, row[0]))
            return row[0], True
        cur = self.db.execute("INSERT INTO docs(path,source,kind,size,mtime,sha,title,seen) VALUES(?,?,?,?,?,?,?,?)",
                              (path, source, kind_of(path), size, mtime, sha, title, self.epoch))
        return cur.lastrowid, False

    def add_chunks(self, doc_id, path, pieces):
        n = 0
        for ord_, (a, b, head, body) in enumerate(pieces):
            body = redact(body)
            if not body.strip():
                continue
            cur = self.db.execute("INSERT INTO chunks(doc_id,ord,start_line,end_line,heading,bytes) VALUES(?,?,?,?,?,?)",
                                  (doc_id, ord_, a, b, head, _bytes(body)))
            self.db.execute("INSERT INTO fts(rowid,heading,path,body) VALUES(?,?,?,?)", (cur.lastrowid, head, path, body))
            n += 1
        self.db.execute("UPDATE docs SET n_chunks=? WHERE id=?", (n, doc_id))
        self.stats["chunks"] += n

    def index_file(self, path, p: Path, ext):
        try:
            st = p.stat()
        except OSError:
            return
        row = self.db.execute("SELECT id,size,mtime FROM docs WHERE path=?", (path,)).fetchone()
        if row and row["size"] == st.st_size and row["mtime"] == int(st.st_mtime):
            self.db.execute("UPDATE docs SET seen=? WHERE id=?", (self.epoch, row["id"]))
            self.stats["unchanged"] += 1
            return
        if SECRET_NAME.search(p.name):
            self.stats["secret_skipped"] += 1
            return
        if ext != ".pdf" and st.st_size > MAX_FILE:
            return
        raw = p.read_bytes()
        sha = hashlib.sha256(raw).hexdigest()
        doc_id, existed = self.upsert_doc(path, "file", st.st_size, int(st.st_mtime), sha, p.name)
        self.stats["changed" if existed else "new"] += 1
        twin = self.db.execute("SELECT id FROM docs WHERE sha=? AND id<>? AND dup_of IS NULL AND n_chunks>0 LIMIT 1",
                               (sha, doc_id)).fetchone()
        if twin:                                   # 같은 내용은 대표본 하나만 조각으로
            self.db.execute("UPDATE docs SET dup_of=? WHERE id=?", (twin[0], doc_id))
            self.stats["dup"] += 1
            return
        if ext == ".pdf":
            text = redact(pdf_text(p))
            if not text:
                return
            pieces = []
            for pno, page in enumerate(text.split("\f"), 1):
                for a, b, h, body in split_lines_capped(page.split("\n"), 1, "p.%d" % pno):
                    pieces.append((pno, pno, h, body))
        else:
            text = raw.decode("utf-8", "replace")
            if "\x00" in text[:2000]:
                return
            text = redact(text)          # 조각 나누기 전에 파일 전체를 가림 (조각 경계에 걸친 키도 차단)
            if path.startswith("TA::30_REGISTRY/asset_manifest"):
                try:
                    pieces = chunk_manifest(text)
                except ValueError:
                    pieces = chunk_text(text, ext)
            else:
                pieces = chunk_text(text, ext)
        self.add_chunks(doc_id, path, pieces)

    def index_gpt(self):
        root = BASE / GPT_EXPORT
        files = sorted(root.glob("conversations-*.json")) if root.is_dir() else []
        for f in files:
            if self.out_of_time():
                return
            for conv in json.loads(f.read_text(encoding="utf-8")):
                if self.out_of_time():
                    return
                cid = conv.get("conversation_id") or conv.get("id")
                title = (conv.get("title") or "제목 없음").strip()
                upd = int(conv.get("update_time") or conv.get("create_time") or 0)
                path = "GPT::" + cid
                row = self.db.execute("SELECT id,mtime FROM docs WHERE path=?", (path,)).fetchone()
                if row and row["mtime"] == upd:
                    self.db.execute("UPDATE docs SET seen=? WHERE id=?", (self.epoch, row["id"]))
                    self.stats["unchanged"] += 1
                    continue
                msgs = thread_messages(conv)
                body_all = "\n".join(m[2] for m in msgs)
                sha = hashlib.sha256(body_all.encode("utf-8")).hexdigest()
                date = time.strftime("%Y-%m-%d", time.localtime(conv.get("create_time") or 0))
                doc_id, existed = self.upsert_doc(path, "gpt", len(body_all), upd, sha, date + " " + title)
                self.stats["changed" if existed else "new"] += 1
                pieces = []
                for no, (role, when, text) in enumerate(msgs, 1):
                    text = redact(text)
                    head = "%s · %s · #%d %s" % (title[:60], date, no, "나" if role == "user" else "GPT")
                    for a, b, h, body in split_lines_capped(text.split("\n"), 1, head):
                        pieces.append((no, no, h, body))
                self.add_chunks(doc_id, path, pieces)
            self.db.commit()

    def run(self, only=None):
        self.db.execute("UPDATE docs SET dup_of=NULL, size=-1 WHERE dup_of IS NOT NULL AND dup_of NOT IN (SELECT id FROM docs)")
        if only in (None, "files"):
            for path, p, ext in file_sources():
                if self.out_of_time():
                    break
                try:
                    self.index_file(path, p, ext)
                except Exception:
                    self.stats["errors"] += 1
                self.pending = getattr(self, "pending", 0) + 1
                if self.pending % 300 == 0:
                    self.db.commit()
            self.db.commit()
            if not self.stats["timed_out"]:          # 사라진 파일 정리 (전체 순회를 마쳤을 때만)
                orphans = []
                for r in self.db.execute("SELECT id FROM docs WHERE source='file' AND seen<?", (self.epoch,)).fetchall():
                    # 지워지는 대표본에 기대던 중복본은 다시 색인 (대표본이 사라져도 내용이 검색에서 빠지지 않게)
                    orphans += [x[0] for x in self.db.execute("SELECT path FROM docs WHERE dup_of=?", (r[0],))]
                    self.db.execute("UPDATE docs SET dup_of=NULL, size=-1 WHERE dup_of=?", (r[0],))
                    self.drop_chunks(r[0])
                    self.db.execute("DELETE FROM docs WHERE id=?", (r[0],))
                    self.stats["removed"] += 1
                for path in orphans:
                    p = resolve_path(path)
                    if p is not None and p.is_file():
                        self.index_file(path, p, p.suffix.lower())
                self.db.commit()
        if only in (None, "gpt") and not self.stats["timed_out"]:
            self.index_gpt()
        self.db.execute("INSERT OR REPLACE INTO meta VALUES('last_index', ?)", (time.strftime("%Y-%m-%d %H:%M:%S"),))
        self.db.execute("INSERT OR REPLACE INTO meta VALUES('last_stats', ?)", (json.dumps(self.stats),))
        self.db.commit()
        return self.stats


def thread_messages(conv):
    """현재 대화 흐름(current_node → 루트)의 user/assistant 메시지만."""
    mapping = conv.get("mapping") or {}
    node, chain = conv.get("current_node"), []
    while node and node in mapping:
        chain.append(mapping[node])
        node = mapping[node].get("parent")
    out = []
    for n in reversed(chain):
        m = n.get("message") or {}
        role = (m.get("author") or {}).get("role")
        if role not in ("user", "assistant"):
            continue
        c = m.get("content") or {}
        parts = c.get("parts") or ([c.get("text")] if c.get("text") else [])
        text = "\n".join(p for p in parts if isinstance(p, str)).strip()
        if text:
            out.append((role, m.get("create_time"), text))
    return out


def pdf_text(p: Path):
    for tool in ("/usr/bin/pdftotext", "/opt/homebrew/bin/pdftotext", "/usr/local/bin/pdftotext"):
        if os.path.exists(tool):
            try:
                return subprocess.run([tool, "-layout", str(p), "-"], capture_output=True, timeout=60).stdout.decode("utf-8", "replace")
            except Exception:
                return ""
    return ""          # Mac에 pdftotext가 없으면 이전 색인의 PDF 조각을 그대로 유지 (크기·시각이 같으면 건너뜀)


# ---------------------------------------------------------------- 검색
ALIASES = {
    "정산": ["Settlement", "월간정산"], "시니어": ["Senior"], "기사앱": ["DISPATCH-One-Android"],
    "고객등록앱": ["CustomerRegistration", "customerreg"], "고객등록": ["CustomerRegistration", "saveShared"],
    "행정동": ["adminDong"], "초성": ["chosung", "Chosung", "KoreanSearch"], "주소록": ["customerDirectory", "CustomerDirectory"],
    "분석앱": ["Analytics"], "일상점검": ["DailyInspection"], "분업": ["DW-01"], "백서": ["Whitepaper", "백서"],
    "등록부": ["asset_manifest"], "보안규칙": ["firestore.rules"], "관리자": ["isAdmin", "admin"],
}
KIND_BOOST = {"main": 2.0, "docs": 1.5, "test": 0.0, "working": -0.5, "gpt": -0.5, "variant": -2.5}
_ASSETS = {"name": None, "map": {}}


def asset_map():
    """최신 등록부: 경로 → [(sha, asset_id)] — SHA가 같을 때만 자산 ID 표시."""
    reg = BASE / "ROUTABL-TechAssets/30_REGISTRY"
    name = latest_manifest_name(reg)
    if name and name != _ASSETS["name"]:
        m = {}
        try:
            data = json.loads((reg / name).read_text(encoding="utf-8"))
            home = str(Path.home())
            for it in data.get("asset_files", []):
                p, sha = it.get("observed_original_path") or "", it.get("sha256")
                for real, pre in ((home + "/StudioProjects/", "MAC::StudioProjects/"), (home + "/ROUTABL-TechAssets/", "TA::"),
                                  ("/Users/yongho/StudioProjects/", "MAC::StudioProjects/"), ("/Users/yongho/ROUTABL-TechAssets/", "TA::")):
                    if p.startswith(real):
                        m.setdefault(pre + p[len(real):], []).append((sha, it.get("asset_id")))
                        break
        except (OSError, ValueError):
            pass
        _ASSETS.update(name=name, map=m)
    return _ASSETS["map"]


def fts_phrase(t):
    return '"' + t.replace('"', '""') + '"'


def preview(body, terms, width=70):
    low = body.lower()
    pos = min([i for i in (low.find(t.lower()) for t in terms) if i >= 0] or [0])
    s = body[max(0, pos - width // 3): pos + width]
    return re.sub(r"\s+", " ", s).strip()


def find(q, k=5, scope="all"):
    q = q.strip()[:120]
    words = [w for w in re.split(r"\s+", q) if w]
    if not words:
        raise ValueError("검색어를 입력하세요")
    k = max(1, min(int(k), 20))
    groups = [[w] + ALIASES.get(w, []) for w in words]
    long_groups = [[t for t in g if len(t) >= 3] for g in groups] if all(len(w) >= 3 for w in words) else [[]]
    db = connect(readonly=True)
    rows = []
    try:
        if all(long_groups):                  # 모든 단어가 3글자 이상(또는 별명 있음) → 색인 검색
            expr = " AND ".join("(" + " OR ".join(fts_phrase(t) for t in g) + ")" for g in long_groups)
            rows = db.execute("SELECT rowid, heading, path, body, bm25(fts, 6.0, 3.0, 1.0) AS r FROM fts WHERE fts MATCH ? "
                              "ORDER BY r LIMIT 400", (expr,)).fetchall()
            if not rows and len(long_groups) > 1:   # 모두 포함이 없으면 하나라도
                expr = " OR ".join(fts_phrase(t) for g in long_groups for t in g)
                rows = db.execute("SELECT rowid, heading, path, body, bm25(fts, 6.0, 3.0, 1.0) AS r FROM fts WHERE fts MATCH ? "
                                  "ORDER BY r LIMIT 400", (expr,)).fetchall()
        else:                                 # 2글자 단어 → LIKE (전체 훑기, 그래도 1초 안팎)
            cond = " AND ".join("(" + " OR ".join(["body LIKE ?", "heading LIKE ?", "path LIKE ?"] * len(g)) + ")" for g in groups)
            params = []
            for g in groups:
                for t in g:
                    params += ["%" + t + "%"] * 3
            # 제목·경로에 맞는 조각을 먼저 가져오고, 후보를 넉넉히 (SQLite 버전마다 훑는 순서가 달라도 같은 결과)
            first = groups[0][0]
            rows = db.execute("SELECT rowid, heading, path, body, 0.0 AS r FROM fts WHERE " + cond +
                              " ORDER BY (heading LIKE ?) + (path LIKE ?) DESC LIMIT 5000",
                              params + ["%" + first + "%", "%" + first + "%"]).fetchall()
            if not rows and len(groups) > 1:   # 모두 포함이 없으면 하나라도 (많이 맞을수록 위로)
                cond = " OR ".join("(" + " OR ".join(["body LIKE ?", "heading LIKE ?"] * len(g)) + ")" for g in groups)
                params = []
                for g in groups:
                    for t in g:
                        params += ["%" + t + "%"] * 2
                rows = db.execute("SELECT rowid, heading, path, body, 0.0 AS r FROM fts WHERE " + cond + " LIMIT 3000", params).fetchall()
        assets = asset_map()
        flat = [t for g in groups for t in g]
        scored = []
        for r in rows:
            path = r["path"]
            kind = kind_of(path)
            if scope != "all" and kind != scope and not (scope == "code" and kind in ("main", "test")):
                continue
            score = -float(r["r"]) + KIND_BOOST.get(kind, 0)
            low_h, low_p = r["heading"].lower(), path.lower()
            score += sum(2.0 for t in flat if t.lower() in low_h) + sum(1.0 for t in flat if t.lower() in low_p)
            low_b = r["body"].lower()
            score += 4.0 * sum(1 for g in groups if any(t.lower() in low_b or t.lower() in low_h for t in g))
            scored.append([score, r])
        scored.sort(key=lambda x: -x[0])
        hits, per_doc = [], {}
        meta = {}
        for score, r in scored:
            if per_doc.get(r["path"], 0) >= 2:      # 한 파일에서 최대 2조각 → 다양성
                continue
            c = db.execute("SELECT c.start_line, c.end_line, d.sha, d.kind FROM chunks c JOIN docs d ON d.id=c.doc_id WHERE c.id=?",
                           (r["rowid"],)).fetchone()
            if c is None:
                continue
            per_doc[r["path"]] = per_doc.get(r["path"], 0) + 1
            aid = next((a for s, a in assets.get(r["path"], []) if s == c["sha"]), None)
            hit = {"id": r["rowid"], "p": r["path"], "L": "%d-%d" % (c["start_line"], c["end_line"]),
                   "h": r["heading"][:80], "s": preview(r["body"], flat)}
            if aid:
                hit["a"] = aid
            hits.append(hit)
            if len(hits) >= k:
                break
        return {"q": q, "n": len(scored), "hits": hits}
    finally:
        db.close()


def chunk(cid, neighbors=0):
    db = connect(readonly=True)
    try:
        c = db.execute("SELECT c.id, c.doc_id, c.ord, c.start_line, c.end_line, c.heading, d.path, d.sha FROM chunks c "
                       "JOIN docs d ON d.id=c.doc_id WHERE c.id=?", (int(cid),)).fetchone()
        if not c:
            raise KeyError("조각 없음")
        lo, hi = c["ord"] - int(neighbors), c["ord"] + int(neighbors)
        parts = db.execute("SELECT c.id, f.body FROM chunks c JOIN fts f ON f.rowid=c.id WHERE c.doc_id=? AND c.ord BETWEEN ? AND ? "
                           "ORDER BY c.ord", (c["doc_id"], lo, hi)).fetchall()
        prev_ = db.execute("SELECT id FROM chunks WHERE doc_id=? AND ord<? ORDER BY ord DESC LIMIT 1", (c["doc_id"], lo)).fetchone()
        next_ = db.execute("SELECT id FROM chunks WHERE doc_id=? AND ord>? ORDER BY ord LIMIT 1", (c["doc_id"], hi)).fetchone()
        aid = next((a for s, a in asset_map().get(c["path"], []) if s == c["sha"]), None)
        head = "# %s:%d-%d @%s%s | %s" % (c["path"], c["start_line"], c["end_line"], c["sha"][:12],
                                         (" | " + aid) if aid else "", c["heading"][:80])
        nav = "# 이전=%s 다음=%s" % (prev_[0] if prev_ else "-", next_[0] if next_ else "-")
        body = "\n".join(p["body"] for p in parts)
        cap = MAX_CHUNK * (1 + 2 * int(neighbors)) + 200
        if _bytes(body) > cap:
            body = body.encode("utf-8")[:cap].decode("utf-8", "ignore") + "\n…(잘림)"
        return head + "\n" + nav + "\n" + body
    finally:
        db.close()


def source_lines(path, a, b):
    """원본 파일의 줄 범위 (최대 120줄, 4KB). MAC::/TA:: 경로만."""
    if path.startswith("MAC::StudioProjects/"):
        root, rel = BASE / "StudioProjects", path[len("MAC::StudioProjects/"):]
    elif path.startswith("TA::"):
        root, rel = BASE / "ROUTABL-TechAssets", path[len("TA::"):]
    else:
        raise ValueError("원본 줄 보기는 파일 경로만 가능")
    target = (root / rel).resolve()
    if not str(target).startswith(str(root.resolve()) + os.sep) or SECRET_NAME.search(target.name):
        raise ValueError("허용되지 않은 경로")
    a, b = max(1, int(a)), int(b)
    b = min(b, a + 119)
    lines = target.read_text(encoding="utf-8", errors="replace").split("\n")[a - 1:b]
    body = redact("\n".join(lines))
    if _bytes(body) > 4096:
        body = body.encode("utf-8")[:4096].decode("utf-8", "ignore") + "\n…(잘림)"
    return "# %s:%d-%d\n%s" % (path, a, a + len(lines) - 1, body)


def status():
    out = {"service": "ROUTABL_ASSET_SEARCH", "version": VERSION, "db": str(DB), "refresh": REFRESH["state"],
           "refresh_error": REFRESH["error"]}
    if DB.exists():
        db = connect(readonly=True)
        try:
            out["docs"] = db.execute("SELECT COUNT(*) FROM docs").fetchone()[0]
            out["chunks"] = db.execute("SELECT COUNT(*) FROM chunks").fetchone()[0]
            out["by_kind"] = {r[0]: r[1] for r in db.execute("SELECT kind, COUNT(*) FROM docs GROUP BY kind")}
            for k, v in db.execute("SELECT key, value FROM meta"):
                out[k] = json.loads(v) if v.startswith("{") else v
        finally:
            db.close()
    out["registry"] = _ASSETS["name"] or latest_manifest_name(BASE / "ROUTABL-TechAssets/30_REGISTRY")
    return out


# ---------------------------------------------------------------- 새로 고침 (서비스 안에서)
REFRESH = {"state": "idle", "error": None}
REFRESH_LOCK = threading.Lock()


def refresh_worker():
    """복사본에서 증분 색인 → 원자적 교체. 검색 중인 연결은 이전 파일을 계속 씀."""
    tmp = DB.with_name(DB.name + ".building")
    try:
        if tmp.exists():
            tmp.unlink()
        if DB.exists():
            with sqlite3.connect("file:" + str(DB) + "?mode=ro", uri=True) as src, sqlite3.connect(str(tmp)) as dst:
                src.backup(dst)
        db = sqlite3.connect(str(tmp), timeout=30)
        db.executescript(SCHEMA)
        db.row_factory = sqlite3.Row
        Indexer(db).run()
        db.close()
        os.replace(tmp, DB)
        REFRESH.update(state="complete", error=None)
    except Exception as e:  # noqa: BLE001
        REFRESH.update(state="failed", error=type(e).__name__ + ": " + str(e)[:200])


# ---------------------------------------------------------------- HTTP
PAGE = """<!doctype html><html lang="ko"><head><meta charset="utf-8"><title>라우터블 기술자산 검색 v1.8</title>
<meta name="viewport" content="width=device-width,initial-scale=1">
<style nonce="__N__">body{font:15px -apple-system,sans-serif;margin:0;background:#f6f7f9;color:#1d2433}
main{max-width:980px;margin:auto;padding:20px}h1{font-size:20px;color:#1f3a68}form{display:flex;gap:8px}
input{flex:1;font-size:16px;padding:10px;border:1px solid #c9d1de;border-radius:8px}button{padding:10px 14px;border:0;border-radius:8px;background:#1f3a68;color:#fff}
.hit{background:#fff;border:1px solid #e1e6ee;border-radius:8px;padding:10px 12px;margin:8px 0;cursor:pointer}
.p{color:#55607a;font-size:12px;word-break:break-all}.h{font-weight:600}.a{color:#0a7a5a;font-size:12px}
pre{white-space:pre-wrap;background:#0f1726;color:#e6edf7;padding:12px;border-radius:8px;font-size:12.5px}#st{color:#55607a;font-size:13px;margin:8px 0}</style></head>
<body><main><h1>라우터블 기술자산 검색 v1.8 · 찾기 → 발췌</h1>
<form id="f"><input id="q" placeholder="예: 행정동, saveShared, 고객등록앱 중복" autofocus><button>찾기</button><button type="button" id="r">색인 새로 고침</button></form>
<div id="st"></div><div id="out"></div><pre id="c" hidden></pre></main>
<script nonce="__N__">const T="__T__";const $=id=>document.getElementById(id);
function el(t,c,x){const e=document.createElement(t);if(c)e.className=c;if(x)e.textContent=x;return e}
$('f').onsubmit=async e=>{e.preventDefault();$('c').hidden=true;const r=await fetch('/api/find?k=10&q='+encodeURIComponent($('q').value));const j=await r.json();
$('out').replaceChildren();if(j.error){$('st').textContent=j.error;return}$('st').textContent='일치 '+j.n+'개 조각';
for(const h of j.hits){const d=el('div','hit');d.append(el('div','h',h.h||'(제목 없음)'),el('div','p',h.p+' : '+h.L));if(h.a)d.append(el('div','a','자산 '+h.a));d.append(el('div','',h.s));
d.onclick=async()=>{const t=await (await fetch('/api/chunk?id='+h.id)).text();$('c').textContent=t;$('c').hidden=false;$('c').scrollIntoView()};$('out').append(d)}};
async function st(){const j=await (await fetch('/api/status')).json();$('st').textContent='조각 '+(j.chunks||0).toLocaleString()+'개 · 파일 '+(j.docs||0).toLocaleString()+'개 · 마지막 색인 '+(j.last_index||'-')+' · 새로 고침 '+j.refresh;return j}
$('r').onclick=async()=>{const r=await fetch('/api/refresh',{method:'POST',headers:{'X-ROUTABL-Request':T}});$('st').textContent=r.ok?'색인 갱신 중…':'갱신 시작 실패';
const t=setInterval(async()=>{const j=await st();if(j.refresh!=='running')clearInterval(t)},2000)};st();</script></body></html>"""


class App(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.0"

    def allowed(self):
        return self.headers.get("Host") in ("127.0.0.1:%d" % PORT, "localhost:%d" % PORT)

    def send(self, code, body, ctype="application/json; charset=utf-8", nonce=None):
        data = body.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        csp = "default-src 'none'; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'"
        if nonce:
            csp += "; script-src 'nonce-%s'; style-src 'nonce-%s'" % (nonce, nonce)
        self.send_header("Content-Security-Policy", csp)
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        if not self.allowed():
            return self.send(403, '{"error":"host"}')
        u = urllib.parse.urlsplit(self.path)
        a = {k: v[0] for k, v in urllib.parse.parse_qs(u.query).items()}
        try:
            if u.path == "/":
                n = secrets.token_urlsafe(12)
                return self.send(200, PAGE.replace("__N__", n).replace("__T__", TOKEN), "text/html; charset=utf-8", n)
            if u.path == "/api/find":
                return self.send(200, json.dumps(find(a.get("q", ""), a.get("k", 5), a.get("scope", "all")), ensure_ascii=False, separators=(",", ":")))
            if u.path == "/api/chunk":
                return self.send(200, chunk(a.get("id", "0"), min(int(a.get("n", 0)), 2)), "text/plain; charset=utf-8")
            if u.path == "/api/lines":
                a1, _, b1 = a.get("L", "1-60").partition("-")
                return self.send(200, source_lines(a.get("p", ""), a1, b1 or a1), "text/plain; charset=utf-8")
            if u.path == "/api/status":
                return self.send(200, json.dumps(status(), ensure_ascii=False))
            if u.path == "/api/help":
                return self.send(200, HELP, "text/plain; charset=utf-8")
            return self.send(404, '{"error":"not found"}')
        except (ValueError, KeyError) as e:
            return self.send(400, json.dumps({"error": str(e)}, ensure_ascii=False))
        except Exception as e:  # noqa: BLE001
            return self.send(500, json.dumps({"error": type(e).__name__}, ensure_ascii=False))

    def do_POST(self):
        if not self.allowed() or self.path != "/api/refresh":
            return self.send(404, '{"error":"not found"}')
        if not secrets.compare_digest(self.headers.get("X-ROUTABL-Request", ""), TOKEN):
            return self.send(403, '{"error":"token"}')
        with REFRESH_LOCK:
            if REFRESH["state"] == "running":
                return self.send(409, '{"ok":false,"state":"running"}')
            REFRESH.update(state="running", error=None)
        threading.Thread(target=refresh_worker, daemon=True).start()
        return self.send(202, '{"ok":true}')

    def log_message(self, *args):
        pass


HELP = """라우터블 기술자산 검색 v1.8 — AI용 사용법 (토큰 절약)
1) GET /api/find?q=검색어&k=5[&scope=main|docs|gpt|working|variant|test|code]
   → {"n":전체, "hits":[{"id","p":경로,"L":줄,"h":제목/함수,"a":자산ID,"s":미리보기}]}
   여러 단어는 모두 포함(AND). 2글자 단어도 가능.
2) GET /api/chunk?id=조각ID[&n=1]  → 그 조각 원문만 (n=1이면 앞뒤 1조각 포함). 첫 줄: 경로:줄 @SHA | 자산ID
3) GET /api/lines?p=경로&L=120-180 → 원본 파일의 줄 범위 (조각 경계가 잘렸을 때, 최대 120줄)
4) GET /api/status → 색인 상태
원칙: find로 위치를 고르고, 필요한 조각만 chunk로 읽는다. 파일 전체를 읽지 않는다.
"""


def serve():
    lock = DB.with_name("server_v1_8.lock")
    import fcntl
    fd = os.open(str(lock), os.O_RDWR | os.O_CREAT, 0o600)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        print("ALREADY_RUNNING", flush=True)
        return 0
    if not DB.exists():
        REFRESH.update(state="running")
        refresh_worker()
    srv = ThreadingHTTPServer(("127.0.0.1", PORT), App)
    srv.daemon_threads = True

    def watch_self():
        """이 파일이 바뀌면 종료 → LaunchAgent(KeepAlive)가 새 코드로 다시 시작. 원격 업데이트용."""
        me = Path(__file__).resolve()
        first = me.stat().st_mtime
        while True:
            time.sleep(10)
            try:
                if me.stat().st_mtime != first:
                    print("CODE_CHANGED_RESTART", flush=True)
                    os._exit(3)
            except OSError:
                pass
    threading.Thread(target=watch_self, daemon=True).start()
    print("ROUTABL_ASSET_SEARCH_V1_8_READY http://127.0.0.1:%d/" % PORT, flush=True)
    srv.serve_forever(poll_interval=0.5)
    return 0


def main(argv):
    if not argv or argv[0] == "serve":
        return serve()
    cmd = argv[0]
    if cmd == "index":
        budget = float(argv[argv.index("--budget") + 1]) if "--budget" in argv else None
        only = argv[argv.index("--only") + 1] if "--only" in argv else None
        db = connect()
        stats = Indexer(db, budget).run(only)
        db.close()
        print(json.dumps(stats, ensure_ascii=False))
    elif cmd == "find":
        print(json.dumps(find(" ".join(argv[1:])), ensure_ascii=False, indent=1))
    elif cmd == "chunk":
        print(chunk(argv[1], int(argv[2]) if len(argv) > 2 else 0))
    elif cmd == "status":
        print(json.dumps(status(), ensure_ascii=False, indent=1))
    else:
        print(__doc__)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
