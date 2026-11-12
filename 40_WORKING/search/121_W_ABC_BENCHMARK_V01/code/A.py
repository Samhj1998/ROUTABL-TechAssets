#!/usr/bin/env python3
"""ROUTABL AssetSearch v1.5: accurate ranked local search and provenance views.
Separate from v1.4. Reuses its independently tested refresh/lifecycle guard.
No source execution, no remote access, no automatic scheduled jobs.
"""
from __future__ import annotations
import fcntl
import importlib.util
import json
import math
import os
import re
import secrets
import sqlite3
import subprocess
import threading
import time
import urllib.parse
from collections import defaultdict
from http.server import ThreadingHTTPServer
from pathlib import Path
from typing import Any

STORE = Path.home() / "Library/Application Support/ROUTABL-AssetSearch"
PROJECT_ROOT = Path.home() / "StudioProjects"
MANIFEST = Path.home() / "ROUTABL-TechAssets/30_REGISTRY/asset_manifest_v0.6.json"
V14 = STORE / "routabl_search_v1_4_service.py"
SERVICE = "ROUTABL_ASSET_SEARCH_V1_5"
PORT = 8769
URL = "http://127.0.0.1:" + str(PORT)
INDEX = STORE / "assets_v1_5.sqlite"
BASELINE = STORE / "assets_v1_4.sqlite"
PREVIOUS = STORE / "assets_v1_5.previous.sqlite"
MAIN_PROJECTS = ("DISPATCH-One-Android", "ROUTABL-Senior-Driver",
                 "ROUTIVEL-Customer-Android", "DailyInspection-Android",
                 "ROUTIVEL-Firebase-Migration")
PROJECTS = MAIN_PROJECTS + ("ROUTABL-Control-Public-20261020",
  "ROUTABL-Integration-Audit-20261019", "ROUTABL-Dispatch-Search-20261019")
SCOPE = {"all", "main", "variants", "nas"}
ALIASES = {
    "정산": ("월간정산", "Settlement"),
    "시니어": ("Senior",),
    "기사앱": ("DISPATCH-One-Android",),
    "고객앱": ("ROUTIVEL-Customer-Android",),
    "초성검색": ("SEARCH-01",),
    "고객등록": ("DATA-01", "cloud_access.py"),
    "주소등록": ("DATA-01", "cloud_access.py"),
    "취소상태": ("TransportStatusPolicy", "F1"),
    "완료 취소": ("TransportStatusPolicy", "transportStatusUndo"),
    "월간정산": ("MonthlySettlement", "월간정산"),
}
spec = importlib.util.spec_from_file_location("routabl_search_v14_core", V14)
core = importlib.util.module_from_spec(spec)
spec.loader.exec_module(core)
core.PORT = PORT
core.URL = URL
core.ACTIVE = INDEX
core.BASELINE = BASELINE
core.PREVIOUS = PREVIOUS
core.SERVICE = SERVICE

def resolve_crosswalk():
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    if data.get("schema_version") != "0.6":
        raise RuntimeError("UNEXPECTED_ASSET_REGISTER_VERSION")
    items = {}
    for item in data.get("provenance_crosswalk", []):
        p = Path(item["mac_original_path"])
        try:
            rel = p.relative_to(PROJECT_ROOT).as_posix()
        except ValueError:
            continue
        items["MAC::StudioProjects/" + rel] = {
            "asset_id": item["asset_id"],
            "sha256": item["mac_sha256"],
            "github_repository": item.get("github_repository"),
            "github_file_path": item.get("github_file_path"),
            "nas_copy": item.get("nas_independent_copy_path"),
            "github_verified": item.get("github_remote_file_verified", "").startswith("YES_"),
            "nas_verified": item.get("nas_status") == "DIRECT_SOURCE_SHA256_MATCH",
        }
    return items

CROSSWALK = resolve_crosswalk()

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

def relevant(row, terms):
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
        # Reward a curated source only if its filename/title/path actually
        # matches the query, not an incidental mention buried in its content.
        direct = any(t.casefold() in path or t.casefold() in title for t in terms)
        if direct and path.startswith("02_핵심기술/"):
            score += 85
        elif path.startswith("00_인계와기준/"):
            score -= 14
        elif path.startswith("ROUTABL_Whitepaper_Archive_"):
            score -= 18
    elif category == "zip":
        # A filename found inside a ZIP is not a directly usable original.
        score -= 135
    if row["path"] in CROSSWALK and CROSSWALK[row["path"]]["sha256"] == row["sha"]:
        # A SHA-verified, explicitly registered original outranks copies with
        # more keyword hits in automatic titles. Authority is not popularity.
        score += 160
    if row["status"] == "OK":
        score += 7
    if "/src/test/" in path or "/src/androidtest/" in path:
        score -= 24
    if "v0.4" in file_name:
        score += 3
    # Content-only matches stay below filename/path matches but are still searchable.
    return score

def query(term, page=1, scope="all", page_size=12):
    term = str(term).strip()
    if not 2 <= len(term) <= 80:
        raise ValueError("검색어는 2~80자로 입력하세요.")
    if scope not in SCOPE:
        raise ValueError("검색 범위가 올바르지 않습니다.")
    page = max(1, min(int(page), 1000))
    page_size = max(1, min(int(page_size), 20))
    terms = [term] + [t for t in ALIASES.get(term, ()) if t.casefold() != term.casefold()]
    expressions = []
    params = []
    for t in terms:
        for col in ("path", "title", "tags", "content"):
            expressions.append(col + " LIKE ? ESCAPE '!'")
            params.append(safe_like(t))
    sql = ("SELECT path,title,tags,sha,status,kind,carrier,sz,mtime_ns FROM docs WHERE " +
           " OR ".join(expressions))
    with sqlite3.connect("file:" + str(INDEX) + "?mode=ro", uri=True, timeout=8) as db:
        db.row_factory = sqlite3.Row
        rows = [dict(row) for row in db.execute(sql, params)]
        manual = []
        for row in db.execute("SELECT id,title,tags,path,source_grade,validation_grade,details FROM manual"):
            info = dict(row)
            compare = " ".join(str(v) for v in info.values()).casefold()
            if any(t.casefold() in compare for t in terms):
                manual.append(info)
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

def reveal_path(index_path):
    prefix = "MAC::StudioProjects/"
    if not isinstance(index_path, str) or not index_path.startswith(prefix):
        raise ValueError("Only indexed Mac project files can be revealed")
    rel = index_path.removeprefix(prefix)
    parts = rel.split("/")
    if (len(parts) < 2 or parts[0] not in PROJECTS or
        any(part in ("", "..", ".") for part in parts) or "\x00" in rel):
        raise ValueError("Invalid source path")
    with sqlite3.connect("file:" + str(INDEX) + "?mode=ro", uri=True, timeout=5) as db:
        r = db.execute("SELECT carrier FROM docs WHERE path=?", (index_path,)).fetchone()
    if not r or r[0] not in ("MAC_PROJECTS_ALLOWLIST_V1_3",
                          "MAC_STUDIOPROJECTS_EXPLICIT_ALLOWLIST"):
        raise ValueError("Not present in trusted local index")
    target = (PROJECT_ROOT / rel).resolve(strict=True)
    base = (PROJECT_ROOT / parts[0]).resolve(strict=True)
    if not target.is_relative_to(base) or not target.is_file():
        raise ValueError("File is outside approved project or missing")
    return target

class App(core.App):
    def do_GET(self):
        global _unused
        if urllib.parse.urlsplit(self.path).path != "/api":
            return super().do_GET()
        if not self.allowed():
            self.respond(403, '{"error":"host"}')
            return
        core.LAST_ACTIVITY = time.monotonic()
        args = urllib.parse.parse_qs(urllib.parse.urlsplit(self.path).query)
        term = args.get("q", [""])[0]
        try:
            page = int(args.get("page", ["1"])[0])
            scope = args.get("scope", ["all"])[0]
            result = query(term, page, scope)
            self.respond(200, json.dumps(result, ensure_ascii=False))
        except (ValueError, TypeError):
            self.respond(400, '{"error":"invalid query or page"}')
        except Exception:
            self.respond(500, '{"error":"index read error"}')

    def do_POST(self):
        if self.path != "/api/reveal":
            return super().do_POST()
        if not self.allowed():
            self.respond(403, '{"error":"host"}')
            return
        origin = self.headers.get("Origin", "")
        token = self.headers.get("X-ROUTABL-Request", "")
        if origin != URL or not secrets.compare_digest(token, core.TOKEN):
            self.respond(403, '{"error":"authorization required"}')
            return
        try:
            size = int(self.headers.get("Content-Length", "0"))
            if not 1 <= size <= 1024:
                raise ValueError("invalid body length")
            body = json.loads(self.rfile.read(size).decode("utf-8"))
            target = reveal_path(body.get("path"))
        except (ValueError, OSError, UnicodeError, KeyError, TypeError):
            self.respond(400, '{"error":"not an approved indexed local file"}')
            return
        core.LAST_ACTIVITY = time.monotonic()
        try:
            subprocess.Popen(
                ["/usr/bin/open", "-R", str(target)],
                stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL, start_new_session=True)
            self.respond(200, '{"ok":true}')
        except OSError:
            self.respond(500, '{"error":"Finder could not be opened"}')


def ui_page():
    page = """<!doctype html><html lang="ko"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>라우터블 기술자산 검색 v1.5</title>
<style nonce="__NONCE__">
:root{font-family:-apple-system,BlinkMacSystemFont,"Apple SD Gothic Neo",sans-serif;
color:#183746;background:#f3f7f9}
body{margin:0}main{max-width:1000px;margin:28px auto;padding:0 20px}
h1{font-size:26px;color:#123853;margin-bottom:6px}p{line-height:1.5}
header,.search,.controls,.pagination{display:flex;flex-wrap:wrap;gap:10px;align-items:center}
header{justify-content:space-between}
.search{margin:18px 0 10px}
input{flex:1;min-width:150px;border:1px solid #b8ccd5;border-radius:9px;padding:12px;font-size:16px}
button,select{border:1px solid #a6c0c9;background:#eef6f7;color:#19485a;border-radius:8px;padding:9px 12px;font-size:14px}
button.primary{background:#136f7d;color:white;border:none}
button:disabled{opacity:.45}
.controls{margin-bottom:14px}
.status{font-size:13px;color:#536f7b;min-height:20px}
.result{background:white;border:1px solid #dbe7eb;border-radius:11px;margin:10px 0;padding:15px 17px}
.result strong{font-size:16px}small{display:block;font-size:12px;color:#58707c;margin-top:5px;overflow-wrap:anywhere}
.chip{display:inline-block;background:#e4f0f3;color:#13596c;padding:3px 7px;border-radius:7px;font-size:12px;margin:7px 7px 0 0}
a{color:#136477}details{margin-top:9px;font-size:13px;color:#446777}
details summary{cursor:pointer}
h2{font-size:17px;margin:22px 0 9px}footer{font-size:12px;color:#71838b;margin:28px 0}
.pagination{justify-content:space-between;margin:20px 0}
</style></head><body><main>
<header><div><h1>라우터블 기술자산 통합검색</h1>
<p>Mac 원본 · NAS 보존자료 · 검증된 GitHub 계보를 찾습니다.</p></div>
<button id="refresh">검색 목록 새로 고침</button></header>
<form class="search" id="search">
<input id="query" placeholder="정산, 시니어, TransportStatusPolicy, 초성검색 등" autocomplete="off" autofocus>
<button class="primary">검색</button></form>
<div class="controls"><label for="scope">범위</label>
<select id="scope"><option value="all">전체 자료</option>
<option value="main">주요 개발 프로젝트</option>
<option value="variants">과거·파생 작업본</option>
<option value="nas">NAS·보관자료</option></select></div>
<p class="status" id="notice">로컬 Mac 전용 · 두 글자 검색 지원 · 검증된 원본 우선 · 색인 5,519개</p>
<section id="results"></section>
<div class="pagination" id="pagination"></div>
<footer>v1.5 · 같은 내용의 파일은 대표본 아래 보관 위치 묶음으로 표시합니다.
소스코드 자체는 실행·수정하지 않습니다. Finder에서 보기는 원본 위치만 표시합니다.</footer>
<script nonce="__NONCE__">
const token="__TOKEN__";
const $=id=>document.getElementById(id);
const el=(tag,value,cls)=>{const n=document.createElement(tag);if(value!==undefined)n.textContent=value;if(cls)n.className=cls;return n};
let current=1,lastQuery="",busy=false;
function showStatus(t){$('notice').textContent=t}
function card(row){
 const box=el('article',undefined,'result');
 box.append(el('strong',row.title));
 const ch=el('div');ch.append(el('span',row.label,'chip'));
 if(row.provenance)ch.append(el('span','원본 계보 검증','chip'));
 box.append(ch,el('small','위치: '+row.path),el('small','상태: '+row.status));
 if(row.provenance){
  const p=row.provenance;
  box.append(el('small','자산 ID: '+p.asset_id));
  if(p.github_verified&&p.github_repository&&p.github_file_path){
   const a=el('a','검증된 GitHub 파일 보기');
   a.href='https://github.com/'+p.github_repository+'/blob/main/'+p.github_file_path;
   a.target='_blank';a.rel='noopener noreferrer';box.append(a);
  }
  if(p.nas_verified&&p.nas_copy)box.append(el('small','검증된 NAS 사본: '+p.nas_copy));
 }
 if(row.can_reveal){
  const b=el('button','Finder에서 위치 보기');
  b.type='button';
  b.addEventListener('click',async()=>{
   try{
    const r=await fetch('/api/reveal',{method:'POST',
     headers:{'Origin':location.origin,'X-ROUTABL-Request':token,'Content-Type':'application/json'},
     body:JSON.stringify({path:row.path})});
    if(!r.ok)throw Error('파일 위치를 열 수 없습니다');
    showStatus('Finder에서 파일 위치를 표시했습니다.');
   }catch(e){showStatus(e.message);}
  });box.append(b);
 }
 if(row.duplicate_count>1){
  const details=el('details');details.append(el('summary','동일 SHA-256 파일 '+row.duplicate_count+'개 위치 보기'));
  for(const loc of row.locations)details.append(el('small',loc.label+' · '+loc.path));
  if(row.duplicate_count>row.locations.length)details.append(el('small','기타 '+(row.duplicate_count-row.locations.length)+'개 위치'));
  box.append(details);
 }
 return box;
}
async function search(page=1){
 lastQuery=$('query').value.trim();if(lastQuery.length<2){showStatus('두 글자 이상 입력해 주세요.');return}
 current=page;$('results').replaceChildren();$('pagination').replaceChildren();showStatus('검색 중…');
 try{
  const url='/api?q='+encodeURIComponent(lastQuery)+'&page='+page+'&scope='+encodeURIComponent($('scope').value);
  const r=await fetch(url);if(!r.ok)throw Error('검색이 실패했습니다');
  const j=await r.json();
  showStatus('일치 '+j.match_count+'개 경로 · 중복을 묶은 '+j.group_count+'개 결과 · '+j.page+'/'+j.pages+'페이지');
  if(j.manual.length){$('results').append(el('h2','검증 사례'));
   for(const v of j.manual){const c=el('article',undefined,'result');
    c.append(el('strong',v.title),el('small','자산 ID: '+v.id),
     el('small',v.path),el('small',v.validation_grade+' / '+v.details));$('results').append(c)}}
  $('results').append(el('h2','파일 및 보관 위치'));
  if(!j.results.length)$('results').append(el('p','검색 결과가 없습니다.'));
  for(const x of j.results)$('results').append(card(x));
  if(j.pages>1){
   const prev=el('button','이전 페이지');prev.disabled=j.page<=1;prev.onclick=()=>search(j.page-1);
   const next=el('button','다음 페이지');next.disabled=j.page>=j.pages;next.onclick=()=>search(j.page+1);
   $('pagination').append(prev,el('span',j.page+' / '+j.pages+'페이지'),next);
  }
 }catch(e){showStatus(e.message)}
}
$('search').onsubmit=e=>{e.preventDefault();search(1)};
$('scope').onchange=()=>{if(lastQuery)search(1)};
async function poll(){
 try{
  const r=await fetch('/api/status');const j=await r.json();
  if(j.refresh.state==='running'){busy=true;$('refresh').disabled=true;showStatus('색인 갱신 중 · 이전 검색은 계속 가능');}
  else if(busy){busy=false;$('refresh').disabled=false;
   showStatus(j.refresh.state==='complete'?'갱신 완료 · '+j.refresh.last_result.total+'개 항목':'갱신 실패 · 기존 DB 유지 · '+j.refresh.last_error);}
 }catch(e){}
}
$('refresh').onclick=async()=>{
 if(busy)return;busy=true;$('refresh').disabled=true;
 try{
  const r=await fetch('/api/refresh',{method:'POST',
    headers:{'X-ROUTABL-Request':token}});
  if(!r.ok)throw Error('갱신을 시작할 수 없습니다');showStatus('색인 갱신 중…');
 }catch(e){busy=false;$('refresh').disabled=false;showStatus(e.message);}
};
setInterval(poll,1500);
</script></main></body></html>"""
    return page.replace("__NONCE__", core.TOKEN).replace("__TOKEN__", core.TOKEN)


_ORIGINAL_STATUS = core.status

def status():
    state = _ORIGINAL_STATUS()
    state["version"] = "1.5"
    state["service"] = SERVICE
    return state

# v1.4's safe HTTP handlers look up these module-level callbacks at request time.
core.ui_page = ui_page
core.status = status

def serve():
    STORE.mkdir(mode=0o700, parents=True, exist_ok=True)
    fd = os.open(STORE / "search_v1_5_server.lock",
                 os.O_RDWR | os.O_CREAT, 0o600)
    try:
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            print("ROUTABL_ASSET_SEARCH_V1_5_ALREADY_RUNNING", flush=True)
            return 0
        core.initialize_index()
        server = ThreadingHTTPServer(("127.0.0.1", PORT), App)
        server.daemon_threads = True
        threading.Thread(target=core.stop_when_idle, args=(server,), daemon=True).start()
        print("ROUTABL_ASSET_SEARCH_V1_5_READY", URL, flush=True)
        try:
            server.serve_forever(poll_interval=.5)
        finally:
            server.server_close()
        return 0
    finally:
        fcntl.flock(fd, fcntl.LOCK_UN)
        os.close(fd)


if __name__ == "__main__":
    import sys
    if len(sys.argv) == 2 and sys.argv[1] == "serve":
        raise SystemExit(serve())
    if len(sys.argv) > 2 and sys.argv[1] == "query":
        # Run without server, provided the v1.5 DB has already been initialized.
        print(json.dumps(query(" ".join(sys.argv[2:])), ensure_ascii=False))
    elif len(sys.argv) == 2 and sys.argv[1] == "check":
        print(json.dumps({"service": SERVICE, "db_exists": INDEX.is_file(),
                          "rows": core.check_db(INDEX)[0] if INDEX.exists() else 0}))
    else:
        raise SystemExit("Usage: routabl_search_v1_5_service.py serve|check|query TERM")
