"""Run pinned MVL code without reading sources outside the approved scope."""
import json
import runpy
import sys
from pathlib import Path
from urllib.parse import urlsplit, unquote

import mvl_provenance as provenance

ROOT = Path(__file__).resolve().parent
DB = ROOT / "assets_v1_5.sqlite"
REGISTRY = ROOT.parents[1] / "30_REGISTRY" / "asset_manifest_v0.27.json"
assert provenance.ROOT == ROOT and provenance.REGISTRY == REGISTRY.parent
assert ROOT.name == "CW01_MVL01_FIRST_IGNITION_RETURN_R01_V01"
assert (ROOT / "incoming").resolve(strict=True) == ROOT / "incoming"
assert DB.resolve(strict=True) == DB and DB.is_file()

policy = json.loads((ROOT / "SOURCE_SCOPE.json").read_bytes())
allowed = {Path(p) for p in policy["read"]}
assert REGISTRY in allowed
read_evidence = provenance.read_evidence

def scoped_read(path, *args, **kwargs):
    path = Path(path)
    if path not in allowed:
        print("SCOPE_DENIED", str(path), file=sys.stderr)
        raise PermissionError("OUTSIDE_APPROVED_SOURCE_SCOPE")
    return read_evidence(path, *args, **kwargs)

provenance.read_evidence = scoped_read

def db_scope(event, args):
    if event == "sqlite3.connect":
        raw = str(args[0])
        path = unquote(urlsplit(raw).path) if raw.startswith("file:") else raw
        if Path(path) != DB:
            raise PermissionError("OUTSIDE_APPROVED_SQLITE_SCOPE")

sys.addaudithook(db_scope)

if __name__ == "__main__":
    program, *args = sys.argv[1:]
    assert program in ("mvl_original.py", "mvl.py")
    sys.argv[:] = [program, *args]
    runpy.run_path(str(ROOT / program), run_name="__main__")
