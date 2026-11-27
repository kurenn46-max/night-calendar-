# NIGHT CALENDAR — release candidate checklist

This repository currently builds QA APKs. **A green CI run is not permission to publish a signed release.**

## Signing-key owner setup (one time)

Generate an app-specific, long-lived signing key **on a trusted local device**, not in a
public GitHub issue, an AI chat, or an Actions build log. Protect the keystore and its passwords.
Never place them in the repository. Save at least two secure backups: if the private key is
lost, future updates for the same package may become impossible.

Example on a trusted machine with the Java JDK installed (not to be executed by CI):

```bash
keytool -genkeypair -keystore nightcalendar-release.jks -alias nightcalendar \
  -keyalg RSA -keysize 3072 -validity 36500
keytool -list -v -keystore nightcalendar-release.jks -alias nightcalendar
```

Record the signer certificate **SHA-256 fingerprint**, not the keystore file's SHA-256 hash.
Create these **GitHub Actions secrets**, preferably in the `release-candidate`
environment with reviewer restrictions:

| Secret | Meaning |
|---|---|
| `NIGHT_CALENDAR_KEYSTORE_B64` | Base64-encoded private keystore file (one line) |
| `NIGHT_CALENDAR_KEYSTORE_PASSWORD` | Keystore password |
| `NIGHT_CALENDAR_KEY_ALIAS` | Key alias |
| `NIGHT_CALENDAR_KEY_PASSWORD` | Key password |
| `NIGHT_CALENDAR_EXPECTED_CERT_SHA256` | Pinned signer certificate fingerprint |

For example, on a trusted machine: `base64 < nightcalendar-release.jks | tr -d '\n'`.
**Treat this result as a secret.** Do not paste it in a conversation or commit.

## No-secret signing rehearsal (automated in PRs)

The release-gate pull request has an isolated, read-only CI job that builds
`:app:assembleRelease` and uses a **new disposable test-only key** to exercise
`scripts/sign_release_candidate.sh`, checks signature/package/portable SHA256SUMS,
and verifies a deliberately mismatched certificate is rejected. The job deletes
the disposable key and candidate afterward. **This cannot replace the owner's
long-lived release signing key** and does not upload a public APK.

Do not attempt a real signed candidate until the rehearsal job is green.

## Produce a signed candidate

1. Confirm `main` has green Android build, unit tests, lint and emulator UI tests.
2. Open **Actions → NIGHT CALENDAR Signed Candidate → Run workflow**, on `main`.
3. GitHub Actions refuses to sign if any secret is missing. It builds the release
   variant, zipaligns it, signs with the owner-managed key, verifies Android signature,
   checks the signer fingerprint against the pinned certificate, checks package ID
   `com.nightcalendar`, and uploads **a candidate artifact only**.
4. Inspect `SHA256SUMS.txt` and keep the hash with the candidate. Nothing automatically
   creates a GitHub Release or publishes the APK.

## Real-device acceptance (required before release)

- Install on an Android physical device, launch, then reopen after force-stop.
- Verify that month navigation, 六曜, holiday colors, date selection, dark/light setting
  and accessibility labels behave properly.
- Grant calendar permission *only if desired*, and verify events from an already-synced
  device calendar. Confirm calendar/event selection and adding/editing work using
  Android's own calendar app, without sending personal event content to the developer.
- Test permission denied and permission granted; test no events, at least one event,
  and multiple calendars. Test outside the supported date ranges to confirm the
  app displays the coverage warning rather than fabricated holiday/六曜 values.
- Verify an update from a previously signed **production** build using the same
  certificate and an increased versionCode.

**Important:** Debug QA APKs are signed with a different key from the production
candidate. Installing a production-signed APK over a debug-signed APK of the same
package ID will normally fail with `INSTALL_FAILED_UPDATE_INCOMPATIBLE`.
Uninstall the debug APK first, after preserving any local app settings you care about.
Synced calendar events are stored by the Android calendar provider, not by this app.

## Publication gate

Only after signed-device acceptance, correct versionCode/versionName, official
reference-date review, and explicit owner approval should a separate protected
workflow or manual process publish the candidate through **GitHub Releases**.
Keep NIGHT CORE's privileged self-repair workflow draft until separately reviewed.
