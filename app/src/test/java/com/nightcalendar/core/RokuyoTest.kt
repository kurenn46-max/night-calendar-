package com.nightcalendar.core

import java.time.LocalDate
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Test

class RokuyoTest {
    @Test fun lunarNewYearsAndTheirEves() {
        expect("2025-01-29", 1, 1, Rokuyo.Day.SENSHO)
        expect("2026-02-16", 12, 29, Rokuyo.Day.BUTSUMETSU)
        expect("2026-02-17", 1, 1, Rokuyo.Day.SENSHO)
        expect("2026-02-18", 1, 2, Rokuyo.Day.TOMOBIKI)
        expect("2027-02-06", 12, 30, Rokuyo.Day.TAIAN)
        // The 00:56 JST new moon was still February 6 in UTC.
        expect("2027-02-07", 1, 1, Rokuyo.Day.SENSHO)
    }

    @Test fun leapMonthRepeatsMonthSix() {
        expect("2025-06-25", 6, 1, Rokuyo.Day.SHAKKO)
        expect("2025-07-24", 6, 30, Rokuyo.Day.TAIAN)
        expect("2025-07-25", 6, 1, Rokuyo.Day.SHAKKO, leap = true)
        expect("2025-08-22", 6, 29, Rokuyo.Day.BUTSUMETSU, leap = true)
        expect("2025-08-23", 7, 1, Rokuyo.Day.SENSHO)
    }

    @Test fun naoTraditionalFestivals() {
        expect("2025-08-29", 7, 7, Rokuyo.Day.SENSHO)
        expect("2026-09-25", 8, 15, Rokuyo.Day.BUTSUMETSU)
        expect("2027-09-15", 8, 15, Rokuyo.Day.BUTSUMETSU)
    }

    @Test fun coverageDoesNotExtrapolate() {
        assertNull(Rokuyo.on(LocalDate.parse("2024-12-31")))
        expect("2025-01-01", 12, 2, Rokuyo.Day.SENSHO)
        expect("2027-12-31", 12, 4, Rokuyo.Day.SENBU)
        assertNull(Rokuyo.on(LocalDate.parse("2028-01-01")))
        val start = LocalDate.of(2025, 1, 1)
        for (offset in 0L until 1095L) {
            val lunar = requireNotNull(Rokuyo.on(start.plusDays(offset)))
            assertTrue(lunar.month in 1..12 && lunar.day in 1..30)
        }
    }

    private fun expect(date: String, month: Int, day: Int, rokuyo: Rokuyo.Day, leap: Boolean = false) {
        val actual = requireNotNull(Rokuyo.on(LocalDate.parse(date)))
        assertEquals(date, Rokuyo.LunarDate(month, day, leap), actual)
        assertEquals(date, rokuyo, actual.rokuyo)
    }
}
