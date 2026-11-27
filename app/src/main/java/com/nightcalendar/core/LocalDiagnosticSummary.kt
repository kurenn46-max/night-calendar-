package com.nightcalendar.core

import java.time.LocalDate

/** Pure UI strings; only counts, no account identifiers or event content. */
object LocalDiagnosticSummary {
    fun permissionMissing(): String =
        "端末診断：カレンダーの読み込み権限がありません。上のボタンから許可してください。"

    fun providerUnavailable(): String =
        "端末診断：カレンダー情報を取得できません。端末のカレンダー設定を確認してください。"

    fun report(date: LocalDate, registered: Int, visible: Int, occurrences: Int): String =
        "端末診断：権限あり\n" +
        "登録カレンダー：$registered 件（表示中 $visible 件）\n" +
        "${date}の予定：$occurrences 件\n" +
        "結果は端末内だけに表示し、送信・保存しません。"
}
