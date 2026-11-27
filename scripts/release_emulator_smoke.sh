#!/usr/bin/env bash
# Smoke-test a release-variant APK signed with a disposable CI-only certificate.
# The runner's key must never be reused for production releases.
set -Eeuo pipefail
apk="signed-candidate/NIGHT_CALENDAR_candidate.apk"
report="night-calendar-release-emulator.log"
package="com.nightcalendar"
stage="emulator"
trap 'code=$?; echo "RELEASE APK QA: $stage failed (exit $code)" >&2; adb -e logcat -d -t 120 2>&1 | tail -120 >&2 || true' ERR

test -s "$apk"
adb -e wait-for-device
test "$(adb -e shell getprop ro.kernel.qemu | tr -d '\r')" = "1"
stage="install"
timeout 60s adb -e install -r "$apk"
stage="launch"
timeout 30s adb -e shell am start -W -n "$package/.MainActivity" | tee "$report"
sleep 3
test -n "$(adb -e shell pidof "$package" | tr -d '\r')"
stage="ui"
# Verify the release build exposes the exact diagnostics UI already tested in debug QA.
timeout 40s adb -e shell uiautomator dump /sdcard/nightcalendar-window.xml >> "$report" 2>&1
adb -e shell cat /sdcard/nightcalendar-window.xml | grep -F '端末内だけでカレンダーの読み込み状態を診断' >/dev/null
stage="relaunch"
adb -e shell am force-stop "$package"
timeout 30s adb -e shell am start -W -n "$package/.MainActivity" >> "$report"
sleep 2
test -n "$(adb -e shell pidof "$package" | tr -d '\r')"
echo "NIGHT CALENDAR release APK emulator smoke: passed install, launch, diagnostic UI and relaunch"
