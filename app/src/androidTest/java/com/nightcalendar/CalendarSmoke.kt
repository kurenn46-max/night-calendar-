package com.nightcalendar

import android.Manifest
import android.app.Activity
import android.app.Instrumentation
import android.content.ContentUris
import android.content.ContentValues
import android.content.Intent
import android.net.Uri
import android.os.Bundle
import android.os.SystemClock
import android.provider.CalendarContract
import android.provider.CalendarContract.Calendars
import android.provider.CalendarContract.Events
import android.view.accessibility.AccessibilityNodeInfo
import java.time.LocalDate
import java.time.YearMonth
import java.time.ZoneId
import java.time.temporal.ChronoUnit

/** Runs only on a fresh CI emulator. Only a synthetic local calendar is written. */
class CalendarSmoke : Instrumentation() {
    private val eventDate = LocalDate.of(2026, 2, 17)
    private val fixtureName = "NIGHT CALENDAR QA"
    private val eventTitle = "NIGHT CALENDAR QA fixture"
    private var stage = "launch"

    override fun onCreate(arguments: Bundle?) {
        super.onCreate(arguments)
        require(arguments?.getString("syntheticCalendar") == "true")
        start()
    }

    override fun onStart() {
        val results = Bundle()
        try {
            startActivitySync(Intent(targetContext, MainActivity::class.java).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK))
            awaitNode("カレンダーのアクセス許可が必要です")
            passed()

            stage = "device-diagnostic-denied"
            click("端末診断（送信なし）")
            awaitNode("端末診断：カレンダーの読み込み権限がありません。上のボタンから許可してください。")
            passed()

            stage = "navigation-and-rokuyo"
            val targetMonth = YearMonth.from(eventDate)
            val steps = ChronoUnit.MONTHS.between(YearMonth.now(), targetMonth).toInt()
            check(steps in -36..36) { "Fixture month is outside the QA navigation window" }
            repeat(kotlin.math.abs(steps)) { click(if (steps < 0) "前の月" else "次の月") }
            awaitNode("2026年 2月")
            awaitNode("2026-02-11 大安 祝日・休日")
            click("2026-02-17 先勝")
            passed()

            stage = "synthetic-event-display"
            val calendar = insertCalendar()
            try {
                insertEvent(ContentUris.parseId(calendar))
                uiAutomation.grantRuntimePermission(targetContext.packageName, Manifest.permission.READ_CALENDAR)
                click("端末のカレンダーを読み込む")
                awaitNode("2026-02-17 の予定（1件）")
                awaitNode("$eventTitle の予定を開く")
                click("2026-02-18 友引")
                awaitNode("2026-02-18 の予定はありません")
                click("端末診断（送信なし）")
                awaitNodeContaining("端末診断：権限あり")
                awaitNodeContaining("登録カレンダー：")
                awaitNodeContaining("の予定：")
            } finally {
                asCalendarWriter { targetContext.contentResolver.delete(asLocalSyncAdapter(calendar), null, null) }
            }
            passed()
            results.putString("calendar_smoke", "passed 4/4")
            finish(Activity.RESULT_OK, results)
        } catch (failure: Exception) {
            results.putString("calendar_smoke", "failed $stage (${failure.javaClass.simpleName})")
            if (failure is IllegalStateException) results.putString("assertion", failure.message)
            results.putString("location", failure.stackTrace.firstOrNull()?.toString())
            finish(Activity.RESULT_CANCELED, results)
        }
    }

    private fun passed() = sendStatus(0, Bundle().apply { putString("passed", stage) })

    private fun awaitNode(label: String): AccessibilityNodeInfo {
        val deadline = SystemClock.uptimeMillis() + 10_000
        while (SystemClock.uptimeMillis() < deadline) {
            val node = uiAutomation.rootInActiveWindow?.findAccessibilityNodeInfosByText(label)
                ?.firstOrNull { it.isVisibleToUser && (it.text?.toString() == label || it.contentDescription?.toString() == label) }
            if (node != null) return node
            SystemClock.sleep(150)
        }
        error("Expected visible UI element: $label")
    }

    private fun awaitNodeContaining(fragment: String): AccessibilityNodeInfo {
        val deadline = SystemClock.uptimeMillis() + 10_000
        while (SystemClock.uptimeMillis() < deadline) {
            val node = uiAutomation.rootInActiveWindow?.findAccessibilityNodeInfosByText(fragment)
                ?.firstOrNull {
                    it.isVisibleToUser &&
                        (it.text?.toString()?.contains(fragment) == true ||
                         it.contentDescription?.toString()?.contains(fragment) == true)
                }
            if (node != null) return node
            SystemClock.sleep(150)
        }
        error("Expected visible UI text fragment: $fragment")
    }

    private fun click(label: String) {
        check(awaitNode(label).performAction(AccessibilityNodeInfo.ACTION_CLICK)) { "Could not click: $label" }
        waitForIdleSync()
    }

    private fun insertCalendar(): Uri = asCalendarWriter {
        val values = ContentValues().apply {
            put(Calendars.ACCOUNT_NAME, fixtureName)
            put(Calendars.ACCOUNT_TYPE, CalendarContract.ACCOUNT_TYPE_LOCAL)
            put(Calendars.NAME, fixtureName)
            put(Calendars.CALENDAR_DISPLAY_NAME, fixtureName)
            put(Calendars.OWNER_ACCOUNT, fixtureName)
            put(Calendars.CALENDAR_ACCESS_LEVEL, Calendars.CAL_ACCESS_OWNER)
            put(Calendars.CALENDAR_TIME_ZONE, ZoneId.systemDefault().id)
            put(Calendars.CALENDAR_COLOR, 0xff336699.toInt())
            put(Calendars.VISIBLE, 1)
            put(Calendars.SYNC_EVENTS, 1)
        }
        checkNotNull(targetContext.contentResolver.insert(asLocalSyncAdapter(Calendars.CONTENT_URI), values)) {
            "Fixture calendar was not created"
        }
    }

    private fun asLocalSyncAdapter(uri: Uri): Uri = uri.buildUpon()
        .appendQueryParameter(CalendarContract.CALLER_IS_SYNCADAPTER, "true")
        .appendQueryParameter(Calendars.ACCOUNT_NAME, fixtureName)
        .appendQueryParameter(Calendars.ACCOUNT_TYPE, CalendarContract.ACCOUNT_TYPE_LOCAL)
        .build()

    private fun insertEvent(calendarId: Long) = asCalendarWriter {
        val zone = ZoneId.systemDefault()
        val values = ContentValues().apply {
            put(Events.CALENDAR_ID, calendarId)
            put(Events.TITLE, eventTitle)
            put(Events.DTSTART, eventDate.atTime(10, 0).atZone(zone).toInstant().toEpochMilli())
            put(Events.DTEND, eventDate.atTime(11, 0).atZone(zone).toInstant().toEpochMilli())
            put(Events.EVENT_TIMEZONE, zone.id)
        }
        checkNotNull(targetContext.contentResolver.insert(Events.CONTENT_URI, values)) { "Fixture event was not created" }
    }

    private fun <T> asCalendarWriter(action: () -> T): T {
        uiAutomation.adoptShellPermissionIdentity(Manifest.permission.READ_CALENDAR, Manifest.permission.WRITE_CALENDAR)
        try {
            return action()
        } finally {
            uiAutomation.dropShellPermissionIdentity()
        }
    }
}
