# Verification

What has been checked, where, and with which status. Nothing here claims more than the environment it
ran in.

## Status vocabulary

| Status | Meaning |
|---|---|
| `verified_local` | exercised end to end with the real local providers (Ollama, faster-whisper, Piper, Azurite) in a browser on the development laptop |
| `verified_ci` | exercised end to end in the automated suites with fixture providers (PostgreSQL 16, ffmpeg, headless Chromium with a fake microphone) |
| `verified_live` | exercised against the production deployment in Azure (resource group `dlp-production`, West Europe) while signed in as the owner |
| `integration_pending` | adapter written and unit-tested against recorded fixtures; no live use recorded yet |
| `review_pending` | content or behaviour that needs a human Belgian Dutch reviewer |

## Automated suites

| Suite | Command | Size | Last run |
|---|---|---|---|
| API | `python scripts/run.py test` | 514 tests, 1 skipped (Azurite round-trip needs the emulator) | 2 October 2026, green |
| Web unit | `cd apps/web && npm run test:unit` | 27 tests | 2 October 2026, green |
| Browser | `python scripts/run.py e2e` | 96 checks across desktop, tablet and phone-width projects, including axe accessibility scans | 2 October 2026, green |
| Lint and types | `make lint` | ruff, eslint, tsc | 2 October 2026, clean |
| Benchmark plumbing | `python scripts/run.py benchmark` | 40 cases; `expected` 40/40, `wrong` 0/40 | CI |

CI (`.github/workflows/ci.yml`) runs the Bicep build, both Docker images, the API suite against a
PostgreSQL service, the benchmark dry runs and the browser suite on every push to `main`.

## Verified on the laptop with the real providers

| Date | What |
|---|---|
| 18 September 2026 | Docker services, migrations, mission fixture and A01; microphone → upload → ffmpeg → faster-whisper (`small`, 4.1 s for a 7.35 s clip of real Dutch); Piper `nl_BE-nathalie-medium` playback labelled synthetic; the reading step in the browser at 1440, 768 and 390 px |
| 22 September 2026 | The full appointment mission with Ollama `llama3.1:8b`, faster-whisper `medium`, Piper and Azurite: reading (2/2, help rungs recorded), listening (clip synthesised on first play), writing (autosave, submission as typed evidence, grounded feedback), typed conversation turns. The run exposed a reply that announced a booking the code had not made; the reply guard, the slot acceptance rule and the feedback citation resolver were fixed and tested the same day |

Not yet run with the real providers: spoken conversation turns and the checkpoint.

## Verified live in Azure

| Date | What |
|---|---|
| 2 October 2026 | Release `a6833ee` through `scripts/deploy_current.sh` (ACR builds, migration job, revision health); `verify_live.py` anonymous scope PASS (liveness, sign-in wall on page and API, anonymous state change refused). Signed in: production configuration on the settings page; three episodes written by `gpt-4.1-mini` (the first failed on sentence length, the next two passed with under-length warnings — the profiles and the rewrite feedback were tuned from exactly these); reading, grading, saving a word, the choice, points and streak; a word review cycle (`haak`, interval one day); synthesis of a paragraph by `nl-BE-DenaNeural` (130 KB WAV in 0.8 s) sent back through read-aloud and recognised 8/8 words; a typed lunch-order turn (`gpt-4.1-mini`, 0.9 s), which exposed the "direct order" refusal fixed as D-21 |

## By feature

| Feature | Status | Evidence |
|---|---|---|
| Fixture identity → proxy → assertion → API; CSRF; allowlist | `verified_ci` | `tests/test_identity.py`, `tests/e2e/proxy.spec.ts` |
| Usage counters (atomic reserve/commit/release, concurrency) | `verified_ci` | `tests/test_usage.py` (20 threads, exactly 12 of 20 succeed within the budget) |
| Durable job loop (leases, backoff, recovery) | `verified_ci` | `tests/test_jobs.py` |
| Audio canonicalisation and bounds | `verified_ci` + `verified_local` | `tests/test_audio.py`; laptop runs |
| Appointment scenario (code-authoritative slots) | `verified_ci` + `verified_local` | `tests/test_actions.py`, `tests/test_turns.py`; 22 September run |
| Evidence, feedback grounding, export | `verified_ci` | `tests/test_writing_feedback.py`, `tests/test_practice_api.py` |
| Curriculum: practice, final checks, topic practice, library | `verified_ci` + `verified_local` (reading/listening/writing) | `tests/test_curriculum.py`, `tests/test_topics.py`, `tests/test_library.py`; browser specs |
| Guided conversations, coach, editing queue | `verified_ci` | `tests/test_topic_conversations.py`, `tests/test_coaching.py`, `tests/test_content_review.py` |
| Story serial: queueing, validation, rewrite, failure modes, answers, choices, isolation | `verified_ci` + `verified_live` | `tests/test_stories.py` (27 tests), `tests/e2e/stories.spec.ts` (6 checks); 2 October live run |
| Word bank and SM-2, streak and daily goal | `verified_ci` + `verified_live` | `tests/test_stories.py`; 2 October live run |
| Read-aloud word comparison | `verified_ci` + `verified_live` | `tests/test_stories.py::test_read_aloud_compares_words_without_inventing_a_score`; 2 October round trip |
| Service conversations (direct order, reason first, phase lines) | `verified_ci` + `verified_live` (one typed turn) | `tests/test_service_missions.py`; 2 October live turn |
| Video lessons: script gate, twenty-second minimum, seconds budget, render jobs, subtitles from the file, byte-range playback, points | `verified_ci` (fixture renderer; the Azure avatar adapter against recorded replies) | `tests/test_videos.py` (16 tests), `tests/e2e/videos.spec.ts` (4 checks) |
| Azure avatar render | `integration_pending` | not yet rendered live |
| Azure chat, speech and blob adapters | `verified_live` (chat, synthesis, recognition, blob writes) | `tests/test_speech_azure.py`, `tests/test_azure_config.py`, `tests/test_blob_store.py`; preflight shows the last live use per adapter (`tests/test_preflight.py`) |
| Bicep, release script, `scripts/verify_live.py` | `verified_live` (anonymous scope); authenticated scope not run | `az bicep build` in CI; 2 October release |
| All fixed Dutch content; generated episodes | `review_pending` | labels in the interface |
| Phone acceptance | not started | — |

## Known gaps

1. The fixture chat model follows keyword rules, so the browser tests show that whatever the model
   proposes is validated in code; they cannot show how `llama3.1:8b` phrases a reply or writes an
   episode.
2. `tone_1s.wav` and `speech-input.wav` are generated tones, not speech; no real recording is committed.
3. In development mode the first request to a route takes 10–20 s on `/mnt/c` (Next.js compiles on
   demand); production builds do not have this.
4. A MediaRecorder WebM upload reports a source duration of 0.00 s (the container carries no duration);
   the canonical WAV's duration is what bounds and usage use.
5. `.env.example` used to put comments after empty values (`KEY= # note`); pydantic read the comment as
   the value, so `LOCAL_CHAT_MODEL_STRONG` and `CURRICULUM_ADMIN_EMAILS` could silently be wrong. Fixed
   on 2 October 2026; check an older `.env` for the same pattern.
