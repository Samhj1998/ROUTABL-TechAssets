"""Validate and render local CW-01 simulations. No action execution."""
import argparse
from datetime import datetime
import hashlib
import json
from pathlib import Path
import re

HERE = Path(__file__).resolve().parent
TEST_ACTION = "validate_local_fixture"
SECRETS = re.compile(r"PRIVATE KEY-----|Bearer\s+\S+|(?:password|api[_ -]?key|token)\s*[:=]\s*\S+", re.I)


class Invalid(ValueError):
    pass


class Blocked(ValueError):
    pass


def unique_keys(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise Invalid(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=unique_keys)


def sha(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def shape(value, rule, where):
    types = {"object": dict, "array": list, "string": str}
    if "type" in rule and not isinstance(value, types[rule["type"]]):
        raise Invalid(f"{where}: expected {rule['type']}")
    if "const" in rule and value != rule["const"]:
        raise Invalid(f"{where}: unexpected value")
    if "enum" in rule and value not in rule["enum"]:
        raise Invalid(f"{where}: invalid status or classification")
    if "pattern" in rule and not re.fullmatch(rule["pattern"], value):
        raise Invalid(f"{where}: invalid format")
    if "format" in rule:
        try:
            stamp = datetime.fromisoformat(value.replace("Z", "+00:00"))
            if stamp.utcoffset() is None or "T" not in value:
                raise ValueError
        except ValueError:
            raise Invalid(f"{where}: expected timestamp with timezone") from None
    if "minLength" in rule and not value.strip():
        raise Invalid(f"{where}: empty text")
    if "minItems" in rule and len(value) < rule["minItems"]:
        raise Invalid(f"{where}: too few items")
    if "items" in rule:
        for index, item in enumerate(value):
            shape(item, rule["items"], f"{where}[{index}]")
    if "properties" in rule:
        missing = set(rule["required"]) - value.keys()
        extra = value.keys() - rule["properties"].keys()
        if missing or extra:
            raise Invalid(f"{where}: missing={sorted(missing)}, extra={sorted(extra)}")
        for key, item in value.items():
            shape(item, rule["properties"][key], f"{where}.{key}")


def validate_record(record, root):
    schema = read_json(HERE / "schema.json")
    for rule in schema["oneOf"]:
        if isinstance(record, dict) and record.get("direction") == rule["properties"]["direction"]["const"]:
            shape(record, rule, "record")
            break
    else:
        raise Invalid("record.direction: unknown or missing")
    paths = set()
    for asset in record["assets"]:
        rel = Path(asset["path"])
        if rel.is_absolute() or ".." in rel.parts:
            raise Invalid("asset path must be inside the reference root")
        path = root / rel
        if not path.resolve().is_relative_to(root) or not path.is_file():
            raise Invalid(f"asset missing or outside reference root: {rel}")
        if sha(path) != asset["sha256"]:
            raise Invalid(f"asset checksum mismatch: {rel}")
        paths.add(asset["path"])
    for evidence in record["evidence"]:
        if evidence["origin"] == "historical" and evidence["source"] not in paths:
            raise Invalid("historical evidence must reference a verified asset")


def execution_gate(record):
    approval, action = record["approval"], record["next"]["action"]
    if (approval["state"] != "approved_test" or action != TEST_ACTION
            or action not in approval["allowed"] or action in approval["prohibited"]):
        return "BLOCKED"
    return "PASS"


def delivery_gate(record):
    delivery = record["delivery"]
    if delivery["target"] == "external":
        raise Blocked("external delivery is disabled")
    if delivery["sensitivity"] == "restricted" or SECRETS.search(json.dumps(record, ensure_ascii=False)):
        raise Blocked("restricted content or a credential marker cannot be rendered")


def markdown(record):
    delivery_gate(record)
    source, target = record["from"], record["to"]
    lines = [f"# {source['mode']} → {target['mode']} | {record['id']}",
             "", "> 모의 인계 기록. 실제 발급·실행 승인 아님.",
             "", f"> 모의 실행 판단 **{execution_gate(record)}**. 프로그램은 작업을 실행하지 않는다.", ""]
    sections = [
        ("기본 정보", ["schema_version", "id", "record_kind", "direction", "from", "to", "reason", "created_at"]),
        ("결정과 남은 작업", ["decisions", "remaining"]),
        ("참조 자산과 증거", ["assets", "evidence"]),
        ("승인과 전달 제한", ["approval", "delivery"]),
        ("다음 작업과 복귀 조건", ["next", "details"]),
    ]

    def bullet(key, value, level=0):
        prefix = "    " * level + "- "
        if isinstance(value, dict):
            lines.append(prefix + f"**{key}**")
            for field in sorted(value):
                bullet(field, value[field], level + 1)
        elif isinstance(value, list):
            lines.append(prefix + f"**{key}**" + (" — []" if not value else ""))
            for index, item in enumerate(value, 1):
                bullet(str(index), item, level + 1)
        else:
            safe = json.dumps(value, ensure_ascii=False)
            safe = safe.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            safe = re.sub(r"([\\*_{}\[\]\x60])", r"\\\1", safe)
            lines.append(prefix + f"**{key}** — {safe}")

    for title, keys in sections:
        lines.extend([f"## {title}", ""])
        for key in keys:
            bullet(key, record[key])
        lines.append("")
    return "\n".join(lines).encode("utf-8")


def validate_batch(records, root):
    ids = set()
    for record in records:
        validate_record(record, root)
        if record["id"] in ids:
            raise Invalid(f"duplicate handoff ID: {record['id']}")
        ids.add(record["id"])


def verify_markdown(record, data):
    if markdown(record) != data:
        raise Invalid("Markdown differs from canonical JSON rendering")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("operation", choices=["render", "verify"])
    parser.add_argument("--root", type=Path, default=HERE.parents[1])
    parser.add_argument("records", nargs="+", type=Path)
    args = parser.parse_args()
    try:
        paths = [path.resolve() for path in args.records]
        if any(path.parent != HERE or path.suffix != ".json" for path in paths):
            raise Invalid("record files must be .json files in the PoC directory")
        records = [read_json(path) for path in paths]
        validate_batch(records, args.root.resolve())
        rendered = [markdown(record) for record in records]
        for path, record, content in zip(paths, records, rendered):
            output = path.with_suffix(".md")
            if args.operation == "render":
                with output.open("xb") as stream:
                    stream.write(content)
            else:
                verify_markdown(record, output.read_bytes())
            print(f"{record['id']}: PASS; simulated execution {execution_gate(record)}")
    except Blocked as error:
        parser.exit(3, f"BLOCKED: {error}\n")
    except (ValueError, OSError) as error:
        parser.exit(2, f"FAIL: {error}\n")


if __name__ == "__main__":
    main()
