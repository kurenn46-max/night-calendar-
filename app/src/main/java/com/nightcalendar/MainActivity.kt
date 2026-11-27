package com.nightcalendar

import android.Manifest
import android.content.pm.PackageManager
import android.app.Activity
import android.graphics.Color
import android.os.Bundle
import android.view.Gravity
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
    private lateinit var heading: TextView
    private lateinit var calendar: GridLayout
    private lateinit var eventSummary: TextView
    private val japanese = Locale.JAPAN

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        val root = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            setPadding(16, 28, 16, 12)
            setBackgroundColor(Color.WHITE)
        }
        val navigation = LinearLayout(this).apply { gravity = Gravity.CENTER_VERTICAL }
        val previous = Button(this).apply { text = "‹"; setOnClickListener { month = month.minusMonths(1); render() } }
        heading = TextView(this).apply {
            textSize = 23f
            gravity = Gravity.CENTER
            setTextColor(Color.BLACK)
        }
        val next = Button(this).apply { text = "›"; setOnClickListener { month = month.plusMonths(1); render() } }
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
        root.addView(TextView(this).apply {
            text = "六曜・祝日判定は開発中です"
            textSize = 13f
            setTextColor(Color.DKGRAY)
        })
        setContentView(root)
        render()
    }

    private fun render() {
        heading.text = month.format(DateTimeFormatter.ofPattern("yyyy年 M月", japanese))
        calendar.removeAllViews()
        eventSummary.text = if (checkSelfPermission(Manifest.permission.READ_CALENDAR) == PackageManager.PERMISSION_GRANTED) {
            try {
                val events = DeviceCalendarEvents.onDate(this, LocalDate.now())
                if (events.isEmpty()) "今日の予定はありません"
                else "今日の予定: " + events.take(4).joinToString(" / ") { it.title }
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
            addCell(label, slot % 7, inMonth && date == today)
        }
    }

    override fun onRequestPermissionsResult(requestCode: Int, permissions: Array<out String>, grantResults: IntArray) {
        super.onRequestPermissionsResult(requestCode, permissions, grantResults)
        if (requestCode == 100) render()
    }

    private fun addCell(label: String, column: Int, today: Boolean) {
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
        }
        calendar.addView(cell, GridLayout.LayoutParams().apply {
            width = 0
            height = GridLayout.LayoutParams.WRAP_CONTENT
            columnSpec = GridLayout.spec(GridLayout.UNDEFINED, 1f)
        })
    }
}
