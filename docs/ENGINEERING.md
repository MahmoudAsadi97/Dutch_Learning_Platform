# Engineering guide

This is the collaborator-facing description of release 0.1. It is deliberately short: the
code is the reference, this explains why it is shaped the way it is.

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

## 7. Usage counters and jobs

`usage/service.py` reserves before every external call (`reserve` → `commit`/`release`), per
metric (`model_calls`, `tokens`, `audio_seconds`), per scope (`daily`, `total`), with the limit
enforced inside the SQL `UPDATE` so concurrent requests cannot overshoot; the same request id
returns the existing reservation. The pricing table stays empty until Phase B.

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
- Deployment: Phase B only. Bicep, the OIDC workflow, `docs/GO_LIVE.md` and `scripts/verify_live.py` are M3 deliverables.

## 9. Configuration contract

Every variable lives in `.env.example` with a comment. Secrets: `ASSERTION_SIGNING_KEY`,
`DATABASE_URL` (Phase B), `AZURE_CHAT_API_KEY`, `AZURE_SPEECH_KEY`,
`AZURE_STORAGE_CONNECTION_STRING` (the published Azurite string is not a secret). The web tier
reads `APP_ENV`, `DEV_AUTH_ENABLED`, `DEV_OWNER_EMAIL`, `DEV_OWNER_NAME`, `API_INTERNAL_URL` and the
`ASSERTION_*` variables; the API reads the rest. `scripts/run.py` passes the root `.env` to both.
