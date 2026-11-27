package com.nightcalendar.core

import java.time.LocalDate
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

class LocalDiagnosticSummaryTest {
    @Test fun deniedPermissionIsExplicit() {
        val text = LocalDiagnosticSummary.permissionMissing()
        assertTrue(text.startsWith("端末診断："))
        assertTrue(text.contains("権限がありません"))
    }

    @Test fun unavailableProviderDoesNotClaimZeroCalendars() {
        val text = LocalDiagnosticSummary.providerUnavailable()
        assertTrue(text.contains("取得できません"))
        assertFalse(text.contains("0 件"))
    }

    @Test fun reportContainsOnlyCountsAndDate() {
        val text = LocalDiagnosticSummary.report(LocalDate.parse("2026-11-27"), 3, 2, 1)
        assertTrue(text.contains("登録カレンダー：3 件"))
        assertTrue(text.contains("表示中 2 件"))
        assertTrue(text.contains("2026-11-27の予定：1 件"))
        assertTrue(text.contains("送信・保存しません"))
        assertFalse(text.contains("gmail"))
        assertFalse(text.contains("予定タイトル"))
    }

    @Test fun emptyCalendarStateIsNotAProviderError() {
        val text = LocalDiagnosticSummary.report(LocalDate.parse("2026-11-27"), 0, 0, 0)
        assertTrue(text.contains("登録カレンダー：0 件"))
        assertTrue(text.contains("の予定：0 件"))
        assertFalse(text.contains("取得できません"))
    }
}
