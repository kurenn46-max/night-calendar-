# NIGHT CORE — NIGHT CALENDAR development contract

## Goal
Deliver a usable Android APK for NIGHT CALENDAR. Prioritize a small, working app over elaborate architecture.

## Product requirements
- Clear month grid with highly visible accurate Japanese rokuyō.
- Highlight today's date; Sundays and Japanese national holidays red, Saturdays blue.
- Read all calendars already synced to Android using Android Calendar Provider and user-granted permissions.
- Show events clearly and support event creation/editing through platform calendar intents or carefully permissioned provider operations.
- Light and dark themes, Japanese UI, no ads, no server, no subscription.
- Publish installable APK via GitHub Releases only after build and tests pass.

## Development loop (inspired by issue-to-PR coding agents)
1. Inspect repository state and CI results.
2. Select the smallest unblocked user-visible task.
3. Implement with focused tests.
4. Run Gradle build, unit tests, and lint in GitHub Actions.
5. On failure, inspect logs, fix the cause, and rerun; never claim a pass without evidence.
6. Open a PR for review, record commit SHA and remaining risks.
7. Repeat on subsequent authorized runs; avoid duplicate work.

## Guardrails
- Zero additional paid services by default; never enable billable AI/model APIs without explicit user consent.
- Public repository: NEVER commit calendar events, account identifiers, access tokens, keystores, or signing secrets.
- Avoid untrusted PR code execution with write-capable tokens or secrets.
- Keep AI-generated changes reviewable; do not auto-merge changes affecting permissions, secrets, publishing, or authentication.
- Do not invent rokuyō values: use a validated Japanese lunisolar conversion source and cross-check reference dates.
- Do not confuse automated scheduling with continuous execution.
- Record completed vs planned vs blocked work truthfully.

## Current status
This document is a development contract, not a running autonomous agent. AI runtime/provider configuration and Android CI must be implemented and verified separately.
