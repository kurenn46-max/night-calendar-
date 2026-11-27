package com.nightcalendar.core

import java.time.DayOfWeek
import java.time.LocalDate

/**
 * Pure date presentation rules. No calendar events or account information leave the device.
 * Holiday dates must come from a separately verified Japanese holiday provider.
 */
object CalendarDayStyle {
    enum class DayTone { HOLIDAY_RED, SATURDAY_BLUE, NORMAL }
    data class DayUi(
        val date: LocalDate,
        val isToday: Boolean,
        val tone: DayTone
    )

    fun dayUi(date: LocalDate, today: LocalDate, japaneseHoliday: Boolean): DayUi {
        val tone = when {
            japaneseHoliday || date.dayOfWeek == DayOfWeek.SUNDAY -> DayTone.HOLIDAY_RED
            date.dayOfWeek == DayOfWeek.SATURDAY -> DayTone.SATURDAY_BLUE
            else -> DayTone.NORMAL
        }
        return DayUi(date, date == today, tone)
    }
}
