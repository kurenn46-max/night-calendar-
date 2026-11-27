#!/usr/bin/env bash
# Runs as ONE shell invocation: the Android emulator action executes script lines
# separately, so APK and package variables must not span separate script lines.
set -Eeuo pipefail

on_error() {
  echo "::error::Android emulator smoke test failed (exit code $?)"
  adb logcat -d -t 150 2>&1 | tail -150 || true
}
trap on_error ERR

apk="$(find app/build/outputs/apk/debug -name '*.apk' -type f -print -quit)"
if [ -z "$apk" ] || [ ! -f "$apk" ]; then
  echo "::error::Debug APK not found"
  exit 1
fi
aapt="$ANDROID_HOME/build-tools/35.0.0/aapt"
pkg="$("$aapt" dump badging "$apk" | sed -n "s/^package: name='\([^']*\)'.*/\1/p" | head -n 1)"
if [ -z "$pkg" ]; then
  echo "::error::Could not extract APK package name from $apk"
  exit 1
fi
echo "Testing Android package: $pkg"
adb wait-for-device
adb install -r "$apk"
for attempt in 1 2; do
  adb shell monkey -p "$pkg" -c android.intent.category.LAUNCHER 1
  sleep 5
  adb shell pidof "$pkg"
  if [ "$attempt" -eq 1 ]; then
    adb shell am force-stop "$pkg"
  fi
done
echo "NIGHT CORE: Android emulator install/launch smoke test passed"
