"""Run the candidate and the pinned original against a disposable MVL fixture."""
import contextlib
import hashlib
import importlib
import io
import json
import shutil
import sqlite3
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
ID = "MVL-USER-R01"
OTHER = "MVL-USER-R01-A"
BODY = b"R01_BODY_SENTINEL_NEVER_EXPORTED"
SCHEMA = """
CREATE TABLE docs (
    path TEXT PRIMARY KEY, carrier TEXT, kind TEXT, sz INTEGER,
    mtime_ns INTEGER, sha TEXT, status TEXT, title TEXT, tags TEXT,
    content TEXT, extra INTEGER
);
CREATE TABLE manual (id, title, tags, path, source_grade, validation_grade, details);
"""


class SelectedHandoffTest(unittest.TestCase):
    def setUp(self):
        temp = TemporaryDirectory(dir=HERE, prefix="test-fixture-")
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name).resolve()
        for name in ("mvl.py", "mvl_original.py", "mvl_provenance.py", "routabl_search_v1_5_service.py"):
            shutil.copyfile(HERE / name, self.root / name)
        # v1.5 requires a v1.4 module at import. Query and provenance are the pinned v1.5 code.
        (self.root / "routabl_search_v1_4_service.py").write_text("# Synthetic import stub.\n")
        (self.root / "incoming").mkdir()
        self.document = self.root / "incoming" / "candidate.md"
        self.document.write_bytes(BODY)
        refs = []
        for index in range(7):
            filename = f"fixed-{index}.md"
            raw = filename.encode()
            (self.root / filename).write_bytes(raw)
            refs.append(dict(id=f"FIXTURE-FIXED-{index}", title=filename, version="1.0",
                             path=str(self.root / filename), registration="PINNED_REFERENCE",
                             sha256=hashlib.sha256(raw).hexdigest()))
        (self.root / "REFERENCES.json").write_text(json.dumps(refs))
        (self.root / "FEEDBACK_CANDIDATE.md").write_text("Synthetic fixed feedback")
        with contextlib.closing(sqlite3.connect(self.root / "assets_v1_5.sqlite")) as db:
            db.executescript(SCHEMA)
        modules = patch.dict(sys.modules)
        modules.start()
        self.addCleanup(modules.stop)
        self.addCleanup(sys.path.remove, str(self.root))
        sys.path.insert(0, str(self.root))
        provenance = importlib.import_module("mvl_provenance")
        provenance.REPO = self.root
        provenance.load_registry = lambda: ({"provenance_crosswalk": []}, {})
        self.mvl = importlib.import_module("mvl")
        self.original = importlib.import_module("mvl_original")
        self.mvl.seed()
        self.mvl.register_feedback()
        self.assertEqual(self.mvl.register(ID, "1.2", "incoming/candidate.md"), "REGISTERED")

    def sql(self, statement, params=()):
        with contextlib.closing(sqlite3.connect(self.mvl.DB)) as db, db:
            return db.execute(statement, params).fetchall()

    def change_reference(self, **changes):
        key = "MVL/" + ID
        raw, = self.sql("SELECT reference_json FROM mvl_sources WHERE index_path=?", (key,))[0]
        self.sql("UPDATE mvl_sources SET reference_json=? WHERE index_path=?",
                 (json.dumps(dict(json.loads(raw), **changes)), key))

    def cli(self, *args):
        out, err = io.StringIO(), io.StringIO()
        with patch.object(sys, "argv", ["mvl.py", *args]), \
                contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            try:
                self.mvl.main()
            except SystemExit as exc:
                return exc.code, out.getvalue(), err.getvalue()
        return 0, out.getvalue(), err.getvalue()

    def test_selected_metadata_and_cli(self):
        before = self.mvl.DB.read_bytes()
        data = self.mvl.package("final", [ID])
        self.assertEqual(len(data["references"]), 9)
        row = data["references"][-1]
        digest = hashlib.sha256(BODY).hexdigest()
        self.assertEqual(row, {
            "asset_id": ID, "source_version": "1.2", "source_path": str(self.document),
            "expected_sha256": digest, "expected_size_bytes": len(BODY),
            "registration": "ISOLATED_CANDIDATE", "registry_version": None, "registry_sha256": None,
            "observed_sha256": digest, "observed_size_bytes": len(BODY), "status": "LOCAL_HASH_MATCH",
        })
        status, out, err = self.cli("handoff", "final", "--asset-id", ID)
        self.assertEqual((status, err), (0, ""))
        self.assertIn(f"| {ID} | {self.document} | 1.2 | {digest} | {digest} | LOCAL_HASH_MATCH | ISOLATED_CANDIDATE |", out)
        self.assertEqual(self.mvl.DB.read_bytes(), before)

    def test_no_body_and_no_unapproved_metadata(self):
        sentinel = BODY.decode()
        self.change_reference(body=sentinel, registry_sha256=sentinel, arbitrary=sentinel)
        data = self.mvl.package("initial", [ID])
        self.assertNotIn(sentinel, json.dumps(data))
        self.assertNotIn(sentinel, self.mvl.render_handoff("initial", [ID]))
        self.assertEqual(self.sql("SELECT content FROM docs WHERE path=?", ("MVL/" + ID,)), [("",)])

    def test_unknown_id_rejected_with_no_output(self):
        code, out, err = self.cli("handoff", "final", "--asset-id", ID, "--asset-id", "MVL-USER-MISSING")
        self.assertEqual((code, out), (1, ""))
        self.assertIn("SELECTED_ASSET_NOT_REGISTERED", err)

    def test_index_only_row_is_not_a_registration(self):
        self.sql("DELETE FROM mvl_sources WHERE index_path=?", ("MVL/" + ID,))
        with self.assertRaisesRegex(ValueError, "SELECTED_ASSET_NOT_REGISTERED"):
            self.mvl.package("initial", [ID])

    def test_invalid_id_rejected(self):
        code, out, err = self.cli("handoff", "initial", "--asset-id", "mvl-user-r01")
        self.assertEqual((code, out), (1, ""))
        self.assertIn("INVALID_USER_ASSET_ID", err)

    def test_duplicate_requested_id_rejected(self):
        code, out, err = self.cli("handoff", "final", "--asset-id", ID, "--asset-id", ID)
        self.assertEqual((code, out), (1, ""))
        self.assertIn("DUPLICATE_SELECTED_ASSET_ID", err)

    def test_duplicate_index_id_rejected(self):
        self.sql("CREATE TABLE duplicated AS SELECT * FROM docs")
        self.sql("DROP TABLE docs")
        self.sql("ALTER TABLE duplicated RENAME TO docs")
        self.sql("INSERT INTO docs SELECT * FROM docs WHERE path=?", ("MVL/" + ID,))
        with self.assertRaisesRegex(ValueError, "DUPLICATE_SELECTED_ASSET_ID"):
            self.mvl.package("initial", [ID])

    def test_registration_id_binding(self):
        self.change_reference(asset_id=OTHER)
        with self.assertRaisesRegex(ValueError, "INVALID_SELECTED_REGISTRATION"):
            self.mvl.package("initial", [ID])

    def test_non_candidate_rejected(self):
        self.change_reference(registration="OFFICIAL_ROW")
        with self.assertRaisesRegex(ValueError, "INVALID_SELECTED_REGISTRATION"):
            self.mvl.package("initial", [ID])

    def test_invalid_version_rejected(self):
        self.change_reference(source_version="draft")
        with self.assertRaisesRegex(ValueError, "INVALID_SELECTED_METADATA"):
            self.mvl.package("initial", [ID])

    def test_index_mismatch_rejected(self):
        self.sql("UPDATE docs SET sha=? WHERE path=?", ("0" * 64, "MVL/" + ID))
        with self.assertRaisesRegex(ValueError, "SELECTED_INDEX_MISMATCH"):
            self.mvl.package("initial", [ID])

    def test_missing_index_row_rejected(self):
        self.sql("DELETE FROM docs WHERE path=?", ("MVL/" + ID,))
        with self.assertRaisesRegex(ValueError, "SELECTED_INDEX_MISMATCH"):
            self.mvl.package("initial", [ID])

    def test_tampered_same_size_rejected(self):
        self.document.write_bytes(b"x" * len(BODY))
        code, out, err = self.cli("handoff", "initial", "--asset-id", ID)
        self.assertEqual((code, out), (1, ""))
        self.assertIn("HASH_MISMATCH", err)

    def test_missing_file_rejected(self):
        self.document.unlink()
        with self.assertRaisesRegex(ValueError, "SOURCE_MISSING"):
            self.mvl.package("initial", [ID])

    def test_file_symlink_rejected_even_with_matching_content(self):
        target = self.root / "synthetic-target.md"
        self.document.rename(target)
        self.document.symlink_to(target)
        with self.assertRaisesRegex(ValueError, "SOURCE_UNAVAILABLE"):
            self.mvl.package("initial", [ID])

    def test_parent_symlink_rejected_even_with_matching_content(self):
        moved = self.document.parent.rename(self.root / "moved")
        self.document.parent.symlink_to(moved, target_is_directory=True)
        with self.assertRaisesRegex(ValueError, "SOURCE_UNAVAILABLE"):
            self.mvl.package("initial", [ID])

    def test_outside_and_traversal_rejected_before_read(self):
        target = self.root / "synthetic-target.md"
        target.write_bytes(BODY)
        for path in (str(target), str(self.document.parent / ".." / target.name), "incoming/candidate.md"):
            with self.subTest(path=path):
                self.change_reference(source_path=path)
                with patch.object(self.mvl, "verify_source") as verifier:
                    with self.assertRaisesRegex(ValueError, "SELECTED_SOURCE_PATH_NOT_ALLOWED"):
                        self.mvl.package("initial", [ID])
                    verifier.assert_not_called()

    def test_same_sha_different_ids_selected_exactly_in_request_order(self):
        (self.document.parent / "same.txt").write_bytes(BODY)
        self.mvl.register(OTHER, "2.0", "incoming/same.txt")
        search = self.mvl.search(ID)
        self.assertEqual((search["match_count"], search["group_count"]), (2, 1))
        status, out, err = self.cli("handoff", "initial", "--asset-id", OTHER, "--asset-id", ID)
        self.assertEqual((status, err), (0, ""))
        rows = [line.split("|")[1].strip() for line in out.splitlines() if line.startswith("| MVL-USER-")]
        self.assertEqual(rows, [OTHER, ID])

    def test_unchanged_default_handoff_and_search_against_pinned_original(self):
        for phase, count in (("initial", 7), ("final", 8)):
            with self.subTest(phase=phase):
                self.assertEqual(len(self.mvl.package(phase)["references"]), count)
                self.assertEqual(self.mvl.package(phase), self.original.package(phase))
                expected = self.original.render_handoff(phase)
                self.assertEqual(self.cli("handoff", phase), (0, expected, ""))
                self.assertNotIn(ID, expected)
        for term in (ID, self.mvl.FEEDBACK_ID, "FIXTURE-FIXED-0", "no-result"):
            self.assertEqual(self.mvl.search(term), self.original.search(term))

    def test_read_only_selected_db(self):
        with contextlib.closing(self.mvl.connection(read_only=True)) as db:
            with self.assertRaisesRegex(sqlite3.OperationalError, "readonly"):
                db.execute("DELETE FROM docs")


if __name__ == "__main__":
    unittest.main(verbosity=2)
