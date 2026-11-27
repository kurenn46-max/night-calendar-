package com.nightcalendar

import android.Manifest
import android.content.Context
import android.content.pm.PackageManager
import android.provider.CalendarContract
import com.nightcalendar.core.LocalDiagnosticSummary
import java.time.LocalDate
import java.time.ZoneId

/** Read-only diagnostic for a user's own phone. No account IDs, event titles or network calls. */
object DeviceCalendarDiagnostics {
    fun inspect(context: Context, date: LocalDate): String {
        if (context.checkSelfPermission(Manifest.permission.READ_CALENDAR) != PackageManager.PERMISSION_GRANTED) {
            return LocalDiagnosticSummary.permissionMissing()
        }
        return try {
            var registered = 0
            var visible = 0
            val calendarCursor = context.contentResolver.query(
                CalendarContract.Calendars.CONTENT_URI,
                arrayOf(CalendarContract.Calendars.VISIBLE),
                null, null, null
            ) ?: return LocalDiagnosticSummary.providerUnavailable()
            calendarCursor.use { cursor ->
                while (cursor.moveToNext()) {
                    registered += 1
                    if (!cursor.isNull(0) && cursor.getInt(0) != 0) visible += 1
                }
            }

            val zone = ZoneId.systemDefault()
            val from = date.atStartOfDay(zone).toInstant().toEpochMilli()
            val until = date.plusDays(1).atStartOfDay(zone).toInstant().toEpochMilli()
            val instancesUri = CalendarContract.Instances.CONTENT_URI.buildUpon()
                .appendPath(from.toString()).appendPath((until - 1).toString()).build()
            val occurrences = context.contentResolver.query(
                instancesUri, arrayOf(CalendarContract.Instances.EVENT_ID),
                null, null, null
            )?.use { it.count } ?: return LocalDiagnosticSummary.providerUnavailable()

            LocalDiagnosticSummary.report(date, registered, visible, occurrences)
        } catch (_: RuntimeException) {
            // A provider may be absent or deny access despite runtime permission.
            // Never include exception text: it can contain device/account data.
            LocalDiagnosticSummary.providerUnavailable()
        }
    }
}
