# Validation report

Session 1, 2026-09-17. Everything below ran in the Linux build workspace (PostgreSQL 16.13,
Azurite 3.37 via npm, ffmpeg 6, headless Chromium 1194 with a fake microphone, Python 3.11, Node 22).
Nothing has run on the owner's laptop yet.

## Status vocabulary

| Status | Meaning |
|---|---|
| `implemented_local` | code exists; exercised with fixtures only |
| `verified_workspace` | works end to end with real local components **in the build workspace** (not the owner's laptop) |
| `verified_local` | works end to end with the local providers in the desktop browser on the owner's laptop |
| `integration_pending` | Azure adapter written and unit-tested against recorded fixtures; no credentials yet |
| `verified_live` | proven against Azure in Phase B |
| `review_pending` | awaiting the human language reviewer |
| `not_started` | declared, not written |

## M1 items

| Item | Status | Evidence |
|---|---|---|
| Docker Compose (PostgreSQL, Azurite) | `implemented_local` | file present; not started here (no Docker daemon in the workspace); the same PostgreSQL 16 and Azurite versions were run natively instead |
| Alembic migration `0001` | `verified_workspace` | `alembic upgrade head` on `dlp` and `dlp_test`; 13 tables; used by every database test |
| Mission schemas + fixture + A01 | `verified_workspace` | `python -m dlp.cli load-fixture` (297/300 words, 69 texts all unreviewed); `python -m dlp.cli acceptance --check A01` → 12/12 PASS; `tests/test_content.py` (10 rejection cases) |
| Fixture identity → proxy → assertion → API | `verified_workspace` | `tests/e2e/proxy.spec.ts` (4 tests) and curl: 401 without assertion, 403 without anti-CSRF header, 403 cross-site origin, 403 non-localhost `Host`, forged `Authorization`/`X-MS-CLIENT-PRINCIPAL-ID` ignored; `tests/test_identity.py` (10 tests: expiry, audience, key, allowlist, alg=none, lifetime, production refusal) |
| Ollama chat client (`OpenAICompatibleChatModel`) | `implemented_local` | `tests/test_chat_client.py` against a mock OpenAI-compatible transport: schema validation, repair round, 429 retry, bounded attempts, Azure URL and `api-key` header. **Ollama itself could not be reached from the workspace** (registry blocked); preflight reports `unreachable` honestly |
| faster-whisper provider | `implemented_local` | package installs and imports (1.2.1); `available()` reports correctly; model download is blocked in the workspace (Hugging Face 403) → `ProviderUnavailable` with a clear message. Real transcription: OWNER_ACTIONS 3 |
| Piper provider | `implemented_local` | package installs (piper-tts 1.8.0); voice files absent here; `available()` says so. Real synthesis: OWNER_ACTIONS 3 |
| Azurite blob store (Azure SDK) | `verified_workspace` | `tests/test_blob_store.py::test_azurite_round_trip_through_the_azure_sdk` (put/get/exists/delete against a running Azurite); preflight `blob store azurite ok` |
| Audio canonicalisation (ffprobe/ffmpeg, bounds) | `verified_workspace` | `tests/test_audio.py`: WebM/Opus 48 kHz stereo → WAV 16 kHz mono PCM; too-long → 413; non-audio → 400; timeout → 422 |
| Microphone → upload → ffmpeg → transcription → playback | `verified_workspace` (fixture transcriber) | `tests/e2e/speech.spec.ts`: Chromium fake microphone plays a WAV, MediaRecorder (`audio/webm;codecs=opus`) → `/api/speech/transcribe` → canonical 16 kHz → fixture transcript shown; `/api/speech/synthesize` → `X-Audio-Label: synthetic-development`, playable blob. `tests/test_speech_api.py` (7 tests incl. failure injection releasing the reservation and the 429 daily limit) |
| Lesson shell, reading step | `verified_workspace` | `tests/e2e/lesson.spec.ts` at 1440, 768 and 390 px: text, labels, Persian toggle (`dir=rtl`), help ladder rungs, 2/2 questions, four skill records, session start; screenshots inspected (single column at 390 px, no horizontal scroll) |
| Usage counters | `verified_workspace` | `tests/test_usage.py`: reserve/commit/release, refusal leaves no trace, deduplication, 20 concurrent threads → exactly 12 of 20 reservations succeed within a 120 s budget; `/usage` shows the empty pricing table |
| Durable job loop | `verified_workspace` | `tests/test_jobs.py`: idempotent enqueue, run to completion, retry with backoff then succeed, dead after `max_attempts`, expired lease recovered by another worker |
| Appointment action validation (code-authoritative) | `verified_workspace` | `tests/test_actions.py`: invented slots refused, confirm needs an accepted slot, only offered slots acceptable, cancel ends the flow, state round-trips |
| Language-benchmark harness (40 cases) | `verified_workspace` (plumbing only) | `--provider expected` → 40/40, `--provider wrong` → 0/40; results tagged with provider, model, prompt version, commit. **Not a model selection** |
| Preflight (no secrets) | `verified_workspace` | `python -m dlp.cli preflight`; `GET /health/preflight`; `test_preflight_endpoint_never_exposes_secrets` |
| Azure chat configuration | `implemented_local` | same client class; URL/header shape unit-tested; no credentials |
| Azure speech adapters | `not_started` | declared in `providers/speech_azure.py`, scheduled for M3 |
| Web lint / type-check, API lint | pass | `npm run lint`, `npm run typecheck`, `ruff check src tests` |

## Test runs (final, this session)

- API: `pytest` → 78 passed, 1 skipped (the Azurite test skips when Azurite is down; it passed with Azurite running).
- Browser: `python scripts/run.py e2e` → 18 passed (desktop 10, tablet 4, phone-width 4).
- Benchmark dry runs: 40/40 and 0/40.

## Known gaps and honest limits

1. No run on the owner's laptop yet: every `verified_workspace` item needs the owner's run (OWNER_ACTIONS 2–3) before it may be called `verified_local`.
2. Real speech providers were not exercised end to end anywhere: Ollama, the whisper model and the Piper voice could not be downloaded in the workspace.
3. `tone_1s.wav` and `speech-input.wav` are generated tones, not speech. A real recorded sentence is OWNER_ACTIONS 4.
4. The CI workflow is written but its first run on GitHub has not been observed from here.
5. `PRODUCT_BRIEF.md` / `LEARNER_PROFILE.md` were unavailable; content and A01 are provisional (D-01).
6. Docker Compose was not executed in the workspace (no daemon); the same services ran natively.
