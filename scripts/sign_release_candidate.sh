#!/usr/bin/env bash
# Trusted release-candidate signing shared by manual release and no-secret CI rehearsal.
# Never log passwords, private key bytes, or the base64 keystore.
set -Eeuo pipefail

for name in KEYSTORE_B64 KEYSTORE_PASSWORD KEY_ALIAS KEY_PASSWORD EXPECTED_CERT_SHA256 ANDROID_HOME RUNNER_TEMP; do
  if [ -z "${!name:-}" ]; then
    echo "::error::Missing signing input: $name" >&2
    exit 1
  fi
done

expected="$(printf '%s' "$EXPECTED_CERT_SHA256" | tr -d ':' | tr '[:upper:]' '[:lower:]')"
if ! [[ "$expected" =~ ^[a-f0-9]{64}$ ]]; then
  echo "::error::Invalid expected certificate SHA-256 digest" >&2
  exit 1
fi

unsigned="app/build/outputs/apk/release/app-release-unsigned.apk"
if [ ! -s "$unsigned" ]; then
  echo "::error::Unsigned Android release APK is missing" >&2
  exit 1
fi

tools_dir="$ANDROID_HOME/build-tools/35.0.0"
for tool in zipalign apksigner aapt; do
  test -x "$tools_dir/$tool" || { echo "::error::Missing Android build tool: $tool" >&2; exit 1; }
done
private_dir="$(mktemp -d "$RUNNER_TEMP/nightcalendar-sign.XXXXXXXX")"
chmod 700 "$private_dir"
out_dir="signed-candidate"
output="$out_dir/NIGHT_CALENDAR_candidate.apk"
success=0
cleanup() {
  rm -f "$private_dir/release.keystore" "$private_dir/aligned.apk"
  rmdir "$private_dir" 2>/dev/null || true
  if [ "$success" -ne 1 ]; then
    rm -f "$output" "$out_dir/SHA256SUMS.txt"
  fi
}
trap cleanup EXIT
mkdir -p "$out_dir"

keystore="$private_dir/release.keystore"
umask 077
if ! printf '%s' "$KEYSTORE_B64" | base64 --decode > "$keystore"; then
  echo "::error::Signing keystore is not valid base64" >&2
  exit 1
fi
chmod 600 "$keystore"

"$tools_dir/zipalign" -f -p 4 "$unsigned" "$private_dir/aligned.apk"
"$tools_dir/apksigner" sign \
  --ks "$keystore" \
  --ks-key-alias "$KEY_ALIAS" \
  --ks-pass env:KEYSTORE_PASSWORD \
  --key-pass env:KEY_PASSWORD \
  --out "$output" "$private_dir/aligned.apk"

"$tools_dir/apksigner" verify --verbose --min-sdk-version 26 "$output"
"$tools_dir/zipalign" -c -v 4 "$output"
actual="$("$tools_dir/apksigner" verify --print-certs "$output" \
  | sed -n 's/^Signer #1 certificate SHA-256 digest: //p' \
  | head -n 1 | tr -d ':' | tr '[:upper:]' '[:lower:]')"
if [ "${#actual}" -ne 64 ] || [ "$actual" != "$expected" ]; then
  echo "::error::Signing certificate fingerprint mismatch" >&2
  exit 1
fi

package="$("$tools_dir/aapt" dump badging "$output" \
  | sed -n "s/^package: name='\([^']*\)'.*/\1/p" | head -n 1)"
if [ "$package" != "com.nightcalendar" ]; then
  echo "::error::Unexpected Android application ID" >&2
  exit 1
fi

(cd "$out_dir" && sha256sum NIGHT_CALENDAR_candidate.apk > SHA256SUMS.txt)
success=1
echo "Signed APK verified; it is a candidate and must not be published before device acceptance."
