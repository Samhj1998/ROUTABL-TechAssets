"""Local CLI for registration, search, verified handoff, and feedback."""
import argparse
import json
import re
import sqlite3
from pathlib import Path

from mvl_provenance import REPO, ROOT, LATEST_NAME, LATEST_SHA, load_registry, make_ref, read_evidence
import routabl_search_v1_5_service as engine

DB = ROOT / "assets_v1_5.sqlite"
LEGACY_CASES = (
    ("고객등록", "all"), ("취소상태", "all"), ("월간정산", "all"),
    ("기사앱", "main"), ("TransportStatusPolicy.kt", "main"),
    ("cloud_access.py", "main"), ("DailyInspection", "variants"),
    ("ROUTABL", "nas"), ("no-result-mvl01-20261108", "all"),
)
FEEDBACK_ID = "MVL01-FEEDBACK"
FEEDBACK_FILE = ROOT / "FEEDBACK_CANDIDATE.md"
REFERENCES = json.loads((ROOT / "REFERENCES.json").read_bytes())


def search(term, scope="all", page=1):
    return engine.query(term, page=page, scope=scope)


def connection():
    if not DB.is_file() or DB.is_symlink():
        raise ValueError("ISOLATED_DATABASE_MISSING")
    db = sqlite3.connect(DB.as_uri() + "?mode=rw", uri=True)
    db.execute("PRAGMA temp_store=MEMORY")
    return db


def builtin_ref(item):
    _, rows = load_registry()
    path = REPO / item["path"]
    observed, size, _ = read_evidence(path)
    if observed != item["sha256"]:
        raise ValueError("REFERENCE_PIN_MISMATCH")
    if item["registration"] == "OFFICIAL_ROW":
        row = rows[item["id"]]
        if (row["observed_original_path"], row["sha256"], row["bytes"]) != (str(path), observed, size):
            raise ValueError("REFERENCE_REGISTRY_MISMATCH")
    return make_ref(item["id"], item["version"], path, observed, size, item["registration"])


def upsert(db, ref, title, *, replace_feedback=False):
    asset_id = ref["asset_id"]
    path = "MVL/" + asset_id
    encoded = json.dumps(ref, ensure_ascii=False, sort_keys=True)
    previous = db.execute("SELECT reference_json FROM mvl_sources WHERE index_path=?", (path,)).fetchone()
    if previous and previous[0] == encoded:
        indexed = db.execute("SELECT sha,sz FROM docs WHERE path=?", (path,)).fetchone()
        if indexed != (ref["expected_sha256"], ref["expected_size_bytes"]):
            raise ValueError("ISOLATED_INDEX_DRIFT")
        return "ALREADY_REGISTERED"
    if previous and not (replace_feedback and asset_id == FEEDBACK_ID):
        raise ValueError("ASSET_ID_COLLISION")
    args = (path, "MVL_ISOLATED", "metadata", ref["expected_size_bytes"], 0,
            ref["expected_sha256"], "LOCAL_METADATA_INDEX", title, asset_id, "", 0)
    if previous:
        db.execute("DELETE FROM docs WHERE path=?", (path,))
        db.execute("DELETE FROM mvl_sources WHERE index_path=?", (path,))
    db.execute("INSERT INTO docs VALUES (?,?,?,?,?,?,?,?,?,?,?)", args)
    db.execute("INSERT INTO mvl_sources VALUES (?,?)", (path, encoded))
    return "REGISTERED"


def register_records(records, replace_feedback=False):
    with connection() as db:
        db.execute("BEGIN IMMEDIATE")
        db.execute("CREATE TABLE IF NOT EXISTS mvl_sources (index_path TEXT PRIMARY KEY, reference_json TEXT NOT NULL)")
        return [upsert(db, ref, title, replace_feedback=replace_feedback) for ref, title in records]


def seed():
    return register_records([(builtin_ref(item), item["title"]) for item in REFERENCES])


def local_ref(asset_id, version, path):
    if not re.fullmatch(r"[0-9]+(?:\.[0-9]+){0,2}", version):
        raise ValueError("INVALID_VERSION")
    sha, size, _ = read_evidence(path)
    return make_ref(asset_id, version, path, sha, size, "ISOLATED_CANDIDATE")


def register(asset_id, version, name):
    if not re.fullmatch(r"MVL-USER-[A-Z0-9][A-Z0-9-]{0,54}", asset_id):
        raise ValueError("INVALID_USER_ASSET_ID")
    if not re.fullmatch(r"incoming/[A-Za-z0-9][A-Za-z0-9_.-]{0,100}\.(?:md|txt)", name):
        raise ValueError("INCOMING_PATH_REQUIRED")
    return register_records([(local_ref(asset_id, version, ROOT / name), asset_id)])[0]


def register_feedback():
    return register_records([(local_ref(FEEDBACK_ID, "0.1", FEEDBACK_FILE),
                              "MVL-01 환류 검색 v1.5 최신 대장 및 검증 인계")] )[0]


def lookup(asset_id):
    found = [row["origin"] for row in search(asset_id)["results"]
             if row["origin"].get("asset_id") == asset_id]
    if len(found) != 1 or found[0]["status"] != "LOCAL_HASH_MATCH":
        raise ValueError("REQUIRED_SOURCE_NOT_VERIFIED: " + asset_id)
    return found[0]


def package(phase):
    ids = [item["id"] for item in REFERENCES]
    if phase == "final":
        ids.append(FEEDBACK_ID)
    return {"task": "MVL-01 격리 검색 v1.5 최신 대장 연결 및 원본 검증 인계", "phase": phase,
            "registry": {"version": "0.27", "name": LATEST_NAME, "sha256": LATEST_SHA},
            "verification_actor": "120-2-W Mac Studio 격리 CLI",
            "source_verification_method": "격리 색인 기대 해시 대조 및 Mac Studio 파일 전체 바이트 SHA-256",
            "independent_receiver": "NOT_TESTED", "references": [lookup(i) for i in ids]}


def render_handoff(phase):
    data = package(phase)
    lines = [
        "# Digitopia MVL-01 독립 AI 개발 인계", "",
        "목표는 기존 v1.5 검색을 재사용해 최신 대장 연결과 검증 가능한 결과 환류를 완성하는 것이다.",
        "이 자료는 120-2-W의 로컬 검증 기록이다. 수신자가 수행한 검증은 따로 기록한다.", "",
        "## 확인된 동작과 재사용", "",
        "- 운영 v1.5는 출처 연결에 v0.6을 고정 참조한다. v0.6과 v0.27의 출처 연결 두 건은 동일하다.",
        "- v1.5 검색 SQL·별칭·순위·SHA 기준 중복 묶음을 재사용한다. v1.4에서 DB 검사 기능을 재사용한다.",
        "- CW-01의 자산 ID·경로·SHA-256 인계 방식과 AF-01의 접근 우선 방향을 적용한다.",
        "- v0.27의 번호·해시·스키마·ID를 확인한다. 검색 색인 기대값과 원본 직접 해시를 구별한다.", "",
        "## 검색에서 다시 찾은 기술자산", "",
        "| ID | 출처 경로 | 판본 | 기대 SHA-256 | 실측 SHA-256 | 검증 상태 | 등록 구분 |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in data["references"]:
        lines.append("| " + " | ".join([row["asset_id"], row["source_path"], row["source_version"] or "미명시",
                                        row["expected_sha256"], row["observed_sha256"],
                                        row["status"], row["registration"]]) + " |")
    lines += ["", "## 수신자가 검토할 과제", "",
              "독립 승인에 기재된 격리 코드와 증거만 사용해 대장 선택·출처 검증·환류 재검색을 검토한다.",
              "잘못된 원본 경로, 해시 불일치, 민감 자료 포함, 회귀 가능성을 확인하고 재현 가능한 검토 결과 또는 개선안을 반환한다.",
              "기대 산출물은 코드 차이 검토, 시험 명령·결과, 재현 조건, 성공·실패·미검증을 구분한 보고다.",
              "등록되지 않은 후보와 공식 대장 행을 구별한다. 독립 수신자의 직접 파일 검증은 실제 수행 근거가 있는 경우에만 기록한다.", "",
              "## 실행 경계", "",
              "제출과 접근은 별도 승인 범위에서만 수행한다. 기본 인계는 정적 기술 메타데이터로 구성한다.",
              "운영 검색·DB·공식 대장·원본·백업·라우터블 운영 서비스는 변경하지 않는다.",
              "외부 게시, 원본 본문 전송, 고객정보·비밀번호·토큰·키 전달은 금지한다.", "",
              "## 결과 반환 필드", "",
              "수신 환경, 사용 자료 ID·경로·기대/실측 SHA-256, 확인 방식, 실제 검토·변경 내용, 재현 명령, 결과, 미검증, 권한 준수, 다음 판단을 기록한다.", ""]
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    subs = parser.add_subparsers(dest="command", required=True)
    q = subs.add_parser("search")
    q.add_argument("term")
    q.add_argument("--scope", choices=sorted(engine.SCOPE), default="all")
    q.add_argument("--page", type=int, default=1)
    r = subs.add_parser("register")
    r.add_argument("asset_id")
    r.add_argument("version")
    r.add_argument("path")
    h = subs.add_parser("handoff")
    h.add_argument("phase", choices=("initial", "final"))
    subs.add_parser("check")
    subs.add_parser("seed")
    subs.add_parser("feedback")
    args = parser.parse_args()
    try:
        if args.command == "handoff":
            print(render_handoff(args.phase), end="")
            return
        if args.command == "search":
            result = search(args.term, args.scope, args.page)
        elif args.command == "register":
            result = register(args.asset_id, args.version, args.path)
        elif args.command == "seed":
            result = seed()
        elif args.command == "feedback":
            result = register_feedback()
        else:
            load_registry()
            rows, baseline = engine.core.check_db(DB)
            result = {"registry_version": "0.27", "rows": rows, "explicit_local_rows": baseline}
        print(json.dumps(result, ensure_ascii=False, indent=2))
    except (OSError, ValueError, KeyError, sqlite3.Error) as exc:
        parser.exit(1, "MVL-01: " + str(exc) + "\n")


if __name__ == "__main__":
    main()
