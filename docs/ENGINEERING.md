# Engineering guide

### Learning support workflows

`domains/topic_conversations` uses a three-node LangGraph: interpret, validate, compose. The model
proposes meaning; code checks quoted learner evidence and fixed choices; authored content supplies
partner replies. PostgreSQL stores at most six turns per conversation, a content snapshot and stable
client turn identifiers. `domains/coaching` records append-only successful submissions (including
assessed attempts that need another try), filters obsolete content versions and returns three existing
activity links. Optional model ordering cannot alter their IDs or code-authored reasons.

`domains/content_review` runs explicit admin batches through the existing job loop. A durable claim,
version/model cache and one provider attempt per generation prevent automatic paid replay. Findings
reference exact authored text locations and never publish or mark content approved. Its API routes
register the worker; the standalone job CLI imports the same handler. Migration 0005 adds four tables
with learner-deletion cascades; self-export includes observations, conversations, plans and owned reviews.
All three roles use `complete_once`; legacy `complete` retry semantics remain unchanged.
See [LEARNING_AGENTS](LEARNING_AGENTS.md) for operational boundaries and targeted checks.

This is the collaborator-facing description of the scoped learner release. It is deliberately short: the
code is the reference, this explains why it is shaped the way it is.

### Release 0.2 conventions

- `AppShell` provides desktop and mobile navigation; `design.css` contains the shared visual system.
  Fonts are self-hosted. Dashboard/progress read persisted evidence only; technical diagnostics live
  in Settings. A shared navigation guard waits for writing autosave before app-link navigation.
- The web layout is dynamically rendered so runtime environment labels and per-response CSP nonces
  are correct. Script execution is nonce-based; inline styles remain allowed for React layout styles.
- `dlp.release migrate` is the only cloud schema-update path. The server starts Uvicorn directly with
  a DML-only role. `/health` is liveness; `/health/ready` requires the exact packaged migration head.
- Azure model calls use managed identity and the v1 endpoint; explicit keys remain supported for
  owner-controlled integration tests. The main runtime cannot read the migration or auth-client secret.
- Application Insights exports route templates, status and duration, not request bodies or identities.
  Provider auto-instrumentation is disabled. Cloud access logs are disabled at Uvicorn.
- The API production lock is `apps/api/requirements-azure.lock`; regenerate using `uv pip compile
  apps/api/pyproject.toml --extra azure --generate-hashes --output-file apps/api/requirements-azure.lock`.
  CI compiles Bicep and builds both actual Dockerfiles without creating any Azure resources.
- [GO_LIVE](GO_LIVE.md) is authoritative for deployment. Never infer real provider validation from
  a fixture, a model benchmark dry run, a configured endpoint or a compiled infrastructure template.

## 1. Architecture

```
browser ── same origin ──► Next.js (apps/web)  ── /api proxy, signed assertion ──► FastAPI (apps/api, localhost only)
                                                                                     │
                                                          ┌──────────────────────────┼──────────────────────────┐
                                                          ▼                          ▼                          ▼
                                                    PostgreSQL              providers package            ffmpeg / ffprobe
                                                    (state, jobs,           chat · stt · tts · blob       (audio canonicalisation)
                                                     usage counters)        local | azure | fixture
```

- The web server is the only public entry point. It resolves *who* is calling, strips any
  identity the browser may have sent, and forwards each request with a short-lived assertion.
- The API trusts only that assertion. It never sees a cookie, a session or a client-supplied identity.
- Everything external (models, speech, storage) is reached through `dlp.providers`. Application
  code depends on the narrow interfaces in `providers/base.py`, never on a vendor SDK.
- Dates, availability, permissions, task completion, usage limits and submissions are decided in
  application code. A model may *propose* an action (`practice/actions.py::ProposedAction`); the
  code validates it against the scenario's authoritative slots before the character may announce it.

## 2. Repository layout

```
apps/api/src/dlp/
  config.py            settings from environment / .env; production refuses fixture configuration
  main.py              app factory, lifespan (preflight log, job loop)
  cli.py               preflight · load-fixture · acceptance · run-jobs
  api/                 HTTP layer: deps (assertion, CSRF, request id), routers
  db/                  engine, session, declarative base, model registry
  domains/
    identity/          assertion validation, allowlist, learner bootstrap
    content/           mission schemas (contract, scenario, evidence), loader, acceptance check A01
    practice/          sessions, turns, evidence records, appointment action validation
    speech/            upload inspection, ffmpeg canonicalisation, transcription/synthesis use cases
    feedback/          (M2) feedback with cited evidence
    progress/          four separate skill records per learner and mission
    usage/             atomic check/reserve counters, deduplication, pricing table
    jobs/              durable PostgreSQL jobs: leases, backoff with jitter, restart recovery
  providers/           interfaces · registry · preflight · local, azure and fixture implementations
apps/api/migrations/   Alembic, versioned; run `alembic upgrade head`
apps/api/tests/        pytest; fixtures under tests/fixtures are synthetic unless stated otherwise
apps/web/app/          routes: /, /missions/[missionId], /speech-check, /api/[...path] (proxy)
apps/web/lib/server/   config, identity providers (fixture, easyauth), assertion issuance — server only
apps/web/lib/client/   fetch helper (anti-CSRF header, request ids)
apps/web/components/   lesson shell, reading step, help ladder, content labels, microphone check
apps/web/tests/e2e/    Playwright: proxy trust boundary, lesson shell at 1440/768/390 px, push-to-talk
content/missions/      one folder per mission with mission.json
benchmarks/language/   harness + 40 cases; results are ignored by Git
scripts/               run.py task runner, fetch_piper_voice.py, sql/
```

## 3. Conventions

- Python 3.11+, type hints everywhere, Pydantic models with `extra="forbid"` for content.
  `ruff` (line length 130) is the linter. Tests use the real database (`dlp_test`) and fixture providers.
- TypeScript strict; ESLint with the Next.js rules; no state-setting inside effect bodies.
- Every request carries an `X-Request-Id` (`^[A-Za-z0-9._-]{8,64}$`). The browser may supply one so
  that retries stay idempotent (session creation, usage reservations deduplicate on it); anything
  malformed is replaced. The id is echoed on every response and stored on rows it created.
- Fixed Dutch text is a `LocalizedText` (`nl`, `fa`, `review_status`). The UI labels anything that
  is not `reviewed`. The fixed pack (texts the learner reads or hears) must stay under
  `content_pack.word_limit`, counted by `MissionDocument.fixed_dutch_word_count()`.
- Statuses in `VALIDATION_REPORT.md` follow the fixed vocabulary: `implemented_local`,
  `verified_local`, `integration_pending`, `verified_live`, `review_pending`, plus
  `verified_workspace` for things proven end to end in the build workspace but not yet on the owner's laptop.

## 4. Provider abstraction

| Interface | Local (Phase A) | Fixture (CI) | Azure (Phase B) |
|---|---|---|---|
| `ChatModel` | `OpenAICompatibleChatModel` → Ollama `/v1` | `FixtureChatModel` (canned replies) | same class, Azure OpenAI URL + `api-key` |
| `SpeechToText` | `FasterWhisperSpeechToText` (`nl`) | `FixtureSpeechToText` (sidecar transcript) | `AzureSpeechToText` (M3) |
| `TextToSpeech` | `PiperTextToSpeech` (`nl_BE` voice, label `synthetic-development`) | `FixtureTextToSpeech` (tone) | `AzureTextToSpeech` (M3) |
| `BlobStore` | `AzureBlobStore` against Azurite | `MemoryBlobStore` | `AzureBlobStore` against a private container |
| Identity | fixture principal in the web tier | same | Container Apps built-in auth headers |

`providers/registry.py` builds them from `CHAT_PROVIDER`, `STT_PROVIDER`, `TTS_PROVIDER`,
`BLOB_PROVIDER`. `providers/preflight.py` reports mode and reachability without secrets
(`python -m dlp.cli preflight`, `GET /health/preflight`).

Chat calls: one client for local and Azure; JSON-schema instruction in the system prompt,
`response_format: json_object`, first-JSON-object extraction, Pydantic validation, one repair
round per attempt, bounded attempts with jittered backoff, a concurrency semaphore, and usage
figures from the reply (estimated when absent). Prompt templates carry a `prompt_version` tag
that lands in every result and benchmark file.

## 5. Trust boundaries

1. **Browser → web server.** Same origin only. Unsafe methods must carry `X-Requested-With: fetch`
   and pass the `Sec-Fetch-Site` / `Origin` check in the proxy. Client-sent `Authorization`,
   `Cookie` and `X-MS-CLIENT-PRINCIPAL*` headers are dropped.
2. **Identity.** `fixture`: only when `APP_ENV=development` and `DEV_AUTH_ENABLED=true`, and only for
   requests whose `Host` is localhost. `easyauth`: reads the headers the Container Apps auth sidecar
   injects; the web container must be reachable only through that sidecar (checked in Phase B by
   `scripts/verify_live.py`).
3. **Web server → API.** HS256 assertion signed with `ASSERTION_SIGNING_KEY` (server-only, 32+
   characters), issuer `dlp-web`, audience `dlp-api`, `exp` = 60 s, `jti`, subject, email,
   identity provider and request id. The API rejects missing, expired, foreign, over-long or
   unlisted assertions and requires the anti-CSRF header again on unsafe methods.
4. **Production.** `APP_ENV=production` refuses `DEV_AUTH_ENABLED=true`, fixture providers and the
   memory blob store at startup, in both tiers.
5. **Audio.** Uploads are bounded (`MAX_UPLOAD_BYTES`, `MAX_AUDIO_SECONDS`), inspected with
   `ffprobe`, converted with `ffmpeg` to mono 16 kHz 16-bit PCM WAV, under a timeout and an
   address-space limit, with argument lists and no shell.

## 6. Speech mode

Push-to-talk only in 0.1: `MediaRecorder` (container/codec chosen with `isTypeSupported`) →
multipart upload → canonical WAV → `SpeechToText` → transcript stored as evidence with modality
`speech`. Typed input is stored with modality `typed` and never counts as speaking practice.
Replies are synthesised to WAV and always carry `X-Audio-Label` (`synthetic-development` for
local voices). Streaming is not part of 0.1.

### 6.1 The conversation turn

`domains/practice/turns.py::submit_turn` is the one entry point for a learner turn, typed or
spoken (`api/routes_practice.py`: `POST /practice/sessions/{id}/turns` with `{step_key, text}`,
`POST …/turns/speech` with multipart `audio` + `step_key`). Order of work:

1. request-id deduplication (a stored turn is returned; a stored failure is repeated as 502);
2. `ensure_turn_allowed`: session active, step is a conversation step of this variant, modality
   allowed (the checkpoint refuses typed input), turn limit not reached — all before any provider call;
3. for speech: upload → `canonicalise` → `SpeechToText` → transcript (422 when empty);
4. reserve `model_calls` (2) and `tokens` (1 800) for the request id;
5. `workflow.run_turn` — the LangGraph graph `propose_action` → `validate_action` → `compose_reply`
   (`domains/practice/workflow.py`, prompts and versions in `prompts.py`);
6. commit the measured usage, store the turn (`proposed_action`, `action_result`, `character_text`,
   `model_meta` with phase, reply source, model calls, errors), write the evidence rows, update the
   session state (`appointment`, `step_progress`), the skill record and the session status
   (checkpoint: `completed` when the required actions are done, `ended` when the turns run out);
7. synthesise the reply (`_attach_character_audio`); a synthesis failure is recorded on the turn and
   never fails it.

A model failure marks the turn `failed`, releases the reservations and is *returned* as a 502 body
(not raised) so the transaction commits. `GET …/turns/{turn_id}/audio` serves the character line.
The session view carries `conversation[]` (opening line, character, limits, restrictions, slots) so
the client needs no scenario logic of its own. The fixture chat model (`providers/fixtures.py`)
resolves keyword rules from `tests/fixtures/chat_replies.json`, which is how the browser tests run
the whole loop without a model.

### 6.2 Evidence for the other steps, feedback, export

`domains/practice/steps.py` judges reading and listening answers against the mission document and stores
`answer` evidence; records help-ladder use (`help_used`); keeps the writing draft in `state.drafts` and
stores the submitted message as `typed_text` evidence. `GET /missions/{id}/audio/{key}` synthesises a
listening clip once and serves it from the blob store. `domains/feedback/service.py` produces one
`feedback_reports` row per request: the model sees the step's evidence as handles and every point it
returns must cite handles that resolve; the rest is dropped and counted (`dropped_points`). `GET /export`
returns everything about the learner as one JSON document. Database connections run in UTC
(`db/session.py`) so timestamps compare the same in the browser regardless of where they came from.

## 7. Usage counters and jobs

`usage/service.py` reserves before every external call (`reserve` → `commit`/`release`), per
metric (`model_calls`, `tokens`, `audio_seconds`), per scope (`daily`, `total`), with the limit
enforced inside the SQL `UPDATE` for the reserved amount; the same reservation key returns the existing
reservation. Measured usage may exceed the initial estimate and is recorded. Provider invocation keys
are generated on the server, distinct from browser tracing IDs. Conversation/report idempotency is
handled before provider execution; raw STT/TTS calls execute and consume allowance on every request.
Counters are not an exact Azure invoice or a process-crash-proof billing ledger. The pricing table
stays empty until Phase B.

Upload handlers use synchronous FastAPI endpoints so blocking ffmpeg, SQL and SDK calls run in the
worker pool. Anticipated refusals after successful STT return an error response without rolling back
its recorded usage. Model call/token reservations are grouped in a savepoint to avoid partial holds.
Recording storage errors preserve the transcript with an explicit warning. Fixed listening clips are
cached by content hash, exact text, provider and voice; the browser must revalidate through the API.
The old unversioned clip path is no longer the storage key.

`jobs/service.py` keeps durable jobs in PostgreSQL: claim with `FOR UPDATE SKIP LOCKED` and a
lease, exponential backoff with full jitter, `max_attempts` then `dead`, expired leases are
reclaimable after a crash, one idempotency key per job. The in-process loop starts with the API
(`JOB_LOOP_ENABLED`) and is bounded by the poll interval.

## 8. Startup, tests, deployment

- `python scripts/run.py setup|services|migrate|fixture|preflight|dev|test|e2e|benchmark|acceptance`. Started from an activated conda env (`environment.yml`, name `dlp`) or virtualenv the runner uses that interpreter; otherwise it creates `apps/api/.venv`.
- API tests: `pytest` in `apps/api` (needs `dlp_test` and ffmpeg; Azurite tests skip when it is down).
- Browser tests: `python scripts/run.py e2e` builds the web app, starts both tiers with fixture
  providers and runs Playwright with a fake microphone (`tests/e2e/fixtures/speech-input.wav`).
- CI (`.github/workflows/ci.yml`) runs lint, the API suite, the benchmark dry runs, the web build and the browser tests.
- Acceptance: `python scripts/run.py acceptance` runs A01 (content integrity) and A02–A06 (data integrity:
  `domains/practice/acceptance.py`); the same checks answer at `GET /missions/{id}/acceptance/all`.
- Deployment (Phase B, not executed): `infra/main.bicep` (validated with the Bicep CLI) describes one
  Container Apps environment — public web app with built-in Entra sign-in, internal API, PostgreSQL,
  Storage, Speech, optional Azure OpenAI, Key Vault, managed identities; `apps/*/Dockerfile` build from the
  repository root; `.github/workflows/deploy.yml` is a manual OIDC workflow; `docs/GO_LIVE.md` is the
  owner's runbook and `scripts/verify_live.py` the black-box check that moves the Azure adapters from
  `integration_pending` to `verified_live`.

## 9. Configuration contract

Every variable lives in `.env.example` with a comment. Secrets: `ASSERTION_SIGNING_KEY`,
`DATABASE_URL` (Phase B), `HF_TOKEN` (optional), `AZURE_CHAT_API_KEY`, `AZURE_SPEECH_KEY`,
`AZURE_STORAGE_CONNECTION_STRING` (the published Azurite string is not a secret). The web tier
reads `APP_ENV`, `DEV_AUTH_ENABLED`, `DEV_OWNER_EMAIL`, `DEV_OWNER_NAME`, `API_INTERNAL_URL` and the
`ASSERTION_*` variables; the API reads the rest. `scripts/run.py` passes the root `.env` to both.

## Learning-path boundary

`content/curriculum/path.json` contains original lesson units and separate final checks. It is validated
before release migrations. `domains/curriculum` owns schema validation, practice records, versioned
assessment snapshots and within-stage final-check readiness. `api/routes_curriculum.py` uses the same verified
identity and budget controls as other API routes. The browser never chooses a learner identity or a pass.

- Twelve ordered stages; pre-stages provide transition practice, including A2 → pre-B1 → B1.
- Each of the four practice skills must be attempted before a student's final check opens.
- Reading and listening require 75% each; writing and speaking require their explicit task criteria.
  These are internal course rules, not CEFR cut scores. There is no aggregate score.
- Speaking requires a fresh, owned recording with recognised speech. The rubric reviews the transcript;
  it cannot assess accent, prosody or authenticate who spoke. The recorder stays within the short-audio
  service limit. Longer interactive oral examinations need a future speech workflow.
- All stages are open; model failure never awards a passing result. Completed skill evaluations can be reused on an identical retry.
- `CURRICULUM_ADMIN_EMAILS` is a separate, explicit account list for tester previews. Empty means no
  bypass. Preview attempts are stored separately and do not become student progression evidence.
- Assessment API responses omit answer keys, listening scripts and sample responses. Authored items
  remain in the repository, so this is a practice platform, not a secure standardised examination system.
- Productive feedback includes observable evidence; model/provider identifiers stay in operational data.

The web components are grouped into path, lesson, final check and shared audio/question controls.
`LanguageSupport` owns the three support-language modes. The lesson always retains Dutch; Persian
uses RTL. On-device writing drafts are scoped to the verified learner and stage, and are cleared on
sign-out. Assessment answers are not displayed in browser storage as correct-answer keys.

Source extraction is a separate local workflow. `scripts/index_teaching_sources.py` produces a public
metadata inventory and private unverified OCR/review candidates. `.local/source-import` is ignored;
scans, full textbook text and handwriting must not be included in commits. See `SOURCE_COVERAGE.md`.

The design uses restrained navy and blue, readable content widths, visible keyboard focus, large
interactive controls and responsive layouts. Accessibility checks use WCAG criteria, not a visual
claim of certification: <https://www.w3.org/WAI/standards-guidelines/wcag/new-in-22/>.

Future practice videos belong to approved lesson assets with a transcript, captions and four-skill
activities. No video-generation provider, cost or empty video tab is introduced in this release.


## Extended practice library

`domains/curriculum/library.py` validates the twelve original content banks in `content/library/`.
`api/routes_library.py` requires the same authenticated identity as all other learner routes. Pagination
is bounded (50 vocabulary items or 30 story summaries maximum); opening a story fetches its paragraphs
and practice question. Search is literal, Unicode-normalised and includes the three supported languages.
Release validates all banks before database migration. Structural constraints include 500 unique terms,
100 distinct Dutch stories, two paragraphs, complete translations and valid vocabulary links per stage.
These checks are not linguistic certification. Raw OCR is never used as the serving library.

`PhraseAudio` uses the existing speech route, explicit clicks, a single active player and a bounded
32-entry/8MB tab-only cache. It observes cancellation and revokes object URLs. Microphone and other
players share audio focus. Drafts are not sent for writing review on each keystroke. The writing-feedback
endpoint applies model-proposed edits only if they identify exact, unique, nonoverlapping source spans;
it reconstructs the corrected draft in code. The client requires an explicit choice to adopt it.
Correction requests consume the existing model allowance; cached phrase replay does not call TTS again.

Read marks are keyed by learner and stage in browser storage, cleared at logout and never written to
assessment records. Practice questions expose their answers for self-check; final-test answer boundaries
remain unchanged. Fixture audio is a labelled tone and fixture writing does not pretend to correct text.


## Topic practice

Versioned topic banks live in `content/practice`; each stage has at least 100 distinct situation
IDs and all four activities. `/curriculum/{stage}/topics` exposes paginated authenticated summaries
and on-demand task detail. Answer keys remain server-side until an attempt is submitted.
`topic_practice` stores learner/stage/topic/skill evidence with a content hash and sticky completion;
the existing curriculum aggregate continues to control within-stage final-check readiness.
A new migration is required before the API release. The release job validates every bank first.
The learner export includes topic evidence and deleting a learner cascades to these records.
Draft keys include learner, stage, skill and topic; stale network replies cannot replace another
topic. Listening players and recording uploads are cancelled when their activity unmounts.

Topic practice POSTs do not automatically retry and do not deduplicate productive feedback by
request ID. An explicit resubmission can consume another model call. Concurrent responses for the
same learner/topic/skill use a unique database upsert: the last stored response supplies the latest
evidence and result, while a previously earned completion stays true. This is separate from final
checks, whose saved partial assessments support identical-submission retries. A transport failure
after submission can leave the browser unsure whether a topic response was saved; refresh topic
progress before deliberately resubmitting.
