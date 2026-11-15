#!/usr/bin/env python3
"""Run the read-only Kotlin originals; generate or byte-compare fixture expectations.

No network, Gradle, Firebase, app execution, cleanup, or writes outside this asset.
Python only reads JSON, emits typed Kotlin input literals, and handles result bytes.
The Kotlin originals perform every date, amount, sorting, and CSV calculation.
"""
import argparse
import base64
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
BUILD = ROOT / "tools" / ".build"


def literal(value):
    if value is None:
        return "null"
    if isinstance(value, bool):
        return str(value).lower()
    if isinstance(value, str):
        return json.dumps(value, ensure_ascii=False).replace("$", "\\$")
    if isinstance(value, int):
        if not -(2**63) < value < 2**63:
            raise ValueError("Fixture integer must fit Kotlin Long")
        return str(value) + "L"
    if isinstance(value, float):
        return json.dumps(value, allow_nan=False)
    if isinstance(value, dict):
        return "mapOf<String, Any?>(" + ",".join(
            literal(k) + " to " + literal(v) for k, v in value.items()
        ) + ")"
    raise ValueError("Only scalar Firestore fixture fields are supported")


KOTLIN = r'''
import com.routivel.shared.SettlementRules
import com.routivel.shared.SettlementFare
import com.routivel.shared.SettlementCsv
import com.routivel.shared.SettlementExportRow
import java.time.Instant
import java.util.Base64
import java.util.Date

// Adapter of DriverSettlement.kt:13-18 and DispatchExportController.kt:294-305.
// Input documents are already within the authorized rider query scope.
// JSON timestamp is an ISO instant standing in for Firestore Timestamp.toDate().
private fun runCase(
    name: String, targetMonthKey: String, targetCustomer: String,
    documents: List<Pair<String, Map<String, Any?>>>,
    columns: List<Pair<String, String>>
) {
    val rows = documents.mapNotNull { (id, data) ->
        if (!SettlementRules.includes((data["status"] as? String).orEmpty(), data["isDeleted"] == true)) return@mapNotNull null
        val recordedAt = (data["timestamp"] as? String)?.let { Date.from(Instant.parse(it)) }
        val date = SettlementRules.dateKey(data["dispatchTime"] as? String, recordedAt) ?: return@mapNotNull null
        if (targetMonthKey != "ALL" && date.take(7) != targetMonthKey) return@mapNotNull null
        if (targetCustomer != "전체 고객사" && data["requester"] as? String != targetCustomer) return@mapNotNull null
        SettlementExportRow(
            id, date, SettlementRules.time(data["dispatchTime"] as? String),
            SettlementCsv.columns.associate { (_, key) -> key to (data[key]?.toString() ?: "") },
            SettlementFare(SettlementRules.amount(data["totalFare"]), SettlementRules.amount(data["baseFare"]),
                SettlementRules.amount(data["extraFare"]), if (data["takSong"] == null) 0L else SettlementRules.amount(data["takSong"]))
        )
    }
    try {
        // Empty rows use the formatter's identical refusal instead of the UI Toast.
        val csv = SettlementCsv.create(rows, columns)
        println(name + "\tcsv\t" + Base64.getEncoder().encodeToString(csv.toByteArray(Charsets.UTF_8)))
    } catch (error: IllegalArgumentException) {
        // Stable fixture codes wrap actual Kotlin exceptions; Kotlin has no native codes.
        // Never serialize exception messages, which may contain caller-provided fields.
        val code = when {
            error.message == "해당 조건에 맞는 배차 내역이 없습니다." -> "E_NO_ROWS"
            error.message == "추출할 항목을 하나 이상 선택해 주세요." -> "E_COLUMNS_EMPTY"
            error.message == "배차 날짜를 확인해 주세요." -> "E_DATE_INVALID"
            error.message?.endsWith("운송료 구성 금액이 없거나 올바르지 않습니다.") == true -> "E_AMOUNT_INVALID"
            error.message?.endsWith("기본·추가·탁송 합계가 요금과 일치하지 않습니다.") == true -> "E_FARE_MISMATCH"
            error.message == "요금 합계를 확인해 주세요." -> "E_TOTAL_OVERFLOW"
            error.message == "총요금 합계를 확인해 주세요." -> "E_GRAND_TOTAL_OVERFLOW"
            columns.any { it !in SettlementCsv.columns } || columns.distinct().size != columns.size -> "E_COLUMNS_INVALID"
            else -> throw error
        }
        println(name + "\terror\t" + code)
    }
}
fun main() {
'''


def pairs(columns):
    return "listOf<Pair<String, String>>(" + ",".join(
        literal(name) + " to " + literal(key) for name, key in columns
    ) + ")"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true", help="Write expectations from Kotlin")
    mode.add_argument("--check", action="store_true", help="Regenerate and compare exact bytes")
    parser.add_argument("--source-root", type=Path, default=Path.home() / "StudioProjects/DISPATCH-One-Android")
    parser.add_argument("--kotlinc", default=os.environ.get("KOTLINC"))
    args = parser.parse_args()
    spec = json.loads((ROOT / "spec.json").read_text(encoding="utf-8"))
    source_root = args.source_root.expanduser().resolve()
    for source in spec["sources"]:
        actual = hashlib.sha256((source_root / source["path"]).read_bytes()).hexdigest()
        if actual != source["sha256"]:
            raise ValueError("Kotlin source drift: " + source["path"] + "; review spec/version and regenerate")
    compiler = args.kotlinc or shutil.which("kotlinc")
    if not compiler:
        bundled = Path("/Applications/Android Studio.app/Contents/plugins/Kotlin/kotlinc/bin/kotlinc")
        compiler = str(bundled) if bundled.is_file() else None
    if not compiler:
        raise RuntimeError("Kotlin compiler unavailable; no expectations will be written")
    inputs = sorted((ROOT / "cases").glob("*.input.json"))
    if len(inputs) < 12:
        raise ValueError("At least 12 cases required")
    default_columns = [(c["name"], c["source_field"]) for c in spec["columns"]]
    code = KOTLIN + "check(SettlementCsv.columns == " + pairs(default_columns) + ")\n"
    names = []
    for path in inputs:
        case = json.loads(path.read_text(encoding="utf-8"))
        name = path.name.removesuffix(".input.json")
        if case["case_id"] != name or case["spec_version"] != spec["version"]:
            raise ValueError("Case identity/version mismatch: " + name)
        names.append(name)
        request = case["request"]
        docs = "listOf<Pair<String, Map<String, Any?>>>(" + ",".join(
            literal(doc["id"]) + " to " + literal(doc["data"]) for doc in case["documents"]
        ) + ")"
        columns = pairs(request["selectedColumns"]) if "selectedColumns" in request else "SettlementCsv.columns"
        code += "runCase(" + ",".join([
            literal(name), literal(request["targetMonthKey"]), literal(request["targetCustomer"]), docs, columns
        ]) + ")\n"
    code += "}\n"
    BUILD.mkdir(parents=True, exist_ok=True)
    bridge = BUILD / "FixtureMain.kt"
    bridge.write_text(code, encoding="utf-8")
    env = os.environ.copy()
    env["TMPDIR"] = str(BUILD)
    env["JAVA_OPTS"] = "-Djava.io.tmpdir=" + str(BUILD) + " -Djansi.mode=strip -Djansi.passthrough=true"
    compiled = BUILD / "fixtures.jar"
    shared = source_root / "shared/kotlin/com/routivel/shared"
    subprocess.run([
        compiler, str(shared / "SettlementRules.kt"), str(shared / "SettlementCsv.kt"),
        str(bridge), "-include-runtime", "-d", str(compiled)
    ], check=True, cwd=BUILD, env=env)
    result = subprocess.run([
        "java", "-Djava.io.tmpdir=" + str(BUILD), "-jar", str(compiled)
    ], check=True, capture_output=True, text=True, cwd=BUILD, env=env)
    outputs = {}
    for line in result.stdout.splitlines():
        name, kind, payload = line.split("\t", 2)
        if name in outputs or kind not in ("csv", "error"):
            raise ValueError("Invalid Kotlin runner output")
        if kind == "csv":
            content = base64.b64decode(payload, validate=True)
            suffix = ".expected.csv"
            if not content.startswith(b"\xef\xbb\xbf") or not content.endswith(b"\n"):
                raise ValueError("CSV BOM/LF missing")
        else:
            content = (json.dumps({"error": {"code": payload}}, indent=2) + "\n").encode("utf-8")
            suffix = ".expected.error.json"
        outputs[name] = (ROOT / "cases" / (name + suffix), content)
    if sorted(outputs) != names:
        raise ValueError("Kotlin runner did not return every case")
    expected_paths = {p for p, _ in outputs.values()}
    stale = set((ROOT / "cases").glob("*.expected.*")) - expected_paths
    if stale:
        raise ValueError("Unexpected old expectation files; no files deleted: " + ", ".join(p.name for p in stale))
    differences = []
    for name, (path, content) in outputs.items():
        if args.write:
            path.write_bytes(content)
        elif not path.is_file() or path.read_bytes() != content:
            differences.append(name)
    if differences:
        raise ValueError("Byte differences: " + ", ".join(differences))
    csv_count = sum(p.suffix == ".csv" for p, _ in outputs.values())
    print(f"Kotlin originals executed: {len(outputs)} cases ({csv_count} CSV, {len(outputs)-csv_count} errors); "
          + ("expectations written" if args.write else "byte diff 0"))


if __name__ == "__main__":
    try:
        main()
    except (ValueError, RuntimeError, OSError, subprocess.CalledProcessError) as error:
        print("FAILED: " + str(error), file=sys.stderr)
        sys.exit(1)
