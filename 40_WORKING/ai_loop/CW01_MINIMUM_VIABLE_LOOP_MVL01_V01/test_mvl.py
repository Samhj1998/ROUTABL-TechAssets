"""Exercise the MVL-01 CLI and fail-closed provenance in the isolated directory."""
import hashlib
import json
import sqlite3
import subprocess
import sys
from pathlib import Path
from tempfile import TemporaryDirectory

from mvl import (
    DB, FEEDBACK_FILE, FEEDBACK_ID, LEGACY_CASES, REFERENCES, connection,
    lookup, package, register, render_handoff, search, seed, register_feedback,
)
from mvl_provenance import ROOT, REGISTRY, LATEST_NAME, LATEST_SHA, load_registry, make_ref, verify_source

RESULTS = []


def test(name, check):
    try:
        details = check()
        RESULTS.append({"test": name, "result": "PASS", "evidence": details})
    except Exception as exc:
        RESULTS.append({"test": name, "result": "FAIL", "error": repr(exc)})


def reject(expected, action):
    try:
        action()
    except ValueError as exc:
        assert expected in str(exc), str(exc)
        return expected
    raise AssertionError("Expected rejection: " + expected)


def official():
    data, ids = load_registry()
    assert data["schema_version"] == "0.27" and len(ids) == 162
    return {"latest": LATEST_NAME, "sha256": LATEST_SHA, "rows": len(ids)}


def existing_cases():
    proof = json.loads((ROOT / "LEGACY_REGRESSION.json").read_bytes())
    assert len(proof["cases"]) == len(LEGACY_CASES)
    for case in proof["cases"]:
        result = search(case["term"], case["scope"])
        got = [[r["path"], r["score"], r["duplicate_count"]] for r in result["results"]]
        assert got == case["order"], (case["term"], case["scope"])
        assert [result["match_count"], result["group_count"], len(result["manual"])] == [
            case["match_count"], case["group_count"], case["manual_count"]]
    return {"post_overlay_cases": len(proof["cases"]), "checks": "result order, score, group counts, manual counts"}


def crosswalk(asset_id, term):
    found = [r["origin"] for r in search(term, "main")["results"] if r["origin"].get("asset_id") == asset_id]
    assert len(found) == 1, found
    row = found[0]
    assert row["status"] == "LOCAL_HASH_MATCH"
    assert row["expected_sha256"] == row["observed_sha256"]
    assert row["registry_version"] == "0.27" and row["registration"] == "OFFICIAL_ROW"
    return row


def ref_results():
    rows = [lookup(r["id"]) for r in REFERENCES]
    assert len(rows) == 7
    assert {r["registration"] for r in rows} == {"OFFICIAL_ROW", "REGISTRY_DOCUMENT", "PINNED_REFERENCE"}
    assert all(r["observed_sha256"] == r["expected_sha256"] for r in rows)
    return {"found": len(rows), "classification_preserved": True}


def fixture_paths():
    with TemporaryDirectory(dir=ROOT) as d:
        base = Path(d)
        path = base / "reference.md"
        path.write_bytes(b"reference")
        sha = hashlib.sha256(b"reference").hexdigest()
        ref = make_ref("MVL-USER-TEST", "1.0", path, sha, 9, "ISOLATED_CANDIDATE")
        assert verify_source(ref, sha)["status"] == "LOCAL_HASH_MATCH"
        assert verify_source(ref, "0" * 64)["status"] == "INDEX_HASH_MISMATCH"
        path.write_bytes(b"incorrect")
        tampered = verify_source(ref, sha)
        assert tampered["status"] == "HASH_MISMATCH" and tampered["observed_sha256"] != sha
        path.unlink()
        missing = verify_source(ref, sha)
        assert missing["status"] == "SOURCE_MISSING" and missing["observed_sha256"] is None
        path.symlink_to(REGISTRY / LATEST_NAME)
        alias = verify_source(ref, sha)
        assert alias["status"] == "SOURCE_UNAVAILABLE" and alias["observed_sha256"] is None
        other = base / "alias"
        other.symlink_to(REGISTRY, target_is_directory=True)
        assert verify_source(dict(ref, source_path=str(other / LATEST_NAME)), sha)["status"] == "SOURCE_UNAVAILABLE"
    return ["byte mutation", "indexed hash mismatch", "missing", "file symlink", "directory symlink"]


def future_registry():
    with TemporaryDirectory(dir=ROOT) as d:
        p = Path(d)
        (p / LATEST_NAME).write_bytes((REGISTRY / LATEST_NAME).read_bytes())
        assert load_registry(p)[0]["schema_version"] == "0.27"
        (p / "asset_manifest_v0.100.json").write_bytes(b"{}")
        reject("UNPINNED_LATEST_REGISTRY", lambda: load_registry(p))
        (p / "asset_manifest_v0.100.json").unlink()
        (p / LATEST_NAME).write_bytes(b"{}")
        reject("REGISTRY_PIN_MISMATCH", lambda: load_registry(p))
        (p / "asset_manifest_v0.027.json").touch()
        reject("REGISTRY_VERSION_COLLISION", lambda: load_registry(p))
    return ["numeric latest", "future pin absent", "tampered pin", "duplicate version"]


def register_cli():
    fixture = ROOT / "incoming/MVL_TEST_TEMP.md"
    asset_id = "MVL-USER-REGISTRATION-TEST"
    with fixture.open("x") as f:
        f.write("MVL_TEST_NO_EXPORT_2011 synthetic body")
    try:
        assert register(asset_id, "1.0", "incoming/" + fixture.name) == "REGISTERED"
        assert register(asset_id, "1.0", "incoming/" + fixture.name) == "ALREADY_REGISTERED"
        assert lookup(asset_id)["registration"] == "ISOLATED_CANDIDATE"
        assert not search("MVL_TEST_NO_EXPORT_2011")["results"]
        assert asset_id not in render_handoff("initial")
        with connection() as db:
            assert db.execute("SELECT content FROM docs WHERE path=?", ("MVL/" + asset_id,)).fetchone() == ("",)
        fixture.write_text("changed bytes")
        reject("ASSET_ID_COLLISION", lambda: register(asset_id, "1.0", "incoming/" + fixture.name))
        assert search(asset_id)["results"][0]["origin"]["status"] == "HASH_MISMATCH"
        reject("INCOMING_PATH_REQUIRED", lambda: register(asset_id, "1.0", "incoming/../secret.md"))
    finally:
        with connection() as db:
            db.execute("DELETE FROM docs WHERE path=?", ("MVL/" + asset_id,))
            db.execute("DELETE FROM mvl_sources WHERE index_path=?", ("MVL/" + asset_id,))
        fixture.unlink()
    return ["new row", "idempotence", "collision rejection", "no source text indexing", "no automatic export", "traversal rejection"]


def handoff(phase):
    data = package(phase)
    md = render_handoff(phase)
    assert len(data["references"]) == (8 if phase == "final" else 7)
    for row in data["references"]:
        assert row["asset_id"] in md and row["observed_sha256"] in md and row["source_path"] in md
    assert data["independent_receiver"] == "NOT_TESTED"
    assert "cloud_access.py" not in md and "assets_v1_5.sqlite" not in md and "nas_copy" not in md
    assert (FEEDBACK_ID in md) == (phase == "final")
    return {"phase": phase, "records": len(data["references"]), "export": "static allowlist; paths and evidence metadata only"}


def index_integrity():
    with sqlite3.connect(DB.as_uri()+"?mode=ro",uri=True) as db:
        assert db.execute("PRAGMA quick_check").fetchone() == ("ok",)
        docs = db.execute("SELECT COUNT(*) FROM docs").fetchone()[0]
        refs = db.execute("SELECT COUNT(*) FROM mvl_sources").fetchone()[0]
        assert (docs, refs) == (5527, 8), (docs, refs)
        assert db.execute("SELECT COUNT(*) FROM docs WHERE carrier='MVL_ISOLATED' AND content<>''").fetchone() == (0,)
    completed = subprocess.run([sys.executable, "-B", str(ROOT/"mvl.py"), "check"],
                               check=True, capture_output=True, text=True)
    result = json.loads(completed.stdout)
    assert result == {"registry_version": "0.27", "rows": 5527, "explicit_local_rows": 2}
    return result


def run(stage):
    if stage == "initial":
        test("latest registry byte pin and schema", official)
        test("legacy query regression after seeding", existing_cases)
        test("legacy official crosswalk source 1", lambda: crosswalk("TA-CASE-20261102-01", "cloud_access.py"))
        test("legacy official crosswalk source 2", lambda: crosswalk("INTEGRATION-F1", "TransportStatusPolicy.kt"))
        test("seven actual search references", ref_results)
        test("missing, tampered, symlinked, or unbound source", fixture_paths)
        test("future, tampered, or conflicting registry", future_registry)
        test("user registration and local-only content", register_cli)
        test("idempotent baseline registry", lambda: idempotence())
        test("initial handoff allowlist", lambda: handoff("initial"))
    elif stage == "final":
        test("feedback search and local source hash", lambda: lookup(FEEDBACK_ID))
        test("final handoff includes independently re-searched feedback", lambda: handoff("final"))
        test("legacy regression after feedback", existing_cases)
        test("SQLite and Mac CLI entry point", index_integrity)
    return RESULTS


def idempotence():
    assert seed() == ["ALREADY_REGISTERED"] * 7
    return {"idempotent_count": 7}


if __name__ == "__main__":
    results = run(sys.argv[1])
    print(json.dumps(results, ensure_ascii=False, indent=2))
    raise SystemExit(0 if all(t["result"] == "PASS" for t in results) else 1)
