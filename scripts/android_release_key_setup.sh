#!/usr/bin/env bash
# Owner-operated from Termux on an Android phone. Do NOT run in GitHub Actions.
# Only uploads encrypted Actions secrets to the owner's release-candidate environment.
# Does not build/sign an APK, trigger a workflow or publish a release.
set -Eeuo pipefail
set +x
umask 077

repo="kurenn46-max/night-calendar-"
environment="release-candidate"
alias_name="night-calendar"
private_dir="$HOME/.local/share/night-calendar-signing"
keystore="$private_dir/night-calendar-release.jks"

for binary in keytool gh openssl base64; do
  if ! command -v "$binary" >/dev/null 2>&1; then
    echo "Missing $binary. In Termux run: pkg install openjdk-17 gh openssl coreutils" >&2
    exit 1
  fi
done

if ! gh auth status --hostname github.com >/dev/null 2>&1; then
  echo "GitHub login required. Run: gh auth login --web" >&2
  exit 1
fi
# Make sure the signed-in account has access before generating the irreplaceable key.
if ! gh repo view "$repo" --json nameWithOwner --jq .nameWithOwner >/dev/null; then
  echo "Cannot access NIGHT CALENDAR repository with this GitHub account." >&2
  exit 1
fi

mkdir -p "$private_dir"
chmod 700 "$private_dir"
printf 'Create/reuse the NIGHT CALENDAR private release signing key.\n'
printf 'Keep its password private. It will not be printed or stored in this script.\n'
IFS= read -r -s -p "Release keystore password (at least 12 characters): " NIGHT_SIGN_PASS
printf '\n'
trap 'unset NIGHT_SIGN_PASS' EXIT

password_bytes="$(printf '%s' "$NIGHT_SIGN_PASS" | wc -c | tr -d ' ')"
if [ "$password_bytes" -lt 12 ]; then
  echo "Password is too short; no key or secret was changed." >&2
  exit 1
fi

IFS= read -r -s -p "Re-enter password: " confirmation
printf '\n'
if [ "$NIGHT_SIGN_PASS" != "$confirmation" ]; then
  unset confirmation
  echo "Passwords differ; no key or secret was changed." >&2
  exit 1
fi
unset confirmation
export NIGHT_SIGN_PASS

if [ -e "$keystore" ]; then
  printf 'Existing release keystore detected. Never overwrite an existing release key.\n'
  IFS= read -r -p "Type REUSE to keep the existing key: " choice
  if [ "$choice" != "REUSE" ]; then
    echo "Stopped without replacing the key." >&2
    exit 1
  fi
  if ! keytool -list -storetype PKCS12 -keystore "$keystore" \
      -alias "$alias_name" -storepass:env NIGHT_SIGN_PASS >/dev/null 2>&1; then
    echo "The existing key or entered password is invalid. No secrets were uploaded." >&2
    exit 1
  fi
else
  keytool -genkeypair -noprompt -storetype PKCS12 \
    -keystore "$keystore" -alias "$alias_name" \
    -keyalg RSA -keysize 3072 -sigalg SHA256withRSA \
    -validity 36500 -dname "CN=NIGHT CALENDAR" \
    -storepass:env NIGHT_SIGN_PASS -keypass:env NIGHT_SIGN_PASS
  chmod 600 "$keystore"
fi

test -s "$keystore"
fingerprint="$(keytool -exportcert -rfc -storetype PKCS12 \
  -keystore "$keystore" -alias "$alias_name" \
  -storepass:env NIGHT_SIGN_PASS | openssl x509 -noout -fingerprint -sha256 | cut -d= -f2)"
fingerprint_compact="$(printf '%s' "$fingerprint" | tr -d ':' | tr '[:upper:]' '[:lower:]')"
if ! [[ "$fingerprint_compact" =~ ^[a-f0-9]{64}$ ]]; then
  echo "Could not calculate the signing certificate fingerprint; no secrets uploaded." >&2
  exit 1
fi

printf 'Registering five GitHub Actions environment secrets without clipboard or chat.\n'
# GitHub CLI encrypts secrets locally before uploading. Never use repository-level secrets.
gh api -X PUT "repos/$repo/environments/$environment" >/dev/null
base64 -w 0 "$keystore" | gh secret set NIGHT_CALENDAR_KEYSTORE_B64 -R "$repo" -e "$environment"
printf '%s' "$NIGHT_SIGN_PASS" | gh secret set NIGHT_CALENDAR_KEYSTORE_PASSWORD -R "$repo" -e "$environment"
printf '%s' "$alias_name" | gh secret set NIGHT_CALENDAR_KEY_ALIAS -R "$repo" -e "$environment"
printf '%s' "$NIGHT_SIGN_PASS" | gh secret set NIGHT_CALENDAR_KEY_PASSWORD -R "$repo" -e "$environment"
printf '%s' "$fingerprint" | gh secret set NIGHT_CALENDAR_EXPECTED_CERT_SHA256 -R "$repo" -e "$environment"

printf '\nSecret names registered in release-candidate (values cannot be read back):\n'
gh secret list -R "$repo" -e "$environment" --json name --jq '.[].name'
printf '\nPrivate key stays in Termux private storage: %s\n' "$keystore"
printf 'Important: before ANY real signed build, create two secure OFF-DEVICE backups\n'
printf 'of this keystore plus its password (e.g., encrypted USB/cloud storage).\n'
printf 'Never post the key, base64 data or password in ChatGPT, GitHub issues or commits.\n'
printf 'Next: configure main-only deployment protection and run Actions manually.\n'
