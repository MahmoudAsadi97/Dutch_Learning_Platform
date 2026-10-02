# Verification

What has been checked, where, and with which status. Nothing here claims more than the environment it
ran in.

## Status vocabulary

| Status | Meaning |
|---|---|
| `verified_local` | exercised end to end with the real local providers (Ollama, faster-whisper, Piper, Azurite) in a browser on the development laptop |
| `verified_ci` | exercised end to end in the automated suites with fixture providers (PostgreSQL 16, ffmpeg, headless Chromium with a fake microphone) |
| `integration_pending` | adapter written and unit-tested against recorded fixtures; never run against the cloud service |
| `review_pending` | content or behaviour that needs a human Belgian Dutch reviewer |

## Automated suites

| Suite | Command | Size | Last run |
|---|---|---|---|
| API | `python scripts/run.py test` | 484 tests, 1 skipped (Azurite round-trip needs the emulator) | 2 October 2026, green |
| Web unit | `cd apps/web && npm run test:unit` | 27 tests | 2 October 2026, green |
| Browser | `python scripts/run.py e2e` | 91 checks across desktop, tablet and phone-width projects, including axe accessibility scans | 2 October 2026, green |
| Lint and types | `make lint` | ruff, eslint, tsc | 2 October 2026, clean |
| Benchmark plumbing | `python scripts/run.py benchmark` | 40 cases; `expected` 40/40, `wrong` 0/40 | CI |

CI (`.github/workflows/ci.yml`) runs the Bicep build, both Docker images, the API suite against a
PostgreSQL service, the benchmark dry runs and the browser suite on every push to `main`.

## Verified on the laptop with the real providers

| Date | What |
|---|---|
| 18 September 2026 | Docker services, migrations, mission fixture and A01; microphone → upload → ffmpeg → faster-whisper (`small`, 4.1 s for a 7.35 s clip of real Dutch); Piper `nl_BE-nathalie-medium` playback labelled synthetic; the reading step in the browser at 1440, 768 and 390 px |
| 22 September 2026 | The full appointment mission with Ollama `llama3.1:8b`, faster-whisper `medium`, Piper and Azurite: reading (2/2, help rungs recorded), listening (clip synthesised on first play), writing (autosave, submission as typed evidence, grounded feedback), typed conversation turns. The run exposed a reply that announced a booking the code had not made; the reply guard, the slot acceptance rule and the feedback citation resolver were fixed and tested the same day |

Not yet run with the real providers: spoken conversation turns and the checkpoint on the laptop, and
the story serial (the engine is `verified_ci`; its first laptop episodes are the next step in
`docs/STATUS.md`).

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
| Story serial: queueing, validation, rewrite, failure modes, answers, choices, isolation | `verified_ci` | `tests/test_stories.py` (26 tests), `tests/e2e/stories.spec.ts` (6 checks) |
| Word bank and SM-2, streak and daily goal | `verified_ci` | `tests/test_stories.py` |
| Read-aloud word comparison | `verified_ci` | `tests/test_stories.py::test_read_aloud_compares_words_without_inventing_a_score` |
| Azure chat, speech and blob adapters | `integration_pending` | `tests/test_speech_azure.py`, `tests/test_azure_config.py`, `tests/test_blob_store.py` |
| Bicep, release workflow, `scripts/verify_live.py` | `integration_pending` | `az bicep build` in CI; nothing deployed |
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
