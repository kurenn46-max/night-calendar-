package com.nightcalendar

import android.Manifest
import android.content.pm.PackageManager
import android.app.Activity
import android.graphics.Color
import android.os.Bundle
import android.text.SpannableString
import android.text.Spanned
import android.text.style.RelativeSizeSpan
import android.view.Gravity
import android.view.View
import android.content.Intent
import android.provider.CalendarContract
import java.time.ZoneId
import android.widget.Button
import android.widget.GridLayout
import android.widget.LinearLayout
import android.widget.ScrollView
import android.widget.TextView
import com.nightcalendar.core.CalendarDayStyle
import com.nightcalendar.core.Rokuyo
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
    private lateinit var deviceDiagnosticStatus: TextView
    private lateinit var holidayStatus: TextView
    private lateinit var eventButtons: LinearLayout
    private val japanese = Locale.JAPAN
    private var dark = false
    private val nightForegroundColor get() = if (dark) Color.rgb(235, 235, 235) else Color.BLACK
    private val nightSecondaryColor get() = if (dark) Color.rgb(190, 190, 190) else Color.DKGRAY
    private val nightBackgroundColor get() = if (dark) Color.rgb(24, 24, 28) else Color.WHITE

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        dark = getPreferences(MODE_PRIVATE).getBoolean("dark", 
            resources.configuration.uiMode and android.content.res.Configuration.UI_MODE_NIGHT_MASK ==
                android.content.res.Configuration.UI_MODE_NIGHT_YES)
        savedInstanceState?.getString("selectedDate")?.let {
            selectedDate = LocalDate.parse(it)
            month = YearMonth.from(selectedDate)
        }
        setTheme(if (dark) android.R.style.Theme_Material_NoActionBar else android.R.style.Theme_Material_Light_NoActionBar)
        val root = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            setPadding(16, 28, 16, 12)
            setBackgroundColor(nightBackgroundColor)
        }
        val navigation = LinearLayout(this).apply { gravity = Gravity.CENTER_VERTICAL }
        val previous = Button(this).apply {
            text = "‹"
            contentDescription = "前の月"
            setOnClickListener { moveMonth(-1) }
        }
        heading = TextView(this).apply {
            textSize = 23f
            gravity = Gravity.CENTER
            setTextColor(nightForegroundColor)
        }
        val next = Button(this).apply {
            text = "›"
            contentDescription = "次の月"
            setOnClickListener { moveMonth(1) }
        }
        navigation.addView(previous)
        navigation.addView(heading, LinearLayout.LayoutParams(0, -2, 1f))
        navigation.addView(next)
        root.addView(navigation)
        root.addView(Button(this).apply {
            text = if (dark) "ライト表示に切替" else "ダーク表示に切替"
            setOnClickListener {
                getPreferences(MODE_PRIVATE).edit().putBoolean("dark", !dark).apply()
                recreate()
            }
        })
        calendar = GridLayout(this).apply { columnCount = 7 }
        root.addView(calendar)
        holidayStatus = TextView(this).apply {
            textSize = 13f
            setTextColor(nightSecondaryColor)
        }
        root.addView(holidayStatus)
        root.addView(Button(this).apply {
            text = "端末のカレンダーを読み込む"
            setOnClickListener {
                if (checkSelfPermission(Manifest.permission.READ_CALENDAR) != PackageManager.PERMISSION_GRANTED)
                    requestPermissions(arrayOf(Manifest.permission.READ_CALENDAR), 100)
                else render()
            }
        })
        root.addView(Button(this).apply {
            text = "端末診断（送信なし）"
            contentDescription = "端末内だけでカレンダーの読み込み状態を診断"
            setOnClickListener {
                deviceDiagnosticStatus.text = DeviceCalendarDiagnostics.inspect(this@MainActivity, selectedDate)
                deviceDiagnosticStatus.visibility = View.VISIBLE
            }
        })
        deviceDiagnosticStatus = TextView(this).apply {
            textSize = 14f
            setTextColor(nightSecondaryColor)
            setPadding(8, 8, 8, 8)
            visibility = View.GONE
        }
        root.addView(deviceDiagnosticStatus)
        eventSummary = TextView(this).apply {
            textSize = 14f
            setTextColor(nightSecondaryColor)
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
        setContentView(ScrollView(this).apply {
            isFillViewport = true
            addView(root)
        })
        render()
    }

    override fun onSaveInstanceState(outState: Bundle) {
        outState.putString("selectedDate", selectedDate.toString())
        super.onSaveInstanceState(outState)
    }

    private fun moveMonth(delta: Long) {
        month = month.plusMonths(delta)
        selectedDate = month.atDay(selectedDate.dayOfMonth.coerceAtMost(month.lengthOfMonth()))
        render()
    }

    private fun render() {
        if (::deviceDiagnosticStatus.isInitialized && deviceDiagnosticStatus.visibility == View.VISIBLE) {
            deviceDiagnosticStatus.text = DeviceCalendarDiagnostics.inspect(this, selectedDate)
        }
        heading.text = month.format(DateTimeFormatter.ofPattern("yyyy年 M月", japanese))
        holidayStatus.text = listOfNotNull(
            "祝日データ対象外（2026〜2027年）".takeUnless { JapanHolidays.isSupported(month.year) },
            "六曜データ対象外（2025〜2027年）".takeUnless { month.year in Rokuyo.supportedYears },
        ).joinToString("\n")
        holidayStatus.visibility = if (holidayStatus.text.isEmpty()) View.GONE else View.VISIBLE
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
        val today = LocalDate.now()
        for ((index, name) in headers.withIndex()) {
            addCell(name, index, today)
        }
        val firstOffset = month.atDay(1).dayOfWeek.value % 7
        for (slot in 0 until 42) {
            val date = month.atDay(1).plusDays((slot - firstOffset).toLong())
            val inMonth = YearMonth.from(date) == month
            val label = if (inMonth) date.dayOfMonth.toString() else ""
            addCell(label, slot % 7, today, date.takeIf { inMonth })
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

    private fun addCell(label: String, column: Int, today: LocalDate, date: LocalDate? = null) {
        val holiday = date?.let(JapanHolidays::isHoliday) ?: false
        val rokuyo = date?.let(Rokuyo::on)?.rokuyo?.label
        val day = date?.let { CalendarDayStyle.dayUi(it, today, holiday) }
        val tone = day?.tone
        val isToday = day?.isToday == true
        val inset = (4 * resources.displayMetrics.density).toInt()
        val cell = TextView(this).apply {
            text = if (rokuyo == null) label else SpannableString("$label\n$rokuyo").apply {
                setSpan(RelativeSizeSpan(0.72f), label.length + 1, length, Spanned.SPAN_EXCLUSIVE_EXCLUSIVE)
            }
            if (date != null) {
                contentDescription = listOfNotNull(date.toString(), rokuyo, "祝日・休日".takeIf { holiday }).joinToString(" ")
            }
            textSize = if (isToday) 22f else 18f
            gravity = Gravity.CENTER
            setPadding(0, inset, 0, inset)
            minHeight = if (date != null || label.isEmpty()) (48 * resources.displayMetrics.density).toInt() else 0
            setTextColor(when {
                tone == CalendarDayStyle.DayTone.HOLIDAY_RED || (date == null && column == 0) -> if (dark) Color.rgb(255, 145, 145) else Color.rgb(195, 45, 45)
                tone == CalendarDayStyle.DayTone.SATURDAY_BLUE || (date == null && column == 6) -> if (dark) Color.rgb(145, 185, 255) else Color.rgb(35, 95, 190)
                else -> nightForegroundColor
            })
            if (isToday) setBackgroundColor(if (dark) Color.rgb(90, 65, 20) else Color.rgb(255, 235, 180))
            else if (date != null && date == selectedDate) setBackgroundColor(if (dark) Color.rgb(35, 55, 90) else Color.rgb(220, 235, 255))
            if (date != null) setOnClickListener { selectedDate = date; render() }
        }
        calendar.addView(cell, GridLayout.LayoutParams().apply {
            width = 0
            height = GridLayout.LayoutParams.WRAP_CONTENT
            columnSpec = GridLayout.spec(GridLayout.UNDEFINED, 1f)
        })
    }
}
