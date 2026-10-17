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
register the worker; `domains/jobs/handlers.py::register_all()` imports every handler module for the API's
job loop and for the standalone job CLI alike. Migration 0005 adds four tables
with learner-deletion cascades; self-export includes observations, conversations, plans and owned reviews.
All three roles use `complete_once`; legacy `complete` retry semantics remain unchanged.
See [LEARNING_AGENTS](LEARNING_AGENTS.md) for operational boundaries and targeted checks.

This is the collaborator-facing description of the scoped learner release. It is deliberately short: the
code is the reference, this explains why it is shaped the way it is.

### Release 0.2 conventions

- `components/shell` provides the frame: five destinations (`nav.ts`), the sidebar, header and bottom
  tabs, and `SectionTabs` for the second level; `app/styles/shell.css` styles it. Styles are global CSS in cascade layers
  (`app/styles/layers.css` fixes the order `reset, tokens, base, components, legacy, features, utilities`):
  `tokens.css` is the only stylesheet with colour literals (primitive ramps, semantic tokens, one accent
  set per section or skill selected by `data-accent` on a container, and compatibility aliases for the
  legacy layer), `reset.css` holds the reduced-motion and print rules, `base.css` the element defaults, type scale,
  focus ring, skip link and `.visually-hidden`, and the ten pre-existing
  stylesheets are wrapped in `@layer legacy` and shrink as screens move onto the primitives. No stylesheet
  outside `tokens.css` holds a colour literal; `lib/design/identity.ts` maps skills and sections to the
  accent a container sets with `data-accent` (D-24).
  Shared primitives live in `components/ui` (typed wrappers over one global class each, styled in
  `app/styles/ui/*.css` inside `@layer components`); icons come from `lucide-react` (pinned exactly) behind
  `components/Icon.tsx`, whose `IconName` union is the app's icon vocabulary. `/dev/ui` shows every primitive
  in every state outside production and is covered by `tests/e2e/ui-gallery.spec.ts` and a screenshot baseline.
  Motion is CSS only: `app/styles/motion.css` names every animation once and screens apply it with
  `data-anim`; each has a static reduced-motion state, and `lib/client/motion.ts` picks the attribute for an
  answer state. Toasts come from `useToast()` (the provider sits inside `.app-frame`); dialogs are native
  `<dialog>` elements rendered in place. Answer and goal tones (`lib/client/tones.ts`) are synthesised with Web
  Audio, off by default, stored under one key in `lib/client/storage.ts`.
  Progress visuals (`ProgressRing`, `ProgressBar`, `SkillMeter`) draw one measured value against one maximum
  and never an overall level; `lib/design/progress.ts` holds their arithmetic.
  Fonts are self-hosted. Dashboard/progress read persisted evidence only; technical diagnostics live
  in Settings. A shared navigation guard waits for writing autosave before app-link navigation.
- The web layout is dynamically rendered so runtime environment labels and per-response CSP nonces
  are correct. Script execution is nonce-based; inline styles remain allowed for React layout styles.
- `GET /me` is the one source of the learner's level, daily goal and support language (`learner_profiles`);
  every screen that chooses a level reads it, and `POST /me/onboarding` runs once per learner.
- `dlp.release migrate` is the only cloud schema-update path. The server starts Uvicorn directly with
  a DML-only role. `/health` is liveness; `/health/ready` requires the exact packaged migration head.
- Azure model calls use managed identity and the v1 endpoint; explicit keys remain supported for
  deliberately run integration tests. The main runtime cannot read the migration or auth-client secret.
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
- Statuses in `docs/VERIFICATION.md` follow a fixed vocabulary: `verified_local` (real local providers on
  the laptop), `verified_ci` (fixture providers in the automated suites), `verified_live` (the production
  deployment in Azure, signed in), `integration_pending` (configured, no live use recorded yet),
  `review_pending` (needs a human reviewer).

### Errors

Every expected failure is a subclass of `dlp.errors.DomainError` (`CurriculumError`, `PracticeError`,
`AudioError`, `VocabError`, `UsageLimitExceeded`, ...). Routes raise them; `dlp/api/errors.py` turns them into
one JSON body, `{"detail", "code", "request_id"}` plus any parameters, so the web app can map the stable
`code` (`usage_limit`, `provider_unavailable`, `story`, ...) to copy in the learner's languages. A provider
failure no route handled becomes 503 instead of 500. Routes that must commit work before answering
(usage rows, a failed turn) still return a `JSONResponse` themselves and include the same `code`. The request's
session (`api/deps.db_session`, function scope) commits once the route has returned and before the response is
sent, so a failed commit answers 500, never a 2xx whose writes were lost (D-33); every route and `context_dep` share
that one dependency, because FastAPI caches a dependency per request by its scope too and a second scope would open
a second session (`tests/test_today_contract.py` checks every route). A learner's `last_seen_at` is written at most
once every ten minutes, so most reads write nothing. That write no longer serializes one learner's requests, so
writes that touch several of the learner's rows take `identity.service.lock_learner` first, and a first insert
that may race uses ON CONFLICT DO NOTHING and reads the winner's row (learner, profile, story series).

A conflict a learner can reach carries its own code (`episodes_busy`, `videos_busy`, `not_ready`,
`already_answered`, `session_closed`, `turn_limit`, `no_retry`, `in_progress`, `evidence_short`,
`paid_not_approved`). The `detail` sentence is English and for developers; the browser never shows it.
`lib/client/errors.ts` (`errorFor`) picks the catalogue copy by code first and status second, a screen may
pass overrides for a code or a status, and `lib/client/error-copy.ts` (`errorCopy`) lets a screen name what
failed ("Bewaren lukte niet.") where the general message would only say that something did. Copy must be
true: only a screen that keeps the learner's typed or recorded answer passes the `input` context, and only
then do the messages say "Je invoer blijft staan"; a `load` shows the screen's own "kon niet worden geladen"
when the network or the API is down. A 502 means "the server is away" only when the proxy says so
(`api_unreachable`, `upstream_timeout`); the API's own 502 is a failed provider call that the screen words.
`tests/unit/errors.test.mjs` scans the API source and fails when a code has no copy and is not listed as
general on purpose, so a new code gets its sentence in the same change.

### Interface copy

Interface text lives in the catalogue, never in components: `lib/ui-copy.ts` for shared groups (navigation,
actions, states, errors, failures, welcome, honesty chips, about) and `lib/copy/*.ts` for one screen each
(episode, words, missions, speech, exercise). Every entry has `nl`, `en` and `fa`; `UiText` renders the Dutch
with the glosses the learner chose and the level allows. Persian appears per batch only after a fluent
reader has checked it: the owner reads a batch at `/dev/copy` and sets its flag in `lib/copy/review.ts`;
until then English stands in for learners who chose it, and Persian-only learners see Dutch alone.
Without a gloss shown, `UiText` takes no box of its own (`display: contents`), so moving a screen onto the
catalogue changes no pixels for a learner without glosses; with one, labels stack compactly and sentences keep
their paragraph's line height.
`tests/unit/dutch-text.test.mjs` counts Dutch still written into components with the TypeScript parser (JSX
text, strings a JSX expression renders, the spoken attributes and inline `nl:` labels) against
`dutch-budget.json`, an exact snapshot: a change that moves text into the catalogue lowers it in the same change.

### Server state in the browser

Data from the API is read through TanStack Query hooks (`lib/client/queries/*`, keys in
`lib/client/query-keys.ts`, client settings in `lib/client/query-client.ts`): the cache is the single copy,
sibling components share one request, a mutation invalidates the keys it changed, and server data is never
mirrored into `useState`. The query functions call the existing `apiJson`/typed client objects, so request
ids and the connectivity event are unchanged. Older components still fetch in effects; they move over as
they are touched.

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
  `E2E_ARGS` passes extra arguments to Playwright (a single spec, `--headed`, `--update-snapshots`).
- Every browser spec imports `test` from `tests/e2e/fixtures/test.ts`, which resets the learner profile
  (`POST /api/me/reset`) and onboards it at A1 with Dutch and English before each test, through the page
  so the same fixture works inside the pinned Linux container. The root layout prefetches `/me` on the
  server (`lib/server/me.ts`) and seeds the query cache; a failure there only means the client fetches it.
- Screenshot baselines: `apps/web/tests/e2e/aa-visual.spec.ts` compares eight learner screens at
  1440, 390 and 320 px with the PNGs in `tests/e2e/__screenshots__` (0.2 % pixel tolerance). They are
  rendered on Linux only, so the spec is skipped on a developer machine; `python scripts/run.py e2e-visual`
  runs it inside the pinned Playwright container against the servers on this machine, and
  `E2E_ARGS="--update-snapshots"` regenerates the baselines (commit them with the change that moved the
  pixels). The manual CI workflow `update_baselines` renders them on the runner and uploads an artifact.
- CSS ratchets: `tests/unit/css-guard.test.mjs` holds every stylesheet in `app/*.css` and `app/styles/*.css`
  to the colour literal, small-font, outline and `!important` counts in `tests/unit/css-budget.json`
  (`styles/tokens.css` is exempt from the colour count only); lower a budget in the same change that
  removes the rules, never raise one. `tests/unit/css-usage.test.mjs` fails on a selector no component
  uses, and `tests/unit/design-tokens.test.mjs` checks every promised text pair for 4.5:1 and every
  graphic pair for 3:1 in `:root` and in each `[data-accent]` block.
- CI (`.github/workflows/ci.yml`) runs lint, the API suite, the benchmark dry runs, the web build and the browser tests.
- Acceptance: `python scripts/run.py acceptance` runs A01 (content integrity) and A02–A06 (data integrity:
  `domains/practice/acceptance.py`); the same checks answer at `GET /missions/{id}/acceptance/all`.
- Deployment (live since 2 October 2026): `infra/main.bicep` (validated with the Bicep CLI) describes one
  Container Apps environment — public web app with built-in Entra sign-in, internal API, PostgreSQL,
  Storage, Speech, optional Azure OpenAI, Key Vault, managed identities; `apps/*/Dockerfile` build from the
  repository root; `scripts/deploy_current.sh` releases the checked-out commit from a signed-in `az`
  session once CI is green for it (`.github/workflows/deploy.yml` is the same release as a manual OIDC
  workflow, not yet configured); `docs/GO_LIVE.md` is the runbook and `scripts/verify_live.py` the
  black-box check. Preflight reports an Azure adapter as `ok` from stored evidence (a ready episode or a
  completed turn written by an `azure-*` provider, a stored recording or synthesis), never by calling
  the paid service itself.

## 9. Configuration contract

Every variable lives in `.env.example` with a comment. Secrets: `ASSERTION_SIGNING_KEY`,
`DATABASE_URL` (Phase B), `HF_TOKEN` (optional), `AZURE_CHAT_API_KEY`, `AZURE_SPEECH_KEY`,
`AZURE_STORAGE_CONNECTION_STRING` (the published Azurite string is not a secret). The web tier
reads `APP_ENV`, `DEV_AUTH_ENABLED`, `DEV_OWNER_EMAIL`, `DEV_OWNER_NAME`, `API_INTERNAL_URL`, `FIRST_RUN_GATE` and
the `ASSERTION_*` variables; the API reads the rest. `FIRST_RUN_GATE=on|off` overrides the first-run redirect
to /welkom, which is on by default outside production and off in production until the owner turns it on. `scripts/run.py` passes the root `.env` to both.

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


## Story serial, word bank and daily plan

`domains/stories` adds four tables (migration `0006`): `story_series` (one per learner: level, bible,
rolling memory), `story_episodes` (status `queued` → `generating` → `ready` | `failed`, the text, glossary,
questions, choices, validator findings, provider/model/prompt version, the learner's answers and
choice), `vocab_items` (the word bank with SM-2 fields) and `learning_days` (points per Europe/Brussels
day). Routes are in `api/routes_stories.py`: `GET /today`, `POST /today/prepare`, `GET/POST /stories…`,
`GET/POST/DELETE /words…`. The writer runs as the `story_episode` job in the existing job loop. `GET /today` only
reads (`today_view`; a learner without a series yet sees the series to come); opening Today, `POST /today/prepare`
(`ensure_buffer`), queues the first episode and keeps one unread episode ahead, holding back while the reader still
owes a choice (twelve-hour grace), and answers the same plan (`TodayPlan`). The page prepares when it opens, when it
tries again after a failure and from the stalled "Vernieuwen"; its polls and the reloads after an action use the
GET. `docs/STORY_ENGINE.md` describes the prompt, the validator and the cost rules.

Rules that hold throughout: answers to the comprehension questions are graded on the server once per
episode (a retried request id replays the stored result; a new id is refused); points are awarded by
code for actions, never by the model; a learner can only see and act on their own series; the fixture
chat model returns one validated A1 episode so every path is exercised in CI; the real text quality is
judged on the laptop with `python -m dlp.cli write-episode`. The web pages (`/`, `/verhalen`,
`/verhalen/[id]`, `/woorden`) live in `components/TodayHome.tsx`, `StoryLibrary.tsx`,
`EpisodeReader.tsx` and `WordReview.tsx`; the learning path moved to `/leerpad`.

## Activity and points

Every point is earned through `domains/activity/service.record_activity(session, learner_id, kind=..., ref=...,
request_id=..., units=..., counted=..., skill=...)`. It inserts one `activity_events` row (migration `0009`) with ON CONFLICT DO
NOTHING on `(learner_id, kind, dedupe_key)`; only a new row moves `learning_days`, so a retried or
simultaneous request awards nothing and a day's points equal the sum of its events (days from before the
table carry one backfilled `legacy` event). `domains/activity/rules.py` is the one table of kinds: points
per unit, the day counter it moves, its skill, and its scope (`once`, `per_day`, `per_request`, which decide
the dedupe key). The day is the Brussels calendar day (`activity/day.py`); usage allowances keep their UTC
day. `learning_days.goal_target` holds the goal in force at the day's latest activity, and a goal change
updates the current day. An award that takes the day from below its goal to the goal returns
`goal_reached`; action responses carry it, `apiJson` fires `dlp:goal-reached`, and `GoalCelebration` in the
shell says it in a toast and plays the goal tone after the screen's own answer tone, once a day. The crossing
is kept in the event's `meta`, so a retried request answered from its stored result repeats it
(`activity.service.replayed`, today only). `activity_events.request_id` holds up to 80 characters, like the
request bodies. `stories/today.py` keeps the old names as re-exports;
its `add_points` only seeds history in tests. A new kind is a row in the rules table plus a
`record_activity` call where the action is stored, never an update of `learning_days` by hand. Every kind of
practice earns points (D-34): the lesson's and the topic's classic forms (`course_questions` per question,
`course_task` for the open task, per activity and day, refs `lesson:<stage>:<skill>` and `topic:<id>:<skill>`),
the stage check (`stage_check`, `curriculum.service.attempt_points`, never an admin preview), missions
(`mission_questions`, `mission_writing`, `mission_turn`), topic conversations (`conversation_turn`,
`topic_conversations.service.turn_points`; the daily start limit counts the Brussels day, `day_bounds_utc`) and
the warm-up (`speech_warmup`, `POST /speech/transcribe` with `purpose=warmup`). `skill` names the action's own
skill (a typed turn is writing); `counted` moves the day counter by another number than the paid units (story and
historical video awards are retained, but no new video activity is accepted). Awards sit only in the entry functions, after
the paid call and every refusal, and a stored body replayed (a topic's classic answer, a stage check, a turn)
repeats `goal_reached` through `replayed`, never in what is stored.

## Judging an answer

`domains/exercises/compare.py` compares a typed answer with one or more accepted answers and returns
`correct`, `almost` or `incorrect` with notes and a token diff. Case, punctuation, quotation marks and
spacing never matter; missing accents, apostrophes and hyphens are forgiven and noted (`accents`,
`punctuation`). Only a term item has an article policy (`article="optional"` or `"required"`): a missing
article is forgiven or `almost`, a wrong de/het is `almost`; a sentence (`"none"`, the default) compares its
first word like any other. One slip in a word of four letters or more (two from eight) is `almost` unless it
spells another word the caller lists in `lexicon` (library terms are read without article and accents), a
negation (geen/een, niet/net) or a number; a compound typed as two words is a slip. One missing or extra
function word (an article, a preposition, er, wel, ...) in a sentence of four words or more is `almost`; a
missing content word or negation is not. Changed words are paired with their closest counterpart, and among
several accepted answers the closest of the kindest is shown. The thresholds are named constants and
`tests/test_exercise_compare.py` is their specification. `almost` never counts as a mistake.
`domains/speech/compare.py` (`read_aloud_compare`) says which words of a text were recognised; the story reader
and `POST /speech/read-aloud` (any text up to 600 characters, the recording not kept, no points, no score
field, audio seconds counted) share it. Text with no words is refused (`nothing_to_read`) before any audio is
counted.

## Exercise engine

`domains/exercises` runs practice as server-graded sessions (migration `0010`). `POST /exercises/sessions`
(`request_id`, `source` `stage_skill`, `while_you_wait` or `topic`, optional `stage_id` (the profile's level by
default; a topic's own stage), `library_topic`, `size` 5-12, `fresh`, `kinds`, the kinds a client can show,
always with `choice`, and for a topic or lesson `topic_id`, `skill` and `retry`) generates the items once from
a seed (learner, request id,
`GENERATOR_VERSION`) and stores them: `prompt` is what the browser may see, `key` stays on the server and out
of the export (an item's `ref` too, until its answer has been shown). A new session answers 201; the same
request id returns the same session (200), another one resumes an open session of the same kind under 12
hours old (200, `resumed`; only one created with the same `kinds`), `fresh` starts over; the same id with
other parameters is a 409. `POST .../items/{item_id}/report` ("Meld een probleem": `reason` answer_wrong,
unclear, sound or other, an optional `note`) keeps the learner's report in the item's key for the content
review and in their export; a later report replaces it (one request id is one report: the same id with
another reason is a 409), and it changes nothing in the session. Until the review queue lists them (7.9) the
owner reads them with `python -m dlp.cli exercise-reports` (JSON lines: item kind, ref, stage, prompt, answer,
reason, note; never the learner).
`GET /exercises/sessions/{id}`, `POST .../items/{item_id}/answer`, `POST .../items/{item_id}/skip`,
`POST .../items/{item_id}/override` and `POST .../finish` (`early` to stop before the end) complete it; every
write locks the session row, and a repeated request id replays the stored response. An answer takes the shape
of its kind: `{option}`, `{done: true}` (intro card), `{text}` (typed), `{known}` (flashcard), `{pairs}` (left
id to right id), `{bins}` (noun id to de or het) or `{order}` (tile or sentence ids); a board is submitted
whole.

- **Pool** (`pool.py`): per stage, built once per library file. Choice distractors come from the same topic
  first, never the same word or a word with the same meaning in any language, nouns for nouns. A cloze card
  needs the term exactly once in its example and no other form of it there ("offertes"); its distractors are
  siblings of the same article class, never one with the same meaning or one already in the sentence. Siblings
  of a topic often fit the same blank (any colour, any vehicle), so every card shows the sentence's translation
  as its cue; where the translation shows the word itself (also as two words or without its hyphen: "yoga mat",
  "email") the word is practised by choice only.
- **Kinds** (`generators.py`): `choice` (Dutch word to meaning, meaning to Dutch word, from A2 the Dutch
  definition, never one that contains the word; an authored question keeps its options, shuffled),
  `cloze_choice`, `odd_one_out` (pre-A1 to B1: three words of one topic and word class, and one of that class
  from a topic at least ten away and outside the group's theme (`themes.py`), never the word that names the
  topic), and the ungraded `intro` card. `typed.py`: `cloze_typed` (the example's word typed as it stands, the
  translation as cue), `typed_recall` (the meaning; the Dutch word typed, another stage word with the same gloss
  in English and Persian and the same word class right too, a missing article forgiven; never for a word its
  meaning spells, "bed"), both with a hint (first letter, the letters of each word) the screen shows on request, and a word of
  the cue typed back is another word, not a slip; and `flashcard` (self-assessed; for word review).
  `boards.py`: `match_pairs` (four words and their meanings), `de_het` (six nouns without article, three of
  each, up to pre-C1, never a noun that takes both articles: `DOUBLE_ARTICLE`), `sentence_builder` (one
  sentence of the word's example as word tiles, or, when long, four to six chunks cut before conjunctions;
  `sentences.py` takes only sentences that open with their subject, and for tiles no comma, no en/of and no
  movable time word or adverb, since another order would also be right; chunks keep their commas) and
  `sentence_order` (three or four sentences of a Story Time paragraph: pre-B1 and from pre-B2, the other
  stages' paragraphs being too short). Option and piece ids are four random letters, and pieces never read
  solved, on first showing or on a retry. `pool.available()` is the per-stage matrix of what each kind can
  draw on, recorded in `tests/test_exercise_typed_kinds.py`. `audio.py` (step 3.5): `listen_choose` (the word
  is spoken, four written words to choose from; a noun among nouns of its own article where there are three,
  so hearing de or het alone does not answer it), `dictation` (a sentence of the word's example spoken and
  typed, at pre-A1 the word alone; judged like a typed answer; its word count is counted the way answers are
  compared, so "e-mail" is one word) and `shadow` (a sentence shown and spoken, then said after the voice).
  The pool keeps one sentence per word for each (`Pool.dictated`, three to twelve words; `Pool.shadowed`, three
  to ten): no number, no quotation, and no name in a dictation, whose spelling cannot be heard; the counts per
  stage are recorded in `tests/test_exercises_audio.py` (B1's examples are nearly all longer: no shadowing
  there until 7.9). The spoken text stays in the key; `POST .../items/{item_id}/audio` serves it from the speech
  cache (`speech.service.synthesize_cached`: `tts-cache/<provider>/<voice>/<sha256>.wav`, course text only, a
  hit costs no allowance, a miss is an ordinary paid synthesis made once: a second request for the same text
  waits on an advisory lock for the first and then hits the cache; a hit never waits). The lesson, topic and
  final-check listening parts come from the same cache. `POST .../items/{item_id}/recording` (multipart) takes
  a shadowing take: one at a time per item (an advisory lock taken before anything is read, so a retry or a
  second tap waits for the first, then replays it or finds the item answered, without a second transcription),
  transcribed before the session row is locked (the learner's usage counters stay locked during the call), a
  refusal after the transcription returned with its usage kept (`DomainError.persist`, honoured by `_run`), the
  recording not kept; the outcome `heard` (any word recognised, D-23) or `not_heard`, never a score; heard
  speech earns the item's point and counts as right the first time; a take not heard may be tried
  once more at once, not at the end; nothing is a mistake, and a skipped shadowing closes without being listed
  as missed. A miss of a dictated sentence is a mistake (and a word-bank suggestion) for the word only when the
  diff shows the word itself missed or changed; a function word left out elsewhere is not the word's.
- **Blueprint** (`blueprints.py`): up to four new words per session (six in a first session, never more than its
  size), the rest words met before, least recently practised first; the intro card shows the new words the
  session practises, each first recognised; then one kind per word at random (choice counts once, whatever its
  direction; no typing or speaking in a while-you-wait session; speech only while 60 seconds of the audio
  allowance are left); items built on an example (cloze, typed cloze, sentence builder, dictation, shadowing)
  never repeat an example or frame nor show another one's answer; a dictated sentence stands nowhere else in
  the session, not on the intro card nor in any item's word cards or boards (one A1 example serves several
  words), else the dictation becomes another kind for the same word; up to two boards take the place of
  extra new words, else of words met before, and are built from the words the session keeps, so a new word on a
  board is on the intro card; an ordering paragraph shares no sentence with the session's examples; no two
  items about one word in a row where another order allows it.
- **Rules**: two attempts per item; a miss or skip shows the answer and comes back once at the end with its
  options, pieces or sentences reshuffled. A missing accent or a forgiven article is correct with a note;
  `almost` (a slip of the keyboard, a wrong de/het where the article is optional, a missing or extra function
  word, two neighbouring sentences swapped or the closing sentence put first) closes the item and is never a
  mistake. On a typed answer or a built sentence the check
  refused, the learner may say "mijn antwoord klopt ook" (`override`): the item closes as `accepted`, its
  mistake row goes, its point stays, the summary counts it as `overridden` and leaves it out of the missed
  words, and it never counts towards completing a topic or stage. An item earns `exercise_item` (1 point)
  with its first real answer, right or wrong, so an early finish pays wrong answers like right ones; a skip is not an answer, and `no_microphone`/`no_audio` skips
  close an item with speech without counting it as missed (refused on items without speech). Finishing with five answered items earns `exercise_session` (5), and a
  retried finish repeats its points. A first miss on a word met before (an earlier session closed an item about
  it, or it is in the word bank) writes a `learner_mistakes` row in the one taxonomy (`taxonomy.py`), on the word
  the learner chose for odd one out, and one per missed pair or noun of a board; a first encounter writes
  none, and neither does a flashcard (the learner's own say), an ordering (a paragraph they may not have read)
  or a built sentence (another order may be right). The summary lists each missed word, a board's one by one.
  Finishing offers the missed words not in the bank as `word_suggestions`; only the learner saves a word. Each
  attempt keeps the learner's own answer, which the export carries (`given`), with `overridden_at`.
- **Topic and lesson sessions** (step 3.8, `activities.py`, D-31): `source: topic` with a `topic_id` and a
  `skill`, or `source: stage_skill` with `skill` reading or listening for the stage lesson (`stage.lesson`
  only; the final check is never read, `tests/test_exercises_final_check_isolation.py`). Reading or listening:
  a passage step (`read_passage`: the Dutch text and the topic's words; `listen_passage`: the number of parts,
  heard from the topic's or lesson's own `/listening?part=N` route), closed with `{done: true}` (a
  `no_audio` skip closes a listening one) and never graded, then the authored questions in their order as
  `choice` items (options shuffled under opaque ids; the key keeps each option's authored place and the
  question id; a lesson's refs name the stage, `question:<stage>:<id>`, since its ids repeat). The session
  view adds the passage's translation, or the transcript, once every question is closed. At finish the first
  answers go through the unchanged `objective_result` (a first-try skip counts as wrong) and are recorded as
  the classic form records them: `_persist_topic_result` (sticky topic completion, the stage skill) and one
  practice observation (`topic_practice`, request id `exercise:<session id>`, which no client can send), or for
  a lesson `_persist_core_practice` (now returning the sticky value) and no observation. The summary's
  `completion` says what happened: `counted`, or why not (`retry`, `unfinished` when a question was never
  tried, `content_changed` when the topic or lesson changed since the session began, `open_task`), the result,
  whether the activity is completed, and `to_retry`, the questions missed the first time. `retry: true` asks
  only the questions the last finished session on the same activity did not get right first (409
  `nothing_to_retry` when there are none; the session it came from is kept as `retry_of`) and completes
  nothing. A topic's speaking or writing is a warm-up on the topic's own words (`plan(..., only=
  vocabulary_ids)`, boards included, odd one out's odd word excepted; six items, no ordering board); it
  completes nothing, and its typed items are never tagged speaking. Sessions resume only on the same topic,
  skill and retry, never on content changed since they began (such a session is abandoned: it could not
  count) and, for a retry, only while it still answers the last finished session; reading and listening build
  no word pool, so the library's content gate does not hold them back. The passage steps join `intro` in
  `UNGRADED` (no attempt count, point, mistake or progress). Topic lists and details carry `review_of`
  (`topics.review_of`) for the requested skill: the earliest earlier stage's topic whose reading or listening
  text is exactly the same (none for speaking and writing, whose tasks never repeat; a text that only extends
  an earlier one is new). The earlier texts are read from the bank files once per file version and kept as a
  small index, never stored on the topic.
- **Web kit** (step 3.6, `components/exercise`, `/oefenen`): `ExerciseSession` runs a session from start to
  summary through a pure reducer (`sessionReducer.ts`: creating, answering, checking, feedback, finishing,
  summary, error); server responses are events, so a resumed session continues exactly from what the API
  returns. It asks only for the kinds it can draw (`registry.ts`: every kind the engine plans; the flashcard
  is for word review). The answer as it stands is a draft: an option, typed text,
  or a whole board once every part is in place, so "Controleer" sends a board whole and, too early, says
  "Maak eerst alles af". The boards need no dragging: match pairs (choose a word, then its meaning; a pair shows
  one number on both sides, and every button's name says what it is paired with), de/het (a pair of native
  radios per noun, drawn as a switch), the sentence builder (choose the pieces in order, choose one in the
  sentence to put it back; focus moves to the piece now in its place) and the ordering (up and down buttons per
  sentence; focus stays on the button that moved it). Answered, each board shows every part's result (with an
  icon and words, not colour alone), the right meaning, article, sentence or order (with its translation, and
  where each misplaced sentence stood; an "almost" swap stays neutral), and is read-only; skipped, it shows the
  answers alone. A renderer is keyed per asking and per verdict, so a question that comes straight back starts
  again from the server's reshuffled prompt. Typed answers (typed cloze, typed recall, dictation) go in a Dutch
  field the device leaves alone (`lang=nl`, autocapitalize, autocorrect, spellcheck and autocomplete off);
  Enter checks; a hint (first letter and the letters of each word; an answer of several words is asked for as
  words) is there on request, read out, with focus back in the field, and reported with that item's answer only
  (`hint_used`); answered, the field shows the typed text, a word-by-word comparison with the answer
  (`TokenDiff`: missing, extra and changed words in words and marks, never a score; only a miss is drawn in the
  miss colours, "almost" and an overruled answer are neutral) and what the comparison forgave or found (its
  notes in words); on a typed answer or a built sentence the check did not accept, "Mijn antwoord klopt ook"
  overrules it (`OVERRIDDEN`: the item closes as accepted, the answer's point stays on screen, focus moves to
  "Verder", and the check's answer is shown as what it expected). "Verder" also reads out the item's own
  verdict (the comparison, what was heard). The sound of an item
  (listen-and-choose, dictation, shadowing) comes from its audio route through `ItemAudio` (one sound at a
  time across the app, kept for the tab, silenced by a recording; a development test tone says so), and "Ik kan
  nu niet luisteren" closes such an item without a miss. Shadowing records with one press and stops with
  another (no holding down; the instruction is given before the take and nothing is announced while the
  microphone listens), sends the recording (never kept) and shows heard or not heard and the words heard, never
  a score; "Ik kan nu niet spreken" closes it without a miss; a take not heard may be tried again at once; a
  browser that cannot record is not given shadowing. The create request id is
  minted once, so a repeated effect or a retry replays; an
  answer that did not arrive is sent again under the same id when it is the same answer, and under a new one
  when the learner changed it; a 409 (already answered, session closed) on an answer or the finish reloads the
  session; "Nog een oefening" resets the runner first. Options are the
  `AnswerOption` primitive (`components/ui`, `styles/ui/answer-option.css`): a native radio in its label in a
  fieldset; `data-state` default, selected, correct, incorrect (soft, shaken once unless motion is reduced),
  reveal (dashed) or idle, always with an icon and words. Dutch options show no gloss before the answer
  (guessability); their meanings appear with the verdict. While focus is in the item, keys 1 to 4 choose (the
  number row's key on any layout, Persian digits too) and move focus to the option, and Enter checks; Escape
  asks to stop ("rond nu af" finishes early; the session also stays open for 12 hours) unless another dialog is
  open; focus moves to each question (a missed one that comes straight back too) and then to "Verder", which
  is described by the correction, and returns to the opener when a dialog closes; a polite live region says
  the outcome; tones play only after the verdict and never for a miss. The
  feedback bar shows the outcome ("Nog niet" for a miss, never red), the point, whether the item comes back,
  and the word card; "Meld een probleem" opens the report. The summary shows what was done (answered, right
  first time, right the second time, points, the session bonus), the missed words (once each) and the
  word-bank suggestions to save, as library words with their example. `/oefenen` is a focus mode of the shell (no sidebar or tabs); `?bron=wachten` is the
  short tap-only session that Today offers under a pending episode. The target for an answer round trip is a
  p95 at or under 300 ms: `tests/e2e/exercises.spec.ts` checks it through the proxy with Playwright's request
  timing, `scripts/verify_live.py --measure-answers` on Azure with the script's wall-clock time over one
  kept-alive connection, and the browser records each one as a `performance.measure` named
  `exercise-answer` (`lib/client/round-trips.ts`) for DevTools.
- **Topic sessions in the web** (step 3.9, `SkillTopicPractice`, D-32): a topic opens on a start card (what
  happens, the review label when its text repeats an earlier stage's, whether it already counts); reading and
  listening then run `ExerciseSession` embedded (`source: topic`, `headingLevel` 4 under the topic's h3, no page
  title or second honesty chip, Escape only within the session, the host's way out instead of the links to
  Today, `onActivityChange` while a recording runs or the session is closed, `onFinished` with the summary). The
  request body comes from the pure `sessionRequest` (a page's session still sends `{source, kinds}` only). The
  passage (`PassagePanel`) is one panel from its own step through every question (the text or the
  `CurriculumAudio` player over the topic's `/listening` route stays the same node); after finishing, one
  read of the session brings its translation or transcript (`REVEALED`), shown on request in the summary. The
  summary says what the session did for the topic from `summary.completion` (`completion.ts`: done in the
  success colours, otherwise neutral, never a miss colour) and offers the missed questions first when there
  are some (`retry: true`; a 409 `nothing_to_retry` offers all the questions again). Speaking and writing
  offer a warm-up on the topic's words or "Ga meteen naar de opdracht"; the task is the open task as before,
  under "Jouw opdracht"; a link from the coach, a conversation and a writing draft already begun open the task
  directly. Only what the server counted moves the topic on (`onCompleted` refetches the stage). The classic
  receptive form left the page; its endpoint stays for the API and its tests. `CurriculumQuestions` shows an
  option's gloss only once answers are checked (never in the final check), as the session does.
- **Content gate**: a stage takes sessions only when 200 of its words support a four-option choice, its examples
  hold 150 distinct sentences and it supports two kinds with at least 50 items each (`VARIETY_MIN_*`,
  `KIND_MIN_ITEMS` in `pool.py`). `tests/test_exercise_generators.py` records each stage's numbers, with its
  sentence frames and how many of its words are new against the earlier stages, and checks 200 seeded sessions
  per stage (sizes 5 to 12, topic sessions included) against the rules above. A stage below the gate answers
  409 `not_ready`. Reused word lists pass the gate and are labelled as review (roadmap 3.9).
