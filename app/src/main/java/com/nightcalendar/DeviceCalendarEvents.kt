package com.nightcalendar

import android.Manifest
import android.content.Context
import android.content.pm.PackageManager
import android.provider.CalendarContract
import java.time.LocalDate
import java.time.ZoneId

/** Reads locally synced Android calendars only after the user grants permission. */
object DeviceCalendarEvents {
    data class Event(val title: String, val startMillis: Long)

    fun onDate(context: Context, date: LocalDate): List<Event> {
        if (context.checkSelfPermission(Manifest.permission.READ_CALENDAR) != PackageManager.PERMISSION_GRANTED) {
            return emptyList()
        }
        val zone = ZoneId.systemDefault()
        val from = date.atStartOfDay(zone).toInstant().toEpochMilli()
        val until = date.plusDays(1).atStartOfDay(zone).toInstant().toEpochMilli()
        val projection = arrayOf(CalendarContract.Instances.TITLE, CalendarContract.Instances.BEGIN)
        val uri = CalendarContract.Instances.CONTENT_URI.buildUpon()
            .appendPath(from.toString()).appendPath((until - 1).toString()).build()
        val events = mutableListOf<Event>()
        context.contentResolver.query(
            uri, projection, null, null, CalendarContract.Instances.BEGIN + " ASC"
        )?.use { cursor ->
            val titleColumn = cursor.getColumnIndexOrThrow(CalendarContract.Instances.TITLE)
            val startColumn = cursor.getColumnIndexOrThrow(CalendarContract.Instances.BEGIN)
            while (cursor.moveToNext()) {
                events.add(Event(cursor.getString(titleColumn) ?: "(予定)", cursor.getLong(startColumn)))
            }
        }
        return events
    }
}
