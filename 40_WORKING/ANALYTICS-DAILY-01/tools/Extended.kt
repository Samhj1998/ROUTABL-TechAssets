// v1.2.0 fixture bridge. Data algorithms run unchanged originals; UI-only
// arithmetic below is explicitly mapped to its hashed Android source in spec.
import com.routivel.analytics.data.*
import com.routivel.analytics.export.*
import com.routivel.analytics.ui.Format
import kotlin.math.roundToInt

private fun rangeValue(r: DateRange) = mapOf("start" to r.start, "end" to r.end, "days" to r.days)
private fun months(rows: List<Pair<String, Long?>>) = rows.map { mapOf("month" to it.first, "billing" to it.second) }
private fun pairs(rows: List<Pair<String, Int>>) = rows.map { mapOf("name" to it.first, "count" to it.second) }
private fun spot(s: WaitSpot) = mapOf("dong" to s.dong, "count" to s.count, "totalMinutes" to s.totalMinutes, "averageMinutes" to s.averageMinutes)
private fun flowView(f: FlowStats) = mapOf(
    "linkedPercent" to if (f.linkBase > 0) Math.round(f.linked * 100.0 / f.linkBase) else null,
    "overlappedPercent" to if (f.timedBase > 0) Math.round(f.overlapped * 100.0 / f.timedBase) else null,
    "missingCompletionPairs" to f.pairs - f.timedBase,
    "locationState" to if (f.spots.isNotEmpty()) "located" else if (f.waits > 0) "unlocated" else "no_waits",
    "topSpots" to f.spots.take(8).map(::spot),
    "longestSpot" to f.spots.maxByOrNull { it.totalMinutes }?.let(::spot)
)

// PeriodController.range: only clock acquisition replaced by fixed request.today.
private fun presets(request: Map<String, Any?>): Map<String, Any?> {
    val today = request["today"] as String
    val month = Dates.month(today)
    val last = Dates.addMonths(month, -1)
    return mapOf(
        "THIS_MONTH" to rangeValue(DateRange(Dates.firstDay(month), today)),
        "LAST_MONTH" to rangeValue(DateRange(Dates.firstDay(last), Dates.lastDay(last))),
        "LAST_3_MONTHS" to rangeValue(DateRange(Dates.firstDay(Dates.addMonths(month, -2)), today)),
        "CUSTOM" to rangeValue(DateRange(request["customStart"] as? String ?: today, request["customEnd"] as? String ?: today))
    )
}

@Suppress("UNCHECKED_CAST")
fun extended(data: AnalyticsData, range: DateRange, request: Map<String, Any?>): Map<String, Any?> {
    val ins = Insights(data)
    val beforeRange = Insights.previous(range)
    val now = ins.stats(range)
    val before = ins.stats(beforeRange)
    fun compare(a: Number?, b: Number?) = mapOf("current" to a, "previous" to b,
        "percent" to Format.percent(a?.toDouble(), b?.toDouble()))
    val counts = ins.weekdayHourCounts(range)
    // TimeFragment.renderHeatmap: Sunday conditional; top 3 only visible hours.
    val order = listOf(2, 3, 4, 5, 6, 7) + if (counts[1].any { it > 0 }) listOf(1) else emptyList()
    val usedHours = (0..23).filter { h -> order.any { counts[it][h] > 0 } }
    val from = minOf(8, usedHours.minOrNull() ?: 8).coerceAtLeast(5)
    val to = maxOf(19, usedHours.maxOrNull() ?: 19).coerceAtMost(22)
    val top = order.flatMap { day -> (from..to).map { h -> Triple(day, h, counts[day][h]) } }
        .filter { it.third > 0 }.sortedByDescending { it.third }.take(3)
    val averages = ins.weekdayAverages(range)
    val keys: Map<String, (DispatchRecord) -> String> = linkedMapOf("requester" to { it.requester }, "dept" to { it.dept }, "dest" to { it.dest })
    val customerGroups = keys.map { (group, key) ->
        val rows = ins.ranking(range, key)
        val previous = ins.ranking(beforeRange, key).associateBy { it.name }
        val total = rows.sumOf { it.amount ?: 0L }
        val first = rows.take(3)
        val rest = total - first.sumOf { it.amount ?: 0L }
        val parts = if (total > 0) first.map { it.name to (it.amount ?: 0L) } + if (rest > 0) listOf("나머지" to rest) else emptyList() else emptyList()
        mapOf("group" to group, "customerCount" to rows.size, "knownTotal" to total,
            "topSharePercent" to if (total > 0) (first.sumOf { it.amount ?: 0L } * 100.0 / total).roundToInt() else null,
            "parts" to parts.map { mapOf("name" to it.first, "amount" to it.second, "percent" to (it.second * 100.0 / total).roundToInt()) },
            "rows" to rows.mapIndexed { i, r ->
                val old = previous[r.name]
                val selected = ins.recordsIn(range).filter { key(it).trim() == r.name }
                mapOf("rank" to i + 1, "name" to r.name, "count" to r.count, "amount" to r.amount,
                    "sharePercent" to if (total > 0 && r.amount != null) (r.amount * 100.0 / total).roundToInt() else null,
                    "previousAmount" to old?.amount, "new" to (old == null),
                    "percent" to Format.percent(r.amount?.toDouble(), old?.amount?.toDouble()),
                    "detail" to mapOf("monthly" to months(ins.monthlyFor(r.name, key, Dates.month(range.end), 6)),
                        "routes" to pairs(ins.routes(selected).take(5)), "payments" to pairs(ins.payments(selected))))
            })
    }
    val sleepInput = request["sleep"] as? Map<String, Any?> ?: emptyMap()
    fun cached(row: Map<String, Any?>) = CachedSleep(row["id"] as String,
        SleepSession((row["startMillis"] as Number).toLong(), (row["endMillis"] as Number).toLong()))
    val initial = (sleepInput["current"] as? List<Map<String, Any?>>).orEmpty().map(::cached)
    val changes = (sleepInput["changes"] as? List<Map<String, Any?>>).orEmpty().map {
        if (it["op"] == "delete") SleepChange.Delete(it["id"] as String) else SleepChange.Upsert(cached(it))
    }
    val merged = SleepCache.merge(initial, changes)
    val recent = sleepInput["recent"] as? List<Map<String, Any?>>
    val sessions = if (recent == null) merged else SleepCache.replaceRecent(merged, recent.map(::cached), (sleepInput["replaceStartMillis"] as Number).toLong())
    val nowMillis = (request["nowMillis"] as Number).toLong()
    // SleepReader.publish: only clock acquisition replaced; invalid duration filtered by original.
    val hours = SleepAnalysis.byWakeDate(sessions.map { it.session }.filter { it.endMillis <= nowMillis })
    val report = SleepAnalysis.report(ins, range, hours)
    val todayHours = hours[request["today"] as String]
    val banner = todayHours != null && todayHours < 6 && !SleepAnalysis.isWeekend(nowMillis)
    val trend = report.days.sortedBy { it.date }
    val probes = (request["dayKeys"] as List<String>).map { key ->
        val t = ins.day(key)
        val average = ins.sameWeekdayAverage(key)
        mapOf("date" to key, "sleepHours" to hours[key], "sleepText" to SleepAnalysis.daySleepText(hours[key]),
            "sameWeekdayPercent" to if (average == null || average <= 0 || t.billing == null || t.count == 0) null else Format.percent(t.billing.toDouble(), average.toDouble()),
            "flow" to flowView(ins.dayFlow(key)),
            "timeline" to ins.timeline(key).map { item -> when (item) {
                is Insights.TimelineItem.Wait -> mapOf("kind" to "wait", "minutes" to item.minutes, "dong" to item.dong)
                is Insights.TimelineItem.Ride -> item.record.let { r -> mapOf("kind" to "ride", "id" to r.id,
                    "dispatchTime" to r.dispatchTime, "dept" to r.dept, "deptDong" to r.deptDong,
                    "dest" to r.dest, "destDong" to r.destDong, "totalFare" to r.totalFare,
                    "requester" to r.requester, "payment" to r.payment, "car" to r.car, "note" to r.note) }
            } })
    }
    return mapOf(
        "periods" to mapOf("presets" to presets(request), "previous" to rangeValue(beforeRange)),
        "summary" to mapOf("billing" to compare(now.billing, before.billing),
            "count" to mapOf("current" to now.count, "previous" to before.count, "delta" to now.count - before.count, "text" to Format.countDelta(now.count, before.count)),
            "perHour" to compare(now.perHour, before.perHour), "perKm" to compare(now.perKm, before.perKm),
            "avgFare" to compare(now.avgFare, before.avgFare), "countPerDay" to compare(now.countPerDay, before.countPerDay),
            "hoursPerDay" to compare(now.hoursPerDay, before.hoursPerDay), "kmPerDay" to compare(now.kmPerDay, before.kmPerDay),
            "monthly" to months(ins.monthlyBilling(Dates.month(range.end), 6))),
        "customerGroups" to customerGroups,
        "time" to mapOf("counts" to (1..7).map { counts[it].toList() }, "rowTotals" to (1..7).map { counts[it].sum() },
            "visibleDays" to order, "fromHour" to from, "toHour" to to,
            "top" to top.map { mapOf("weekday" to it.first, "hour" to it.second, "count" to it.third) },
            "weekdayAverages" to listOf(2, 3, 4, 5, 6, 7, 1).map { day -> mapOf("weekday" to day, "billing" to averages[day]?.first, "workDays" to (averages[day]?.second ?: 0)) }),
        "routes" to ins.routeStats(range).map { mapOf("route" to it.route, "count" to it.count, "averageFare" to it.averageFare, "mainCar" to it.mainCar) },
        "flowDisplay" to flowView(ins.flow(range)), "dayDetails" to probes,
        "sleep" to mapOf("cache" to sessions.map { mapOf("id" to it.id, "startMillis" to it.session.startMillis, "endMillis" to it.session.endMillis) },
            "byWakeDate" to hours, "unrecordedWorkDays" to report.days.count { it.hours == null },
            "groups" to report.groups.map { mapOf("band" to it.band.name, "days" to it.days, "average" to it.average, "lowPercent" to it.lowPercent) },
            "days" to report.days.map { mapOf("date" to it.date, "hours" to it.hours, "billing" to it.billing) },
            "lowDays" to report.lowDays.map { mapOf("date" to it.date, "cause" to SleepAnalysis.cause(it.hours, it.endMinute, report.averageEnd, it.partnerBilling, report.averagePartner)) },
            "banner" to mapOf("visible" to banner, "band" to if (banner) SleepAnalysis.band(todayHours!!).name else null),
            "trend" to mapOf("floor" to SleepAnalysis.FLOOR,
                "spanDays" to if (trend.isEmpty()) 0 else Dates.daysBetween(trend.first().date, trend.last().date) + 1,
                "points" to trend.mapIndexed { i, d -> mapOf("date" to d.date, "offsetDays" to Dates.daysBetween(trend.first().date, d.date), "billing" to d.billing, "hours" to d.hours,
                    "connectPrevious" to (i > 0 && d.hours != null && trend[i - 1].hours != null && Dates.daysBetween(trend[i - 1].date, d.date) == 1)) })),
        "qualityDisplay" to mapOf("summaryRecordCount" to data.days.size),
        "exports" to ExportTables.build(data, range, ExportKind.values().toSet()).map {
            mapOf("name" to it.name, "fileName" to it.fileName, "header" to it.header, "rows" to it.rows) },
        "percentProbes" to (request["percentProbes"] as? List<Map<String, Any?>>).orEmpty().map {
            Format.percent((it["current"] as? Number)?.toDouble(), (it["previous"] as? Number)?.toDouble()) },
        "causeProbes" to (request["causeProbes"] as? List<Map<String, Any?>>).orEmpty().map {
            SleepAnalysis.cause((it["hours"] as? Number)?.toDouble(), (it["endMinute"] as? Number)?.toInt(),
                (it["averageEnd"] as? Number)?.toDouble(), (it["partner"] as? Number)?.toLong(), (it["averagePartner"] as? Number)?.toDouble()) }
    )
}
