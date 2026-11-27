package com.nightcalendar

import java.time.LocalDate

/** Explicit Japanese national holiday calendar. Outside the supported years,
 * callers must not interpret a null result as a verified non-holiday. */
object JapanHolidays {
    val supportedYears = 2026..2027
    private val dates = mapOf(
        2026 to "01-01 01-12 02-11 02-23 03-20 04-29 05-03 05-04 05-05 05-06 07-20 08-11 09-21 09-22 09-23 10-12 11-03 11-23",
        2027 to "01-01 01-11 02-11 02-23 03-21 03-22 04-29 05-03 05-04 05-05 07-19 08-11 09-20 09-23 10-11 11-03 11-23"
    ).flatMap { (year, days) -> days.split(" ").map { LocalDate.parse("$year-$it") } }.toSet()

    fun isSupported(year: Int): Boolean = year in supportedYears
    fun isHoliday(date: LocalDate): Boolean = date in dates
}
