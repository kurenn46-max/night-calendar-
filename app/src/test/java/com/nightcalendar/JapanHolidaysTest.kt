package com.nightcalendar
import java.time.LocalDate
import org.junit.Assert.*
import org.junit.Test

class JapanHolidaysTest {
    @Test fun substituteAndCitizensHolidays() {
        for (day in listOf("2026-05-06", "2026-09-22", "2027-03-22")) {
            assertTrue(day, JapanHolidays.isHoliday(LocalDate.parse(day)))
        }
    }
    @Test fun ordinaryDaysAndCoverage() {
        for (day in listOf("2026-05-07", "2027-09-21", "2027-09-22")) {
            assertFalse(day, JapanHolidays.isHoliday(LocalDate.parse(day)))
        }
        assertTrue(JapanHolidays.isSupported(2026))
        assertTrue(JapanHolidays.isSupported(2027))
        assertFalse(JapanHolidays.isSupported(2028))
    }
    @Test fun annualCounts() {
        for ((year, count) in listOf(2026 to 18, 2027 to 17)) {
            val start = LocalDate.of(year, 1, 1)
            assertEquals(count, (0 until start.lengthOfYear()).count { JapanHolidays.isHoliday(start.plusDays(it.toLong())) })
        }
    }
}
