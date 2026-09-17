# Decisions

Each entry: what was decided, why, what it costs. Newest last. Owner decisions are marked; the
rest are implementation decisions the owner can overturn at a gate.

## D-01 · Provisional mission content and acceptance check in the absence of the brief (2026-09-17)

`PRODUCT_BRIEF.md` and `LEARNER_PROFILE.md` were not in the repository or the connected folder in
session 1. Rather than stop, the mission (*Een afspraak verzetten*, A2, dentist base scenario,
hairdresser transfer scenario), the four provisional language targets, the evidence expectations
and acceptance check **A01 = "fixture integrity"** (file validates, stored copy matches by hash,
normalised steps agree, pack under its word limit, every text labelled, four skills covered, both
variants resolve, help ladder Persian/RTL and absent in the checkpoint, authoritative dates
coherent) were written from the build prompt and the known 0.1 scope. **To reconcile with the brief
at Gate 1**; anything the brief defines differently wins.

## D-02 · What counts toward the 300-word fixed Dutch pack

The pack is the Dutch the learner reads or hears as lesson content: reading text, listening
transcript, questions and options, speaking/checkpoint goals, writing prompt, character lines,
reason options and slot notes (regex `PACK_PATH` in `content/schemas.py`). Titles, instructions,
roles, settings, can-do statements and success criteria are interface guidance shown bilingually
and are counted separately (`interface_word_count`). The pack is 297 words; the limit is enforced
at load time and by A01.

## D-03 · Assertion between web and API: HS256 shared secret

A short-lived HS256 JWT with a 32+ character server-only secret, issuer/audience/expiry/jti, and
the owner allowlist checked again in the API. Asymmetric keys (the API holding only a public key)
would stop a compromised API from minting assertions, but both tiers sit inside the same trust
boundary in 0.1 and the extra key handling would burden the laptop setup. The verifier is one
function (`identity/assertions.py::validate_assertion`); switching to RS256/EdDSA in Phase B is a
configuration and key-loading change, not a redesign.

## D-04 · CSRF: custom header plus origin checks, no cookies

The API uses no cookies, so classic CSRF cannot ride on ambient credentials; the defence still
matters because the web proxy attaches identity server-side. Unsafe methods must carry
`X-Requested-With: fetch` (a header a cross-site form cannot set), and the proxy also checks
`Sec-Fetch-Site`/`Origin`. The API enforces the header again so the rule holds even if the proxy is bypassed.

## D-05 · Fixture identity is accepted in `development` and `test`, refused elsewhere

The prompt binds the fixture to `APP_ENV=development`. The automated test suite runs as
`APP_ENV=test` and needs the same principal path, so `test` is accepted too. `production` refuses
`DEV_AUTH_ENABLED=true` at startup in both tiers, and the web tier additionally binds the fixture to
requests whose `Host` is localhost.

## D-06 · Same Azure SDK adapter for Azurite and Azure Blob Storage

`AzureBlobStore` talks to Azurite (connection string) in Phase A and to a private container
(account URL + managed identity) in Phase B. One adapter, one set of tests; the Phase B difference is
credentials. The managed-identity path is an M3 item and is `not_started` until unit-tested.

## D-07 · Usage counters enforced in SQL

`used + reserved + amount <= limit_value` is checked inside the `UPDATE`, in one transaction for
the daily and the total counter, with a nested transaction so a refusal leaves nothing behind. The
concurrency test (20 threads, 120-second daily budget, 10 seconds each) shows exactly 12 successes.
Cost: two rows per learner, metric and day; negligible.

## D-08 · Azure speech adapters deferred to M3, declared now

`AzureSpeechToText` / `AzureTextToSpeech` exist as classes so configuration, the registry and
preflight already know them, but they raise `ProviderUnavailable` and are reported as
`pending_m3`. They will use the Speech REST endpoints for short audio (push-to-talk turns are ≤ 30 s)
and be unit-tested with recorded fixtures before they may be called `integration_pending`.

## D-09 · Storage of files

Committed: source, tests, migrations, content, the two small synthetic WAV fixtures (a tone for
the API tests, a tone for the browser's fake microphone), docs, CI. Ignored: `.env`, `instructions/`,
`D/` and any PDF, `.local/` (whisper cache, Piper voices), benchmark results, recordings, Playwright
output, dependencies. No real recording is committed until the owner supplies one (OWNER_ACTIONS 4).

## D-10 · Build workspace versus the owner's laptop

Session 1 built and verified in a Linux build workspace (PostgreSQL 16, Azurite, ffmpeg, headless
Chromium with a fake microphone). Ollama, faster-whisper models and Piper voices could not be
downloaded there, so those provider paths were exercised against a mock OpenAI-compatible server
and fixture implementations only. The report uses `verified_workspace` for what ran end to end there
and keeps `verified_local` for the owner's laptop. Nothing is claimed as verified on the laptop.

## D-11 · Cross-platform task runner instead of shell-only scripts

The owner works on Windows with Docker Desktop and WSL 2. `scripts/run.py` (plain Python) runs
every routine task on Windows, WSL, macOS and Linux; the `Makefile` only delegates to it.
