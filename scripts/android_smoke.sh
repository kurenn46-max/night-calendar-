#!/usr/bin/env bash
# The emulator action must invoke the whole test as one shell process.
set -Eeuo pipefail

adb_cmd=(adb -e)
app=app/build/outputs/apk/debug/app-debug.apk
test_apk=app/build/outputs/apk/androidTest/debug/app-debug-androidTest.apk
report=night-calendar-emulator.log
stage=adb
trap 'echo "NIGHT CALENDAR QA: $stage failed (exit $?)" >&2' ERR

# -e excludes physical devices. Use only the fresh CI emulator for fixtures.
timeout 60s "${adb_cmd[@]}" wait-for-device
[[ $(timeout 10s "${adb_cmd[@]}" shell getprop ro.kernel.qemu | tr -d '\r') == 1 ]]
stage=install
timeout 60s "${adb_cmd[@]}" install -r "$app"
timeout 60s "${adb_cmd[@]}" install -r -t "$test_apk"

stage=ui-smoke
timeout 210s "${adb_cmd[@]}" shell am instrument -w -r \
  -e syntheticCalendar true com.nightcalendar.test/com.nightcalendar.CalendarSmoke \
  | tee "$report"
grep -Fx 'INSTRUMENTATION_RESULT: calendar_smoke=passed 4/4' "$report"
grep -Fx 'INSTRUMENTATION_CODE: -1' "$report"
for scenario in launch device-diagnostic-denied navigation-and-rokuyo synthetic-event-display; do
  grep -Fx "INSTRUMENTATION_STATUS: passed=$scenario" "$report"
done
