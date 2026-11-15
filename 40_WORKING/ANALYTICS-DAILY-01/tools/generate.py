#!/usr/bin/env python3
"""Compile unchanged Kotlin originals, then write or byte-check JSON expectations.

No network, Gradle, Firebase, cleanup, or writes outside this asset. Expected
values are never calculated in Python. Source hashes are checked before/after.
"""
import argparse
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
        if not -(2**63) <= value < 2**63:
            raise ValueError("Fixture integer must fit Kotlin Long")
        return "Long.MIN_VALUE" if value == -(2**63) else str(value) + "L"
    if isinstance(value, float):
        return json.dumps(value, allow_nan=False)
    if isinstance(value, list):
        return "listOf<Any?>(" + ",".join(map(literal, value)) + ")"
    if isinstance(value, dict):
        if set(value) in ({"$date"}, {"$timestamp"}):
            tag = next(iter(value))
            date = "Date.from(Instant.parse(" + literal(value[tag]) + "))"
            return date if tag == "$date" else "Timestamp(" + date + ")"
        return "mapOf<String, Any?>(" + ",".join(
            literal(k) + " to " + literal(v) for k, v in value.items()
        ) + ")"
    raise ValueError("Unsupported fixture value")


KOTLIN = r'''
import com.routivel.analytics.data.*
import com.routivel.shared.SettlementRules
import java.time.Instant
import java.util.Date
import java.util.Locale

// Fixture-only stand-in for Timestamp.toDate(); never connects to Firebase.
private class Timestamp(private val date: Date) { fun toDate(): Date = date }

// FirestoreReader's conversion methods are inserted verbatim below.
__READER__

private fun quote(s: String): String = buildString {
    append('"')
    for (c in s) when (c) {
        '"' -> append("\\\""); '\\' -> append("\\\\")
        '\n' -> append("\\n"); '\r' -> append("\\r"); '\t' -> append("\\t")
        else -> if (c.code < 32) append("\\u%04x".format(Locale.ROOT, c.code)) else append(c)
    }
    append('"')
}
private fun json(v: Any?): String = when (v) {
    null -> "null"
    is String -> quote(v)
    is Boolean, is Byte, is Short, is Int, is Long -> v.toString()
    is Double -> { check(v.isFinite()); v.toString() }
    is Map<*, *> -> v.entries.joinToString(",", "{", "}") { quote(it.key as String) + ":" + json(it.value) }
    is Iterable<*> -> v.joinToString(",", "[", "]") { json(it) }
    else -> error("Unsupported JSON type")
}
private fun total(t: DayTotal) = mapOf(
    "date" to t.date, "count" to t.count, "billing" to t.billing,
    "takSong" to t.takSong, "outsourcing" to t.outsourcing,
    "expense" to t.expense, "net" to t.net
)
private fun stats(t: PeriodStats) = mapOf(
    "count" to t.count, "billing" to t.billing, "expense" to t.expense, "net" to t.net,
    "workDays" to t.workDays, "timedDays" to t.timedDays, "hours" to t.hours,
    "billingOnTimedDays" to t.billingOnTimedDays, "perHour" to t.perHour,
    "avgFare" to t.avgFare, "countPerDay" to t.countPerDay,
    "hoursPerDay" to t.hoursPerDay, "perWorkDay" to t.perWorkDay,
    "kmDays" to t.kmDays, "km" to t.km, "billingOnKmDays" to t.billingOnKmDays,
    "perKm" to t.perKm, "kmPerDay" to t.kmPerDay
)
private fun customers(rows: List<CustomerRow>) = rows.map {
    mapOf("name" to it.name, "count" to it.count, "amount" to it.amount)
}
private fun hour(h: Insights.HourStat) = mapOf("hour" to h.hour, "count" to h.count, "billing" to h.billing)

// Minimal non-Android bridge of CalendarFragment.kt:133-146 (no UI layout).
private fun calendar(ins: Insights, month: String): Map<String, Any?> {
    val first = Dates.firstDay(month)
    val last = Dates.lastDay(month)
    val gridStart = Dates.addDays(first, -(Dates.weekday(first) - 1))
    val gridEnd = Dates.addDays(last, 7 - Dates.weekday(last))
    val weekCount = (Dates.daysBetween(gridStart, gridEnd) + 1) / 7
    val weeks = (0 until weekCount).map { week ->
        val keys = (0..6).map { Dates.addDays(gridStart, week * 7 + it) }
        val totals = keys.map { ins.day(it) }
        mapOf("keys" to keys, "count" to totals.sumOf { it.count },
            "billing" to SettlementRules.sum(totals.map { it.billing }))
    }
    return mapOf("gridStart" to gridStart, "gridEnd" to gridEnd, "weeks" to weeks)
}

private fun runCase(name: String, version: String, request: Map<String, Any?>,
    documents: List<Pair<String, Map<String, Any?>>>,
    summaries: List<Pair<String, Map<String, Any?>>>) {
    val records = documents.map { (id, d) -> toDispatch(id, d) }
    val days = summaries.mapNotNull { (id, d) -> toDay(id, d) }
    val ins = Insights(AnalyticsData("synthetic-rider", 0L, records, days))
    val range = DateRange(request["start"] as String, request["end"] as String)
    val month = request["month"] as String
    val today = request["today"] as String
    val nowMinute = (request["nowMinute"] as Number).toInt()
    val probes = request["dayKeys"] as List<*>
    // Use only non-sleep projections of the real report; no cause or sleep outputs.
    val report = SleepAnalysis.report(ins, range, emptyMap())
    val q = DailyStats.quality(records)
    val result = mapOf(
        "case_id" to name, "spec_version" to version,
        "convertedDispatches" to records.map { r -> mapOf(
            "id" to r.id, "dispatchTime" to r.dispatchTime, "recordedAtMillis" to r.recordedAtMillis,
            "requester" to r.requester, "status" to r.status, "isDeleted" to r.isDeleted,
            "totalFare" to r.totalFare, "takSongCost" to r.takSongCost, "outsourcingCost" to r.outsourcingCost,
            "included" to DailyStats.included(r), "dateKey" to DailyStats.dateKey(r), "hour" to ins.hourOf(r)
        ) },
        "convertedSummaries" to days.map { d -> mapOf(
            "workDate" to d.workDate, "startTime" to d.startTime, "endTime" to d.endTime,
            "distanceKm" to d.distanceKm, "toll" to d.toll
        ) },
        "quality" to mapOf("documents" to q.documents, "included" to q.included,
            "deleted" to q.deleted, "notCompleted" to q.notCompleted, "unknownDate" to q.unknownDate,
            "unknownFare" to q.unknownFare, "firstDate" to q.firstDate, "lastDate" to q.lastDate),
        "daily" to ins.byDay.values.map(::total),
        "monthTotal" to total(DailyStats.month(ins.byDay, month)),
        "monthStats" to stats(ins.stats(DateRange(Dates.firstDay(month), Dates.lastDay(month)))),
        "periodStats" to stats(ins.stats(range)),
        "workDays" to ins.workDays(range).map { d -> mapOf(
            "date" to d.date, "start" to d.start, "end" to d.end, "hours" to d.hours,
            "billing" to d.billing, "perHour" to d.perHour, "perKm" to d.perKm
        ) },
        "floorReport" to mapOf("floor" to SleepAnalysis.FLOOR, "knownDays" to report.knownDays,
            "unknownBilling" to report.unknownBilling, "lowDates" to report.lowDays.map { it.date },
            "lowPercent" to report.lowPercent, "averageEnd" to report.averageEnd,
            "averagePartner" to report.averagePartner,
            "days" to report.days.map { d -> mapOf("date" to d.date, "billing" to d.billing,
                "end" to d.end, "endMinute" to d.endMinute, "partnerBilling" to d.partnerBilling) }),
        "customers" to customers(ins.customers(range)),
        "dayDetails" to probes.map { value ->
            val key = value as String
            val t = ins.day(key)
            val summary = ins.days[key]
            val hourly = ins.hourly(key)
            // CalendarFragment.kt:187-201, 219: fixed clock replaces only clock acquisition.
            val live = if (key == today) ins.hoursSoFar(key, nowMinute) else null
            val hours = ins.workHours(key) ?: live
            val peak = hourly.maxWithOrNull(compareBy<Insights.HourStat> { it.count }.thenBy { it.billing ?: 0L })
            mapOf("total" to total(t), "recordIds" to ins.records(key).map { it.id },
                "start" to summary?.startTime.orEmpty(), "end" to summary?.endTime.orEmpty(),
                "workHours" to ins.workHours(key), "liveHours" to live, "displayHours" to hours,
                "displayPerHour" to if (hours != null && t.billing != null && t.count > 0) (t.billing / hours).toLong() else null,
                "hourly" to hourly.map(::hour), "peak" to peak?.let(::hour),
                "customers" to customers(ins.customers(DateRange(key, key))),
                "sameWeekdayAverage" to ins.sameWeekdayAverage(key))
        },
        "calendar" to calendar(ins, month)
    )
    println(name + "\t" + json(result))
}
'''


def documents_literal(docs):
    return "listOf<Pair<String, Map<String, Any?>>>(" + ",".join(
        literal(d["id"]) + " to " + literal(d["data"]) for d in docs
    ) + ")"


def verify_sources(spec, source_root):
    for source in spec["sources"]:
        if hashlib.sha256((source_root / source["path"]).read_bytes()).hexdigest() != source["sha256"]:
            raise ValueError("Kotlin source drift: " + source["path"] + "; review spec/version")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true")
    mode.add_argument("--check", action="store_true")
    parser.add_argument("--source-root", type=Path, default=Path.home() / "StudioProjects/ROUTABL-Analytics-Android")
    parser.add_argument("--kotlinc", default=os.environ.get("KOTLINC"))
    args = parser.parse_args()
    spec = json.loads((ROOT / "spec.json").read_text(encoding="utf-8"))
    source_root = args.source_root.expanduser().resolve()
    verify_sources(spec, source_root)
    compiler = args.kotlinc or shutil.which("kotlinc")
    if not compiler:
        bundled = Path("/Applications/Android Studio.app/Contents/plugins/Kotlin/kotlinc/bin/kotlinc")
        compiler = str(bundled) if bundled.is_file() else None
    if not compiler:
        raise RuntimeError("Kotlin compiler unavailable; no expectations will be written")
    inputs = sorted((ROOT / "cases").glob("*.input.json"))
    if len(inputs) != 32:
        raise ValueError("Exactly 32 cases required for version 1.0.0")
    # Extract actual conversion code, not a reimplementation. Firebase listener
    # code and all imports/dependencies of the Android reader are omitted.
    reader_path = next(s["path"] for s in spec["sources"] if s["path"].endswith("/FirestoreReader.kt"))
    reader = (source_root / reader_path).read_text(encoding="utf-8")
    adapter = reader[reader.index("    private fun toDispatch("):reader.rfind("}")]
    code = KOTLIN.replace("__READER__", adapter)
    names = []
    calls = []
    for index, path in enumerate(inputs):
        case = json.loads(path.read_text(encoding="utf-8"))
        name = path.name.removesuffix(".input.json")
        if case["case_id"] != name or case["spec_version"] != spec["version"]:
            raise ValueError("Case identity/version mismatch: " + name)
        if not 0 <= case["request"]["nowMinute"] < 1440:
            raise ValueError("nowMinute outside fixed Seoul day")
        names.append(name)
        call = "runCase(" + ",".join([
            literal(name), literal(spec["version"]), literal(case["request"]),
            documents_literal(case["documents"]), documents_literal(case["dailySummaries"])
        ]) + ")"
        code += "\nprivate fun case" + str(index) + "() { " + call + " }\n"
        calls.append("case" + str(index) + "()")
    code += "\nfun main() { Locale.setDefault(Locale.ROOT); " + "; ".join(calls) + " }\n"
    BUILD.mkdir(parents=True, exist_ok=True)
    bridge = BUILD / "FixtureMain.kt"
    bridge.write_text(code, encoding="utf-8")
    env = os.environ.copy()
    env["TMPDIR"] = str(BUILD)
    env["JAVA_OPTS"] = "-Djava.io.tmpdir=" + str(BUILD) + " -Djansi.mode=strip -Djansi.passthrough=true"
    compiled = BUILD / "fixtures.jar"
    originals = [str(source_root / s["path"]) for s in spec["sources"] if s["role"] == "compiled_original"]
    subprocess.run([compiler, *originals, str(bridge), "-include-runtime", "-d", str(compiled)],
                   check=True, cwd=BUILD, env=env)
    result = subprocess.run(["java", "-Djava.io.tmpdir=" + str(BUILD), "-Duser.timezone=Asia/Seoul",
                             "-jar", str(compiled)], check=True, capture_output=True, text=True, cwd=BUILD, env=env)
    verify_sources(spec, source_root)
    outputs = {}
    for line in result.stdout.splitlines():
        name, payload = line.split("\t", 1)
        value = json.loads(payload)
        if name in outputs or value["case_id"] != name or value["spec_version"] != spec["version"]:
            raise ValueError("Invalid Kotlin runner output")
        outputs[name] = (json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n").encode("utf-8")
    if sorted(outputs) != names:
        raise ValueError("Kotlin runner did not return every case")
    expected_paths = {ROOT / "cases" / (name + ".expected.json") for name in names}
    if set((ROOT / "cases").glob("*.expected.*")) - expected_paths:
        raise ValueError("Unexpected old expectation files; no files deleted")
    differences = []
    for name, content in outputs.items():
        path = ROOT / "cases" / (name + ".expected.json")
        if args.write:
            path.write_bytes(content)
        elif not path.is_file() or path.read_bytes() != content:
            differences.append(name)
    if differences:
        raise ValueError("Byte differences: " + ", ".join(differences))
    print(f"Kotlin originals executed: {len(outputs)} cases; "
          + ("expectations written" if args.write else "byte diff 0")
          + f"; {len(spec['sources'])} source hashes unchanged")


if __name__ == "__main__":
    try:
        main()
    except (ValueError, RuntimeError, OSError, subprocess.CalledProcessError) as error:
        print("FAILED: " + str(error), file=sys.stderr)
        sys.exit(1)
