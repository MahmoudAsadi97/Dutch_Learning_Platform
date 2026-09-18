# Validation report

Session 1 (2026-09-17) ran in the Linux build workspace (PostgreSQL 16.13, Azurite 3.37 via npm,
ffmpeg 6, headless Chromium 1194 with a fake microphone, Python 3.11, Node 22). Session 2
(2026-09-18) repeated the checks on the owner's laptop (Windows 11, WSL 2 Ubuntu 22.04, conda env
`dlp` with Python 3.11 / Node 22 / conda-forge ffmpeg, Docker Desktop with PostgreSQL 16.15 and
Azurite, Ollama with `llama3.1:8b`, faster-whisper `small`, Piper `nl_BE-nathalie-medium`, Windows
browser against `http://localhost:3000`).

## Owner laptop run, 2026-09-18 (evidence for `verified_local`)

| Check | Result |
|---|---|
| `python scripts/run.py preflight` | all ten rows `ok`: PostgreSQL 16.15, ffmpeg/ffprobe (conda), Ollama reachable with the configured model found, faster-whisper `small` on cpu/int8, Piper voice present, Azurite container reachable, job loop configured |
| Migrations, fixture, A01 | `alembic upgrade head` → 0001; fixture loaded (297 Dutch words, 5 steps); A01 exercised by the API suite |
| `python scripts/run.py test` | first run 73 passed / 6 failed, all six being `ffmpeg` refusing to start under the 512 MB address-space cap with the conda-forge build (fixed: cap 2048, single-threaded conversion, stderr logged); re-run after the fix: **80 passed in 13.06 s** (including the Gate 1 test) |
| `python scripts/run.py e2e` | **18 passed** in headless Chromium on the laptop (desktop, tablet, phone widths; fixed fixture identity; test database) |
| Microphone check, real providers, Windows browser | MediaRecorder `audio/webm;codecs=opus` → upload (matroska/opus, 48 kHz, 2 channels) → canonical WAV (pcm_s16le, 16 kHz, 1 channel, 7.35 s) → `local-faster-whisper · small · 4088 ms` → a correct transcript of a two-clause Dutch sentence; API log shows the whisper model download on first use and the VAD filter working |
| Synthetic playback | `POST /speech/synthesize` 200 in 3.8 s → 3 s WAV from `local-piper` played in the browser with the `synthetic-development` label |
| Status panel | first `/api/health/preflight` took 20 s (Next.js dev compile on `/mnt/c`), then 200; panel now shows a hint after 8 s and times out at 45 s with a retry |
| Findings fixed during the run | Docker WSL integration off (owner setting); ROS 2 `python3.10` entries on `PYTHONPATH` broke pytest (runner now strips foreign interpreters); `sudo npx` picked an old Node (documented `sudo env "PATH=$PATH"`); ffmpeg address-space cap; browser tests depended on the developer `.env` (now isolated); `next start` with standalone output (now opt-in); unhandled media-load abort on the microphone page (handled) |

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
| Docker Compose (PostgreSQL, Azurite) | `verified_local` | laptop: `python scripts/run.py services` started `dlp-postgres` (16.15) and `dlp-azurite`; the workspace ran the same services natively |
| Alembic migration `0001` | `verified_local` | workspace: `alembic upgrade head` on `dlp` and `dlp_test`, 13 tables; laptop: applied to the Docker PostgreSQL 16.15 |
| Mission schemas + fixture + A01 | `verified_local` | `python -m dlp.cli load-fixture` (297/300 words, 69 texts all unreviewed); `python -m dlp.cli acceptance --check A01` → 12/12 PASS; `tests/test_content.py` (10 rejection cases) |
| Fixture identity → proxy → assertion → API | `verified_local` | `tests/e2e/proxy.spec.ts` (4 tests) and curl: 401 without assertion, 403 without anti-CSRF header, 403 cross-site origin, 403 non-localhost `Host`, forged `Authorization`/`X-MS-CLIENT-PRINCIPAL-ID` ignored; `tests/test_identity.py` (10 tests: expiry, audience, key, allowlist, alg=none, lifetime, production refusal) |
| Ollama chat client (`OpenAICompatibleChatModel`) | `implemented_local` | `tests/test_chat_client.py` against a mock OpenAI-compatible transport: schema validation, repair round, 429 retry, bounded attempts, Azure URL and `api-key` header. Laptop preflight reaches Ollama and finds `llama3.1:8b`; no feature in M1 makes a real completion yet (`benchmarks/language/harness.py --provider local` is the first real call; M2 uses it in the turn loop) |
| faster-whisper provider | `verified_local` | laptop: real Dutch speech transcribed correctly (`small`, cpu/int8, 4.1 s for a 7.35 s clip); workspace: package imports, model download blocked there → `ProviderUnavailable` with a clear message |
| Piper provider | `verified_local` | laptop: `nl_BE-nathalie-medium` synthesised and played with the `synthetic-development` label; workspace: package imports, voice absent there |
| Azurite blob store (Azure SDK) | `verified_local` | `tests/test_blob_store.py::test_azurite_round_trip_through_the_azure_sdk` (put/get/exists/delete against a running Azurite); preflight `blob store azurite ok` |
| Audio canonicalisation (ffprobe/ffmpeg, bounds) | `verified_local` | `tests/test_audio.py`: WebM/Opus 48 kHz stereo → WAV 16 kHz mono PCM; too-long → 413; non-audio → 400; timeout → 422 |
| Microphone → upload → ffmpeg → transcription → playback | `verified_local` | `tests/e2e/speech.spec.ts`: Chromium fake microphone plays a WAV, MediaRecorder (`audio/webm;codecs=opus`) → `/api/speech/transcribe` → canonical 16 kHz → fixture transcript shown; `/api/speech/synthesize` → `X-Audio-Label: synthetic-development`, playable blob. `tests/test_speech_api.py` (7 tests incl. failure injection releasing the reservation and the 429 daily limit) |
| Lesson shell, reading step | `verified_local` (browser tests on the laptop; owner's manual click-through is part of the Gate 1 review) | `tests/e2e/lesson.spec.ts` at 1440, 768 and 390 px: text, labels, Persian toggle (`dir=rtl`), help ladder rungs, 2/2 questions, four skill records, session start; screenshots inspected (single column at 390 px, no horizontal scroll) |
| Usage counters | `verified_local` | `tests/test_usage.py`: reserve/commit/release, refusal leaves no trace, deduplication, 20 concurrent threads → exactly 12 of 20 reservations succeed within a 120 s budget; `/usage` shows the empty pricing table |
| Durable job loop | `verified_local` | `tests/test_jobs.py`: idempotent enqueue, run to completion, retry with backoff then succeed, dead after `max_attempts`, expired lease recovered by another worker |
| Appointment action validation (code-authoritative) | `verified_local` | `tests/test_actions.py`: invented slots refused, confirm needs an accepted slot, only offered slots acceptable, cancel ends the flow, state round-trips |
| Language-benchmark harness (40 cases) | `verified_local` (plumbing only) | `--provider expected` → 40/40, `--provider wrong` → 0/40; results tagged with provider, model, prompt version, commit. **Not a model selection** |
| Preflight (no secrets) | `verified_local` | `python -m dlp.cli preflight`; `GET /health/preflight`; `test_preflight_endpoint_never_exposes_secrets` |
| Azure chat configuration | `implemented_local` | same client class; URL/header shape unit-tested; no credentials |
| Azure speech adapters | `not_started` | declared in `providers/speech_azure.py`, scheduled for M3 |
| Web lint / type-check, API lint | pass | `npm run lint`, `npm run typecheck`, `ruff check src tests` |

## Test runs (final)

- API, laptop: `pytest` → 80 passed. Workspace: 79 passed (80 with the Gate 1 test), the Azurite test skipping when Azurite is down.
- Browser: `python scripts/run.py e2e` → 18 passed (desktop 10, tablet 4, phone-width 4).
- Benchmark dry runs: 40/40 and 0/40.

## Known gaps and honest limits

1. Docker Compose itself was only exercised on the laptop (`services` started `dlp-postgres` and `dlp-azurite`); the build workspace ran the same services natively.
2. No real chat completion against Ollama has run yet; the client is unit-tested against a mock and Ollama is reachable. `benchmarks/language/harness.py --provider local` is the cheapest real exercise.
3. `tone_1s.wav` and `speech-input.wav` are generated tones, not speech. `python -m dlp.cli export-recording <request id>` turns a laptop recording into `tests/fixtures/dutch_sentence.wav` (OWNER_ACTIONS 4); the recording made on 2026-09-18 contains personal data, so a neutral sentence is recommended for the committed fixture.
4. The CI workflow is written but its first run on GitHub has not been observed from here.
5. `PRODUCT_BRIEF.md` / `LEARNER_PROFILE.md` were unavailable; content and A01 are provisional (D-01).
6. The source duration of a MediaRecorder WebM upload reads 0.00 s (the container carries no duration); the canonical WAV's duration is what bounds and usage use. Showing "unknown" instead of 0.00 s is an M3 polish item.
7. In development mode the first request to a route takes 10–20 s on `/mnt/c` (Next.js compiles on demand); production builds do not have this.
