package com.nightcalendar

import android.Manifest
import android.content.pm.PackageManager
import android.app.Activity
import android.graphics.Color
import android.os.Bundle
import android.view.Gravity
import android.content.Intent
import android.provider.CalendarContract
import java.time.ZoneId
import android.view.View
import android.widget.Button
import android.widget.GridLayout
import android.widget.LinearLayout
import android.widget.TextView
import java.time.DayOfWeek
import java.time.LocalDate
import java.time.YearMonth
import java.time.format.DateTimeFormatter
import java.util.Locale

class MainActivity : Activity() {
    private var month: YearMonth = YearMonth.now()
    private var selectedDate: LocalDate = LocalDate.now()
    private lateinit var heading: TextView
    private lateinit var calendar: GridLayout
    private lateinit var eventSummary: TextView
    private lateinit var eventButtons: LinearLayout
    private val japanese = Locale.JAPAN

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        val root = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            setPadding(16, 28, 16, 12)
            setBackgroundColor(Color.WHITE)
        }
        val navigation = LinearLayout(this).apply { gravity = Gravity.CENTER_VERTICAL }
        val previous = Button(this).apply { text = "‹"; setOnClickListener { moveMonth(-1) } }
        heading = TextView(this).apply {
            textSize = 23f
            gravity = Gravity.CENTER
            setTextColor(Color.BLACK)
        }
        val next = Button(this).apply { text = "›"; setOnClickListener { moveMonth(1) } }
        navigation.addView(previous)
        navigation.addView(heading, LinearLayout.LayoutParams(0, -2, 1f))
        navigation.addView(next)
        root.addView(navigation)
        calendar = GridLayout(this).apply { columnCount = 7 }
        root.addView(calendar)
        root.addView(Button(this).apply {
            text = "端末のカレンダーを読み込む"
            setOnClickListener {
                if (checkSelfPermission(Manifest.permission.READ_CALENDAR) != PackageManager.PERMISSION_GRANTED)
                    requestPermissions(arrayOf(Manifest.permission.READ_CALENDAR), 100)
                else render()
            }
        })
        eventSummary = TextView(this).apply {
            textSize = 14f
            setTextColor(Color.DKGRAY)
            setPadding(8, 16, 8, 8)
        }
        root.addView(eventSummary)
        eventButtons = LinearLayout(this).apply { orientation = LinearLayout.VERTICAL }
        root.addView(eventButtons)
        root.addView(Button(this).apply {
            text = "選択日の予定を追加"
            setOnClickListener {
                val start = selectedDate.atTime(9, 0).atZone(ZoneId.systemDefault()).toInstant().toEpochMilli()
                val intent = Intent(Intent.ACTION_INSERT, CalendarContract.Events.CONTENT_URI)
                    .putExtra(CalendarContract.EXTRA_EVENT_BEGIN_TIME, start)
                    .putExtra(CalendarContract.EXTRA_EVENT_END_TIME, start + 3600000L)
                try { startActivity(intent) } catch (e: android.content.ActivityNotFoundException) {
                    android.widget.Toast.makeText(this@MainActivity, "カレンダーアプリが見つかりません", android.widget.Toast.LENGTH_SHORT).show()
                }
            }
        })
        root.addView(TextView(this).apply {
            text = "六曜・祝日判定は開発中です"
            textSize = 13f
            setTextColor(Color.DKGRAY)
        })
        setContentView(root)
        render()
    }

    private fun moveMonth(delta: Long) {
        month = month.plusMonths(delta)
        selectedDate = month.atDay(selectedDate.dayOfMonth.coerceAtMost(month.lengthOfMonth()))
        render()
    }

    private fun render() {
        heading.text = month.format(DateTimeFormatter.ofPattern("yyyy年 M月", japanese))
        calendar.removeAllViews()
        eventButtons.removeAllViews()
        eventSummary.text = if (checkSelfPermission(Manifest.permission.READ_CALENDAR) == PackageManager.PERMISSION_GRANTED) {
            try {
                val events = DeviceCalendarEvents.onDate(this, selectedDate)
                if (events.isEmpty()) "$selectedDate の予定はありません"
                else {
                    events.take(8).forEach { event ->
                        eventButtons.addView(Button(this).apply {
                            text = event.title + "  ›"
                            contentDescription = event.title + " の予定を開く"
                            setOnClickListener {
                                val intent = Intent(Intent.ACTION_VIEW,
                                    android.content.ContentUris.withAppendedId(CalendarContract.Events.CONTENT_URI, event.id))
                                try {
                                    startActivity(intent)
                                } catch (e: android.content.ActivityNotFoundException) {
                                    android.widget.Toast.makeText(this@MainActivity,
                                        "予定を開けるアプリがありません", android.widget.Toast.LENGTH_SHORT).show()
                                }
                            }
                        })
                    }
                    "$selectedDate の予定（" + events.size + "件）"
                }
            } catch (e: RuntimeException) {
                "予定を読み込めませんでした"
            }
        } else "カレンダーのアクセス許可が必要です"
        val headers = listOf("日", "月", "火", "水", "木", "金", "土")
        for ((index, name) in headers.withIndex()) {
            addCell(name, index, false)
        }
        val firstOffset = month.atDay(1).dayOfWeek.value % 7
        val today = LocalDate.now()
        for (slot in 0 until 42) {
            val date = month.atDay(1).plusDays((slot - firstOffset).toLong())
            val inMonth = YearMonth.from(date) == month
            val label = if (inMonth) date.dayOfMonth.toString() else ""
            addCell(label, slot % 7, inMonth && date == today, if (inMonth) date else null)
        }
    }

    override fun onResume() {
        super.onResume()
        if (::eventSummary.isInitialized) render()
    }

    override fun onRequestPermissionsResult(requestCode: Int, permissions: Array<out String>, grantResults: IntArray) {
        super.onRequestPermissionsResult(requestCode, permissions, grantResults)
        if (requestCode == 100) render()
    }

    private fun addCell(label: String, column: Int, today: Boolean, date: LocalDate? = null) {
        val cell = TextView(this).apply {
            text = label
            textSize = if (today) 22f else 18f
            gravity = Gravity.CENTER
            setPadding(3, 17, 3, 17)
            setTextColor(when (column) {
                0 -> Color.rgb(195, 45, 45)
                6 -> Color.rgb(35, 95, 190)
                else -> Color.BLACK
            })
            if (today) setBackgroundColor(Color.rgb(255, 235, 180))
            else if (date != null && date == selectedDate) setBackgroundColor(Color.rgb(220, 235, 255))
            if (date != null) setOnClickListener { selectedDate = date; render() }
        }
        calendar.addView(cell, GridLayout.LayoutParams().apply {
            width = 0
            height = GridLayout.LayoutParams.WRAP_CONTENT
            columnSpec = GridLayout.spec(GridLayout.UNDEFINED, 1f)
        })
    }
}
