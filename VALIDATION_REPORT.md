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

## Owner laptop, first M2 run, 2026-09-18 (evening)

| Check | Result |
|---|---|
| `python scripts/run.py dev` after the pull | preflight: everything `ok` except **chat model unreachable** (Ollama was not running in WSL) — the conversation cannot start without it; whisper `small` on cpu/int8 and Piper present |
| Microphone page | transcription 18.4 s on the first call (model load), 2.2 s on the next; synthesis 1.6 s |
| Whisper `small` vs `medium`, same sentence (*Sorry, ik moet werken vandaag. Tot volgende.*), same speaker | `small`: 7.2 s of speech → 1.9 s, one word wrong (*wendig* for *vandaag*). `medium`: 5.6 s → 5.1 s, **transcript fully correct** (the owner confirmed the sentence ends with *volgende*; an earlier reading of it as a dropped word was wrong). The owner's laptop runs `medium` (`LOCAL_STT_MODEL=medium` in his `.env`); about 1 s of recognition per second of speech on this CPU. The recorder keeps a 400 ms tail after the button is released as a general precaution, not as a fix for this sentence |
| Finding | a media-load `AbortError` surfaced once in the dev overlay while playing synthesis a second time; playback now runs each clip on its own `Audio` object whose `play()` promise is always observed (`lib/client/playback.ts`) |
| Reading step with real providers (later that evening) | answers judged and recorded (2/2), all help rungs recorded (11 evidence items). **Feedback failed**: `llama3.1:8b` produced 600 output tokens three times and was cut off each time (`finish_reason=length`, ~12 s per attempt, 104 s in total) — Persian text costs several tokens per word and the cap was 600. Fixed: a truncated reply is retried with double the budget instead of a repair round, feedback gets its own budget (`FEEDBACK_MAX_OUTPUT_TOKENS=1000`), the prompt asks for at most three short points and the evidence list is capped |

## Owner laptop, full loop with the real providers, 2026-09-22

Run by the build through the desktop app's browser on the owner's laptop (`python scripts/run.py dev`;
preflight all `ok`: PostgreSQL 16.15, Ollama `llama3.1:8b`, faster-whisper `medium`, Piper
`nl_BE-nathalie-medium`, Azurite). The spoken turns and the checkpoint were not exercised (microphone).

| Step | Result |
|---|---|
| Reading | answers judged by the API, 2/2, help rungs recorded; **feedback**: Dutch and Persian summaries arrived in ~25 s, all three points dropped — the model's citations did not resolve (see the fix below) |
| Listening | Piper clip synthesised on first play and labelled `synthetic-development`; 1/1 judged; feedback: one point with a valid citation and a matching quote, no Persian summary that time |
| Writing | autosave shown (`bewaard 14:36`), 32 words, required words found, submitted as typed evidence, `Schrijven: practised`; feedback: two grounded points (one mislabelled *fout* for a help-use observation), one dropped, Persian present |
| Speaking, typed turns | turn 1 *Ik moet dan werken* → `state_reason` accepted, model reply offering only real slots, 3.1 s. Turn 2 *Donderdag om tien uur is goed voor mij* → the model labelled it `propose_slot`, the code recorded no acceptance, and the model reply announced *Uw afspraak is dan verzet naar donderdag om tien uur. Ik zie u dan morgen* — a booking the code had not made, plus an invented *morgen*. Turn 3 *Ja, dat is goed. Tot dan!* → `confirm` refused (nothing accepted) while the reply closed with *Tot dan! Tot donderdag om tien uur dan.* |

Fixes from this run (all with tests): naming one of the available moments now takes it as chosen with
confirmation pending, whatever label the model chose (`apply_action`); the reply guard also catches
closings and rescheduling phrases (*verzet naar*, *tot dan*, *zie u dan*) before the code accepted or
confirmed; the prompts carry today's date and forbid *morgen* and closings before confirmation;
feedback citations are resolved leniently (`E1`, `e1`, `[E1]`, `1`, `bewijs 1`) and a quote alone can
identify its evidence; dropped points are shown under the report for inspection.

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

## M2 items (session 3, 2026-09-18, build workspace)

The workspace has no Ollama, so the model-backed loop ran with the fixture chat model (keyword
rules, `tests/fixtures/chat_replies.json`). What that proves is the plumbing and the code's authority
over the appointment, not the model's language behaviour; the first real conversation is the owner's
(OWNER_ACTIONS 7) and moves the loop to `verified_local`.

| Item | Status | Evidence |
|---|---|---|
| Turn workflow (propose → validate → compose, fixed-line fallback, versioned prompts) | `verified_workspace` (fixture model) / `implemented_local` (Ollama) | `tests/test_turns.py::test_workflow_*`: the fixture proposal is validated in code; an invented slot is refused and the model's "genoteerd" reply is replaced by the fixed line; a failing reply call yields the phase's fixed line with the error recorded; a failing first call fails the turn (`test_an_unreachable_model_fails_the_turn_instead_of_pretending`, 502, no evidence, no state change, turn budget untouched) |
| Typed turn endpoint, evidence, skill record, usage | `verified_workspace` | `test_typed_turns_complete_the_speaking_step_with_evidence_and_usage`: reason → slot → confirm through the HTTP layer; 3 `typed_text` + 3 `action_result` evidence rows, speaking record `practised` with 6 evidence ids, `model_calls` used 6 / reserved 0, tokens and audio seconds counted |
| Spoken turn endpoint (upload → WAV → transcript → turn) | `verified_workspace` (fixture STT) | `test_a_spoken_turn_records_the_transcript_as_evidence`: `transcript` evidence with the STT metadata and the recording asset; the recording is in the blob store; a repeated upload with the same request id is answered from the stored turn |
| Character audio per turn | `verified_workspace` (fixture TTS) | `test_character_audio_is_served_and_labelled`: `audio/wav`, 16 kHz, `X-Audio-Label: synthetic-development`; another learner gets 404 |
| Retry with the same request id | `verified_workspace` | `test_a_retry_with_the_same_request_id_returns_the_same_turn`: one turn row, `deduplicated: true`, 2 model calls counted once |
| Model failure path | `verified_workspace` | `test_a_model_failure_keeps_the_failed_turn_and_releases_usage`: 502 with the failed turn in the body, row kept, no evidence, reservations released; same id → 502 again, new id → 200 |
| Restrictions | `verified_workspace` | `test_turn_restrictions`: reading step 400, unknown step 404, other variant 409, empty text 422, typed input in the checkpoint 403; `test_max_turns_closes_the_step`: 409 at the limit |
| One attempt at the transfer checkpoint; resume; abandon | `verified_workspace` | `test_the_transfer_checkpoint_allows_exactly_one_attempt`, `test_start_session_is_idempotent_and_resumes_the_active_session` |
| Speaking step in the browser (push-to-talk, typed input labelled, bubbles, appointment panel, character audio, resume) | `verified_workspace` | `tests/e2e/conversation.spec.ts`: fake microphone → spoken turn labelled `gesproken · transcriptie`; typed turns to "Doel bereikt"; the audio label `synthetic-development`; skill record `practised`; a reload shows the four turns; the checkpoint shows no typed input, disabled help and its one-attempt rule. Screenshots inspected at 1440 px |
| Reading and listening answers as evidence (server-judged), skill records | `verified_workspace` | `tests/test_steps.py::test_reading_answers_are_judged_on_the_server_and_recorded`; browser: `lesson.spec.ts` (2/2 through the API, "stap voltooid"), `steps.spec.ts` (listening 1/1, `Luisteren: practised`) |
| Listening clip synthesised once, labelled, served from the blob store | `verified_workspace` (fixture TTS) | `test_listening_audio_is_synthesised_once_and_labelled` (second request costs no audio seconds); browser: clip label `synthetic-development`, transcript toggle |
| Help-ladder use as evidence; refused in the checkpoint | `verified_workspace` | `test_help_use_is_evidence_and_refused_in_the_checkpoint`; browser: a rung opened appears as `help_used` in the export |
| Writing draft autosave; submission as typed evidence with word count | `verified_workspace` | `test_writing_draft_autosaves_and_the_submission_is_typed_evidence` (draft is not evidence; 422 under 25 words); browser: autosave shown as "bewaard hh:mm", submit → `Schrijven: practised`, draft restored after a reload |
| Feedback grounded in evidence | `verified_workspace` (fixture model) | `test_feedback_cites_only_real_evidence`: 409 before the expectations are met; the fixture's third point cites E99 and is dropped (`dropped_points: 1`); every shown point cites real evidence ids; same request id → same report; `test_speaking_feedback_needs_a_code_validated_action`. Browser: the reading step shows two points, the dropped count and the model line |
| Owner-only JSON export | `verified_workspace` | `test_export_is_complete_and_owner_only`; browser: `/api/export` through the proxy carries `Content-Disposition` and every evidence kind |

## M3 items (session 5, 2026-09-19, build workspace)

| Item | Status | Evidence |
|---|---|---|
| Disconnected state and recovery | `verified_workspace` | `tests/e2e/resilience.spec.ts`: every `/api` call aborted → banner "De server antwoordt niet" with a retry; retry reaches `/api/health` → banner gone. Retry of a turn with the same request id (session 3) |
| Responsive and keyboard operation | `verified_workspace` | the lesson and step specs run at 1440, 768 and 390 px (tablet and phone-width projects now include the listening/writing steps); the talk button works with the space bar; skip link; focus styles |
| Budget counters with an empty pricing table | `verified_workspace` | `components/UsagePanel.tsx` on the home page; `resilience.spec.ts` checks the counters and the "Prijstabel leeg" note |
| Typed input never counts as speaking practice | `verified_workspace` | `test_typed_turns_complete_the_speaking_step_with_evidence_and_usage` (record stays `in_progress`, `typed_only: true`); `test_a_spoken_turn_records_the_transcript_as_evidence` (record moves after a spoken turn); A03 |
| Acceptance checks A01–A06 | `verified_workspace` | `python -m dlp.cli acceptance --check all`; `GET /missions/appointment-change/acceptance/all`; `test_acceptance_checks_run_over_learner_data` |
| Azure Speech adapters (recognition, synthesis; key or managed identity) | `integration_pending` | `tests/test_speech_azure.py` (6 tests) against recorded reply shapes in `tests/fixtures/azure/`; preflight reports `integration_pending`/`not_configured`; no credentials used |
| Azure Blob with managed identity | `integration_pending` | `AzureBlobStore(account_url=…)` path with `DefaultAzureCredential`; the connection-string path is `verified_local` through Azurite |
| Bicep, Dockerfiles, OIDC deployment workflow | `implemented_local` (validated, not executed) | `infra/main.bicep` builds with Bicep CLI 0.47 without errors; `deploy.yml` is `workflow_dispatch` only; Dockerfiles not built here (no Docker in the workspace) |
| `docs/GO_LIVE.md`, `scripts/verify_live.py` | `implemented_local` | the script runs (exit 1 against an unreachable host, as intended); its signed-in checks are exercised in Phase B only |
| Architecture walkthrough, final owner exercise | written | `docs/ARCHITECTURE_WALKTHROUGH.md`; OWNER_ACTIONS 10 |

## Test runs (final)

- API, laptop: `pytest` → 80 passed (session 2). Workspace after session 5: **109 passed** (turns, chat client, steps, feedback, export, Azure adapters, acceptance).
- Browser, workspace after session 5: `python scripts/run.py e2e` → **32 passed** (desktop 18, tablet 7, phone-width 7); session 2 on the laptop: 18 passed.
- Acceptance: A01–A06 PASS over the test data (`test_acceptance_checks_run_over_learner_data`).
- Benchmark dry runs: 40/40 and 0/40.

## Known gaps and honest limits

1. Docker Compose itself was only exercised on the laptop (`services` started `dlp-postgres` and `dlp-azurite`); the build workspace ran the same services natively.
2. No real chat completion against Ollama has run yet; the client is unit-tested against a mock and Ollama is reachable. The turn loop is verified with the fixture model only; the owner's first conversation on the laptop (OWNER_ACTIONS 7) is the real exercise, and `benchmarks/language/harness.py --provider local` the cheapest one.
3. `tone_1s.wav` and `speech-input.wav` are generated tones, not speech. `python -m dlp.cli export-recording <request id>` turns a laptop recording into `tests/fixtures/dutch_sentence.wav` (OWNER_ACTIONS 4); the recording made on 2026-09-18 contains personal data, so a neutral sentence is recommended for the committed fixture.
4. The CI workflow is written but its first run on GitHub has not been observed from here.
5. `PRODUCT_BRIEF.md` / `LEARNER_PROFILE.md` were unavailable; content and A01 are provisional (D-01).
6. The source duration of a MediaRecorder WebM upload reads 0.00 s (the container carries no duration); the canonical WAV's duration is what bounds and usage use. Showing "unknown" instead of 0.00 s is an M3 polish item.
7. In development mode the first request to a route takes 10–20 s on `/mnt/c` (Next.js compiles on demand); production builds do not have this.
8. The fixture chat model follows keyword rules, so the browser tests cannot show how `llama3.1:8b` phrases replies or reads a learner's Dutch; they show that whatever it proposes is validated in code and that a refused proposal never reaches the learner as a confirmation.
9. Feedback quality is unknown until the owner runs it against `llama3.1:8b`; what is verified is the grounding: a point without a real citation never reaches the learner. The Persian renderings in feedback come from the same model and are labelled as unreviewed.
10. The owner's laptop could not be driven from the build workspace (its services are not reachable from here), so the M2–M3 web work carries `verified_workspace`; the owner's own runs (sessions 2, 3b, 4b) are what earned `verified_local` for the microphone path, the whisper models and the reading step with real providers. The remaining `verified_local` runs are OWNER_ACTIONS 7–9.
11. A bug found by the browser tests and fixed: PostgreSQL on the owner's stack reports `Europe/Brussels`, so loaded timestamps carried `+02:00` while fresh ones carried `+00:00`, and the browser's merge of concurrent updates kept the stale session. Connections are now pinned to UTC and the browser compares instants.
