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

## D-12 · Gate 1 outcome and the shape of the turn loop

Gate 1 closed on 2026-09-18: the owner ran the foundation on the laptop (VALIDATION_REPORT, owner
laptop run) and opened M2 with "start M2"; D-01 to D-11 stand unchanged. The instruction files are
still absent, so the mission content and A01 remain provisional (D-01).

The conversation turn is one small LangGraph graph with typed state (`domains/practice/workflow.py`):
`propose_action` (model, structured output `ProposedActionReply`) → `validate_action` (code,
`apply_action` against the scenario's authoritative slots) → `compose_reply` (model, structured
output `CharacterReply`, anchored on the scenario's fixed line for the current phase). The model
interprets and phrases; it never decides. If the model fails, or if its reply announces a booking the
code did not accept, the fixed line is used and the turn records `reply_source = fixed_line` plus the
error text. Two model calls per turn (`MODEL_CALLS_PER_TURN`) and 1 800 tokens are reserved before
the call, the measured usage is committed after it, and a failure releases both reservations.
Prompt templates carry version tags (`propose-action-v1`, `character-reply-v1`) that are stored with
every turn. Alternative considered: one call that both decides and replies; rejected because the
reply would then have to be parsed to find out what the model "did", and the code could no longer
be the authority on the appointment.

Typed and spoken turns share `submit_turn`; the spoken path only adds upload → canonical WAV →
transcript in front of it. Evidence is written per turn: `transcript` (speech) or `typed_text`
(typed, labelled as such) plus `action_result`; the skill record for speaking moves to
`in_progress` on the first turn and to `practised` (speaking step) or `checkpoint_passed`
(checkpoint) when the required actions are done.

## D-13 · Session semantics: resume, one attempt at the checkpoint, failed turns kept

One active practice session per learner, mission and variant: `POST /practice/sessions` resumes the
active session of that variant instead of opening a second one, and the lesson page loads active
sessions on every visit, so a reload never loses a conversation. `POST …/abandon` closes a session
without completing it. A variant whose checkpoint declares `retry: false` gets exactly one session:
once it is `completed`, `ended` (turns exhausted) or `abandoned`, a new one is refused with 409.
A retry with the same request id returns the stored turn (or repeats its 502 when that turn failed)
and never runs the model twice; a failed turn is kept as a row with its error so the failure is
visible and countable, and the response is returned rather than raised so the transaction commits.
The browser client reuses the request id after a network failure and mints a new one after a 502.
