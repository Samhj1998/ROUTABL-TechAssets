"""PoC acceptance tests. Produces no files outside the PoC directory."""
from copy import deepcopy
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

import handoff as h

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]


def run():
    left, right = [h.read_json(HERE / name) for name in ("chat_to_work.json", "work_to_chat.json")]
    outcomes = []

    def case(name, check, expected=None):
        try:
            check()
        except Exception as error:
            if expected and isinstance(error, expected[0]) and expected[1] in str(error):
                outcomes.append((name, "PASS", f"expected {expected[0].__name__}: {error}"))
            else:
                outcomes.append((name, "FAIL", str(error) or type(error).__name__))
        else:
            outcomes.append((name, "FAIL" if expected else "PASS",
                             "expected rejection was absent" if expected else "expected outcome observed"))

    def alter(change):
        record = deepcopy(left)
        change(record)
        return record

    def valid(change):
        h.validate_record(alter(change), ROOT)

    def gate(record, expected):
        h.validate_record(record, ROOT)
        assert h.execution_gate(record) == expected

    def statuses(record):
        content = h.markdown(record).decode().replace(r"\_", "_")
        for item in record["evidence"]:
            assert f'**status** — "{item["status"]}"' in content
            assert f'**origin** — "{item["origin"]}"' in content

    def independent():
        with tempfile.TemporaryDirectory(prefix=".isolation-", dir=HERE) as temporary:
            directory = Path(temporary)
            names = ("handoff.py", "schema.json", "chat_to_work.json", "work_to_chat.json")
            refs = directory / "references"
            for name in names:
                shutil.copyfile(HERE / name, directory / name)
            for item in left["assets"]:
                destination = refs / item["path"]
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(ROOT / item["path"], destination)
            for operation in ("render", "verify"):
                subprocess.run([sys.executable, "-I", "-B", "handoff.py", operation, "--root",
                                str(refs), "chat_to_work.json", "work_to_chat.json"],
                               cwd=directory, check=True, capture_output=True)
            for name in ("chat_to_work.md", "work_to_chat.md"):
                assert (directory / name).read_bytes() == (HERE / name).read_bytes()

    invalid = h.Invalid
    case("01 Chat to Work", lambda: h.verify_markdown(left, (HERE / "chat_to_work.md").read_bytes()))
    case("02 Work to Chat", lambda: h.verify_markdown(right, (HERE / "work_to_chat.md").read_bytes()))
    case("03 required field", lambda: valid(lambda r: r["next"].pop("completion")), (invalid, "missing"))
    case("04 direction and target", lambda: valid(lambda r: r["to"].update(chat="120-2")), (invalid, "record.to.chat"))
    case("05 missing reference", lambda: valid(lambda r: r["assets"][0].update(path="missing-fixture.md")), (invalid, "asset missing"))
    case("06 altered hash", lambda: valid(lambda r: r["assets"][0].update(sha256="0" * 64)), (invalid, "checksum mismatch"))
    case("07 altered Markdown", lambda: h.verify_markdown(left, h.markdown(left) + b"changed"), (invalid, "differs"))
    case("08 altered JSON", lambda: h.verify_markdown(alter(lambda r: r.update(reason="changed")), h.markdown(left)), (invalid, "differs"))
    case("09 duplicate ID", lambda: h.validate_batch([left, left], ROOT), (invalid, "duplicate handoff ID"))
    case("10 permitted test action", lambda: gate(left, "PASS"))
    case("11 pending approval", lambda: gate(alter(lambda r: r["approval"].update(state="pending")), "BLOCKED"))
    case("12 attempted scope expansion", lambda: gate(alter(lambda r: (r["next"].update(action="production_write"),
                r["approval"]["allowed"].append("production_write"), r["approval"]["prohibited"].remove("production_write"))), "BLOCKED"))
    case("13 prohibition overrides allowance", lambda: gate(alter(lambda r: r["approval"]["prohibited"].append(h.TEST_ACTION)), "BLOCKED"))
    case("14 all evidence states and origins preserved", lambda: statuses(left))
    case("15 unknown status", lambda: valid(lambda r: r["evidence"][0].update(status="DONE")), (invalid, "invalid status"))
    case("16 external target", lambda: h.markdown(alter(lambda r: r["delivery"].update(target="external"))), (h.Blocked, "external delivery"))
    case("17 restricted classification", lambda: h.markdown(alter(lambda r: r["delivery"].update(sensitivity="restricted"))), (h.Blocked, "restricted content"))
    case("18 sample secret", lambda: h.markdown(alter(lambda r: r.update(reason="token=FAKE-TEST-ONLY"))), (h.Blocked, "credential marker"))
    case("19 path outside root", lambda: valid(lambda r: r["assets"][0].update(path="../fixture")), (invalid, "inside the reference root"))
    case("20 independent package", independent)
    case("21 historical evidence without reference", lambda: valid(lambda r: r["evidence"][0].update(source="unlinked")), (invalid, "verified asset"))
    return outcomes


if __name__ == "__main__":
    results = run()
    for name, state, detail in results:
        print(f"{state} | {name} | {detail}")
    raise SystemExit(any(state == "FAIL" for _, state, _ in results))
