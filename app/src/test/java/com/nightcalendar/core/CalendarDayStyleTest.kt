package com.nightcalendar.core

import org.junit.Assert.*
import org.junit.Test
import java.time.LocalDate

class CalendarDayStyleTest {
    @Test fun sundayIsRed() {
        val d = LocalDate.of(2026, 11, 29)
        assertEquals(CalendarDayStyle.DayTone.HOLIDAY_RED, CalendarDayStyle.dayUi(d, d, false).tone)
    }
    @Test fun saturdayIsBlue() {
        val d = LocalDate.of(2026, 11, 28)
        assertEquals(CalendarDayStyle.DayTone.SATURDAY_BLUE, CalendarDayStyle.dayUi(d, d, false).tone)
    }
    @Test fun holidayOverridesWeekday() {
        val d = LocalDate.of(2026, 11, 23)
        assertEquals(CalendarDayStyle.DayTone.HOLIDAY_RED, CalendarDayStyle.dayUi(d, d, true).tone)
    }
}
