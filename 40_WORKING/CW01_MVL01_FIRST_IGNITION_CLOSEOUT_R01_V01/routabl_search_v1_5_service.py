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

STORE = Path(__file__).resolve().parent
PROJECT_ROOT = Path.home() / "StudioProjects"
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

from mvl_provenance import resolve_crosswalk, attach_origins

CROSSWALK = resolve_crosswalk()

def kind(path):
    if path.startswith("MVL/"):
        return "asset", "격리 색인 기술자산"
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
    attach_origins(INDEX, subset)
    return {"term": term, "terms": terms, "scope": scope, "page": page,
            "page_size": page_size, "pages": pages, "match_count": len(scored),
            "group_count": result_count, "manual": manual, "results": subset}

