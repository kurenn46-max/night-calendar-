package com.nightcalendar.core

import java.time.LocalDate
import java.time.temporal.ChronoUnit

/** Japanese civil days from the NAOJ almanacs. Outside 2025–2027 the result is unknown. */
object Rokuyo {
    enum class Day(val label: String) {
        SENSHO("先勝"), TOMOBIKI("友引"), SENBU("先負"), BUTSUMETSU("仏滅"), TAIAN("大安"), SHAKKO("赤口")
    }

    data class LunarDate(val month: Int, val day: Int, val isLeapMonth: Boolean) {
        // A leap month has the same first-day assignment as its ordinary counterpart.
        val rokuyo: Day get() = Day.entries[(month + day - 2) % Day.entries.size]
    }

    private data class MonthStart(val date: LocalDate, val month: Int, val leap: Boolean)

    val supportedYears = 2025..2027

    // New moons in Japan Standard Time. Month numbers are anchored to winter solstice (month 11).
    // In 2025 the month starting July 25 contains no principal solar term and repeats month 6.
    private val starts = listOf(
        "2024-12-31" to 12,
        "2025-01-29" to 1, "2025-02-28" to 2, "2025-03-29" to 3,
        "2025-04-28" to 4, "2025-05-27" to 5, "2025-06-25" to 6, "2025-07-25" to -6,
        "2025-08-23" to 7, "2025-09-22" to 8, "2025-10-21" to 9,
        "2025-11-20" to 10, "2025-12-20" to 11,
        "2026-01-19" to 12, "2026-02-17" to 1, "2026-03-19" to 2,
        "2026-04-17" to 3, "2026-05-17" to 4, "2026-06-15" to 5,
        "2026-07-14" to 6, "2026-08-13" to 7, "2026-09-11" to 8,
        "2026-10-11" to 9, "2026-11-09" to 10, "2026-12-09" to 11,
        "2027-01-08" to 12, "2027-02-07" to 1, "2027-03-08" to 2,
        "2027-04-07" to 3, "2027-05-06" to 4, "2027-06-05" to 5,
        "2027-07-04" to 6, "2027-08-02" to 7, "2027-09-01" to 8,
        "2027-09-30" to 9, "2027-10-29" to 10, "2027-11-28" to 11, "2027-12-28" to 12,
    ).map { (date, month) -> MonthStart(LocalDate.parse(date), kotlin.math.abs(month), month < 0) }

    fun on(date: LocalDate): LunarDate? {
        if (date.year !in supportedYears) return null
        val index = starts.binarySearchBy(date) { it.date }
        val start = starts[if (index < 0) -index - 2 else index]
        val day = ChronoUnit.DAYS.between(start.date, date).toInt() + 1
        return LunarDate(start.month, day, start.leap)
    }
}
