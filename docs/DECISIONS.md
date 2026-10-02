# Decisions

What was decided, why, and what it costs. Newest last. Numbers are kept so that code comments and
older notes still resolve.

## D-01 · Provisional mission content and the fixture-integrity check

The first mission (*Een afspraak verzetten*, A2: a dentist base scenario and a hairdresser transfer
scenario), its four provisional language targets, the evidence expectations and acceptance check
**A01 = fixture integrity** (the file validates, the stored copy matches by hash, normalised steps
agree, the pack stays under its word limit, every text is labelled, four skills are covered, both
variants resolve, the help ladder is Persian/RTL and absent in the checkpoint, authoritative dates are
coherent) were written from the release scope. All of it stays provisional until a language reviewer
has seen it.

## D-02 · What counts toward the 300-word fixed Dutch pack

The pack is the Dutch the learner reads or hears as lesson content: reading text, listening
transcript, questions and options, speaking/checkpoint goals, writing prompt, character lines,
reason options and slot notes (regex `PACK_PATH` in `content/schemas.py`). Titles, instructions,
roles, settings, can-do statements and success criteria are interface guidance shown bilingually
and are counted separately (`interface_word_count`). The pack is 297 words; the limit is enforced
at load time and by A01.

## D-03 · Assertion between web and API: HS256 shared secret

A short-lived HS256 JWT with a 32+ character server-only secret, issuer/audience/expiry/jti, and
the allowlist checked again in the API. Asymmetric keys (the API holding only a public key) would
stop a compromised API from minting assertions, but both tiers sit inside the same trust boundary
and the extra key handling would burden the laptop setup. The verifier is one function
(`identity/assertions.py::validate_assertion`); switching to RS256/EdDSA later is a configuration and
key-loading change, not a redesign.

## D-04 · CSRF: custom header plus origin checks, no cookies

The API uses no cookies, so classic CSRF cannot ride on ambient credentials; the defence still
matters because the web proxy attaches identity server-side. Unsafe methods must carry
`X-Requested-With: fetch` (a header a cross-site form cannot set), and the proxy also checks
`Sec-Fetch-Site`/`Origin`. The API enforces the header again so the rule holds even if the proxy is
bypassed.

## D-05 · Fixture identity is accepted in `development` and `test`, refused elsewhere

The automated test suite runs as `APP_ENV=test` and needs the same principal path as development.
`production` refuses `DEV_AUTH_ENABLED=true` at startup in both tiers, and the web tier additionally
binds the fixture to requests whose `Host` is localhost.

## D-06 · Same Azure SDK adapter for Azurite and Azure Blob Storage

`AzureBlobStore` talks to Azurite (connection string) locally and to a private container (account
URL + managed identity) in the cloud. One adapter, one set of tests; the difference is credentials.

## D-07 · Usage counters enforced in SQL

`used + reserved + amount <= limit_value` is checked inside the `UPDATE`, in one transaction for
the daily and the total counter, with a nested transaction so a refusal leaves nothing behind. The
concurrency test (20 threads, 120-second daily budget, 10 seconds each) shows exactly 12 successes.
Cost: two rows per learner, metric and day; negligible.

## D-08 · Azure speech adapters declared early, verified later

`AzureSpeechToText` / `AzureTextToSpeech` exist as classes so configuration, the registry and
preflight know them. They use the Speech REST endpoints for short audio (push-to-talk turns are
≤ 30 s) and are unit-tested with recorded fixtures; they stay `integration_pending` until a live run.

## D-09 · Storage of files

Committed: source, tests, migrations, content, the two small synthetic WAV fixtures (a tone for
the API tests, a tone for the browser's fake microphone), docs, CI. Ignored: `.env`, `instructions/`,
`D/` and any PDF, `.local/` (whisper cache, Piper voices), benchmark results, recordings, Playwright
output, dependencies. No real recording is committed.

## D-10 · Two verification environments

The API suite and the browser suite run anywhere with PostgreSQL 16, ffmpeg and headless Chromium
(fake microphone), using fixture providers. Ollama, faster-whisper models and Piper voices only run
on the development laptop. `docs/VERIFICATION.md` keeps the two apart: `verified_local` is reserved
for behaviour exercised with the real local providers; CI evidence is called what it is.

## D-11 · Cross-platform task runner instead of shell-only scripts

Development happens on Windows with Docker Desktop and WSL 2. `scripts/run.py` (plain Python) runs
every routine task on Windows, WSL, macOS and Linux; the `Makefile` only delegates to it.

## D-12 · The shape of the conversation turn

The conversation turn is one small LangGraph graph with typed state (`domains/practice/workflow.py`):
`propose_action` (model, structured output `ProposedActionReply`) → `validate_action` (code,
`apply_action` against the scenario's authoritative slots) → `compose_reply` (model, structured
output `CharacterReply`, anchored on the scenario's fixed line for the current phase). The model
interprets and phrases; it never decides. If the *reply* call fails, or if the reply announces a booking
the code did not accept, the fixed line is used and the turn records `reply_source = fixed_line` plus
the error text. If the *first* call fails (model unreachable, timeout) the turn fails with 502: without
the model's reading no action can be recognised, so a fixed-line answer would only simulate a
conversation and, in the checkpoint, burn the single attempt. Failed turns do not count against the
step's turn limit. A refused connection to the chat endpoint is reported at once as unavailable, without
the retry backoff meant for transient errors. Two model calls per turn (`MODEL_CALLS_PER_TURN`) and
1 800 tokens are reserved before the call, the measured usage is committed after it, and a failure
releases both reservations. Prompt templates carry version tags that are stored with every turn.
Alternative considered: one call that both decides and replies; rejected because the reply would then
have to be parsed to find out what the model "did", and the code could no longer be the authority on
the appointment.

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

## D-14 · Evidence for the other three skills, feedback that can only cite evidence, the export

Reading and listening answers are judged on the server against the mission document (`practice/steps.py`)
and stored as `answer` evidence with the attempt number; the browser only collects choices. Every help
rung opened is `help_used` evidence (refused in the checkpoint, capped by `help_policy.max_level`). The
writing draft autosaves into the session state (`state.drafts`, not evidence); the submitted message is
`typed_text` evidence with its word count and the required words found or missing, refused outside the
word bounds. The listening clip is synthesised once from the transcript with the local voice, stored
under the step's `audio_key` in the blob store with a sidecar that carries its label, and served from
there afterwards; the cloud release overwrites that object with the Azure `nl-BE` voice.

Feedback (`domains/feedback/service.py`, one model call) is only produced when the mission's
`evidence_expectations` for the skill are met, including at least one code-validated action for
speaking. The model sees the step's evidence as numbered handles (E1, E2, …) and must cite them per
point; the code resolves handles to evidence ids and drops every point without a valid citation or with
a quote that does not occur in the cited evidence. Dropped points are stored and counted, never shown.
Reports live in `feedback_reports` (migration 0002); the skill record notes the report id. This is
feedback on a step, never an assessment of the skill. The export (`GET /export`, allowlisted accounts)
is one JSON document with the learner, the four skill records, every session with turns, evidence and
feedback, and the usage snapshot.

Every database connection is pinned to UTC (`options=-c timezone=UTC`): the API's ISO timestamps must
compare the same whether a value was just written or loaded from PostgreSQL (whose server time zone can
be Europe/Brussels), and the browser merges concurrent updates by instant.

## D-15 · First Azure shape (superseded by D-17)

Historical. One resource group, one Container Apps environment (consumption, scale to zero): `dlp-web`
with external ingress and the platform's built-in Microsoft Entra authentication (the proxy reads the
`X-MS-CLIENT-PRINCIPAL-*` headers and applies the allowlist), `dlp-api` with internal ingress only, so
the web app stays the single public entry. PostgreSQL Flexible Server `Standard_B1ms`, Storage
`Standard_LRS` with shared-key access disabled, Azure AI Speech `S0` with local authentication disabled
and a custom subdomain, Key Vault (RBAC) for the signing key and the database password, Container
Registry `Basic`, Log Analytics. The Speech adapters use the REST endpoints for short audio with a key
or an Entra token, because every turn is at most 30 s and the streaming SDK would add a native
dependency for nothing. Deployment is a manual GitHub Actions workflow authenticated with OpenID
Connect (federated credential; no cloud secret stored in GitHub).

## D-16 · Typed input never counts as speaking practice; acceptance checks over the data

The goal of the speaking step can be reached with typed text (the practice step allows the typed
fallback), but the speaking skill record only moves to `practised`/`checkpoint_passed` when the step has
at least one spoken (`transcript`) evidence record; a typed-only completion is recorded as such and the
page offers a fresh practice session. Checks A02–A06 (`domains/practice/acceptance.py`) are read-only
queries over the stored data — separate skill records, no typed credit, feedback citations resolve to
the step's evidence, checkpoint independence, settled usage — runnable at any time from the CLI, the
API and `scripts/verify_live.py`, so the claims in the verification notes can be re-checked by anyone.

## D-17 · Learner experience and controlled Azure release

The product label is Taalstudio, with one desktop/mobile shell, separated learning and technical
settings, four evidence-based skill records and local recording replay. No fictitious scores,
certificates or reviewed-content claims are added. Primary app navigation waits for writing autosave;
automated accessibility checks supplement, not replace, manual review.

The cloud profile uses a warm 0.25-vCPU API for its PostgreSQL job loop; the web can scale to zero.
PostgreSQL is VNet-private. An explicit, bounded migration job uses a separate identity and
administrator connection, while the API uses a DML-only role. Azure chat is required in production,
authenticated through managed identity, with a pinned, region-supported deployment. Separate per-secret
Key Vault grants prevent the web/API from reading migration credentials. Create foundation, images and
migration job first; run migrations; deploy the apps privately; configure and verify sign-in; publish
explicitly. The release workflow requires exact-commit main CI and protected OIDC deployment approval.
A budget alert is not a hard currency cap. Paid use is switched on deliberately (`PAID_USAGE_ENABLED`),
never by the presence of credentials.

## D-18 · A generated serial instead of more templated stories — 2026-10-02

The static libraries (1 200 Story Time texts, 4 800 topic activities) are templated and heavily reused:
from A2 upward every story in a stage asks the same question, and neighbouring stages share most texts.
Rather than hand-writing more of the same, the model now writes a continuing serial per learner
(`domains/stories`): a fixed, original cast and town, the learner's level and saved words as input,
one episode written ahead of time by the job loop. The model proposes; a deterministic validator
(`stories/validator.py`) decides: Dutch, length and sentence complexity per stage, vocabulary
coverage against the stage banks plus the learner's own words, every comprehension question backed by a
sentence copied from the text, regional `gij/ge` only when labelled. A failed draft is rewritten once
with the validator's findings; a second failure is shown to the learner as a failure, never as a story.
Each episode ends with a two-way choice that is fed to the next one; the next episode is not written
until the choice is made or twelve hours have passed. Episodes are labelled as generated content and
remain unreviewed by a teacher. Usage is reserved per attempt through the existing counters; two model
calls per episode at most.

## D-19 · Daily plan, points and spaced repetition — 2026-10-02

Reading an episode, answering its questions, choosing, reading aloud and reviewing words earn points
for the day (`learning_days`, one row per learner per Europe/Brussels day). A streak counts consecutive
active days; the daily goal is twenty points. Points reward doing and are never a judgement of the
learner's Dutch. Saved words (`vocab_items`) are scheduled with SM-2 (ease 1.3–∞, intervals 1 → 6 →
ease-multiplied days); a lapse brings the card back after ten minutes within the same session. The word
bank is the learner's own choice: nothing enters it unless they save it.

## D-20 · Read-aloud compares words, it does not score pronunciation — 2026-10-02

Reading a paragraph aloud sends the recording through the normal transcription path (no storage) and
reports which target words the transcriber recognised and which it did not. Points are awarded once
per paragraph when at least half the words are recognised. No accent or pronunciation score is
computed or shown, because a transcript cannot carry one.

## D-21 · A direct order is not a mistake — 2026-10-02

The first live lunch conversation answered *"Ik wil graag een broodje kip en een water"* with *"Dat kan
niet. Kies uit het aanbod."*: the rules required the need to be stated before an option could be chosen,
the model had labelled the sentence a choice, and the refusal borrowed the line meant for an option that
is not on offer. Three changes. A valid option named straight away now counts as stating the need, and
a stated need that names an option selects it, so nobody repeats themselves and the character asks for
confirmation next. A scenario can set `reason_before_choice` (the shop return does, in both variants):
the option is kept but the character asks what the problem is before anything can be confirmed. And the
"not on offer" line is only used for an option that is not on offer; a premature "yes" simply gets the
question of the current phase. The interpretation prompt is `propose-action-v3`.
