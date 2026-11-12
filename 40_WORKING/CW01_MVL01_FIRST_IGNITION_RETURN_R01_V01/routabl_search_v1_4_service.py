from pathlib import Path
import sqlite3

def check_db(path: Path) -> tuple[int, int]:
    with sqlite3.connect("file:" + str(path) + "?mode=ro", uri=True, timeout=10) as db:
        if db.execute("PRAGMA quick_check").fetchone()[0] != "ok":
            raise RuntimeError("SQLite integrity check failed")
        rows = db.execute("SELECT COUNT(*) FROM docs").fetchone()[0]
        safe = db.execute(
            "SELECT COUNT(*) FROM docs WHERE carrier='MAC_STUDIOPROJECTS_EXPLICIT_ALLOWLIST'"
        ).fetchone()[0]
        if safe != 2 or rows < 2272:
            raise RuntimeError("Expected verified baseline not found")
        return rows, safe


