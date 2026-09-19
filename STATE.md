# State

**Release 0.1, Phase A complete in the build workspace.** Updated 2026-09-19 (session 5; implementation day 3). M1–M3 are built; Phase B (Azure) is written and validated but not executed, by the owner's instruction that accounts are created only when the whole project is ready for production testing.
Next action (owner): pull, `python scripts/run.py migrate`, `python scripts/run.py dev`, walk every step with the real providers (OWNER_ACTIONS 7–10), then Gate 2 with the language reviewer (`docs/GATE2_DEMO.md`); when ready for production, `docs/GO_LIVE.md`.
Next action (build): none until the owner reports; the build stops here as agreed.

## M1 — Validate the foundation (local)

- [x] Docker Compose for PostgreSQL and Azurite (`docker-compose.yml`)
- [x] Alembic migrations, initial schema (13 tables) — `apps/api/migrations/versions/0001_initial_schema.py`
- [x] Contract, scenario and evidence schemas (`domains/content/schemas.py`), the appointment-change fixture loaded, **A01 passing**
- [x] Provider interfaces with local implementations (Ollama client, faster-whisper, Piper, Azurite) and fixture implementations
- [x] Fixture identity through the proxy path (web proxy → signed assertion → API validation, allowlist, CSRF)
- [x] Language-benchmark harness with 40 cases; dry runs labelled as a plumbing test (100 % / 0 %)
- [x] Desktop smoke path microphone → upload → ffmpeg → transcription, plus synthetic playback — **verified on the owner's laptop on 2026-09-18 with faster-whisper and Piper in the Windows browser** (see VALIDATION_REPORT)
- [x] Lesson shell rendering the reading step (labels, Persian toggle, vocabulary, questions, help ladder) at 1440 / 768 / 390 px
- [x] Fixed Dutch pack under 300 words (297), every text labelled unreviewed
- [x] Usage counters (atomic reserve/commit/release, deduplication, concurrency test) and the durable job loop
- [x] `STATE.md`, `OWNER_ACTIONS.md`, `DECISIONS.md`, `VALIDATION_REPORT.md`, `docs/ENGINEERING.md`
- [x] Owner has run `preflight` (all ok), `test` (80 passed), `e2e` (18 passed) and the microphone check on the laptop → statuses moved to `verified_local`
- [ ] `PRODUCT_BRIEF.md` and `LEARNER_PROFILE.md` reconciled with the provisional content and A01 (they were not available in session 1; see DECISIONS D-01)

## Gate 1 (passed 2026-09-18)

Presented: the running example, the data records, the decisions D-01 to D-11, the evidence in
`VALIDATION_REPORT.md`. The owner ran the foundation on the laptop (preflight, 80 API tests, 18 browser
tests, microphone check) and opened M2 with "start M2"; the decisions stand as written (D-12).

## M2 — Complete the learning loop (local, speaking first)

- [x] Turn workflow: LangGraph graph `propose_action` (model) → `validate_action` (code) → `compose_reply` (model), fixed-line fallback, versioned prompts — `domains/practice/{prompts,workflow,turns}.py`
- [x] Turn endpoints: typed turn, spoken turn (upload → canonical WAV → transcript → same workflow), character audio, session resume, abandon, one-attempt checkpoint — `api/routes_practice.py`, 16 tests in `tests/test_turns.py` + `test_practice_api.py`
- [x] Push-to-talk turn in the web app: record → send → learner bubble → character bubble → play, appointment panel, resume after reload, retry/cancel — `components/SpeakingStep.tsx`, `lib/client/recorder.ts`, `tests/e2e/conversation.spec.ts` (3 tests)
- [x] Typed conversation labelled as typed evidence (API and web); refused in the checkpoint
- [x] Reading, listening, writing steps record evidence (server-judged answers, typed message with word count); writing autosave — `domains/practice/steps.py`, `components/{QuestionList,ListeningStep,WritingStep}.tsx`
- [x] Persian text-help ladder usage recorded as evidence (refused in the checkpoint)
- [x] Feedback with cited evidence (`domains/feedback/service.py`, `feedback_reports`, `components/FeedbackPanel.tsx`): points without a real citation are dropped and counted
- [x] Transfer variant; independent checkpoint with API-level restrictions (speech only, no help, one attempt, `ended` when the turns run out) and the matching UI; tool-level restrictions are moot until tools exist
- [x] Owner-only JSON export (`GET /export`)
- [x] Turn and request ids, retry recovery (same request id → same turn, failed turns kept), cancellation (abort + reconcile), code-validated appointment actions in the turn loop

## Gate 2 (opens after the owner's laptop run)

To present: the whole learning loop with real providers (reading → listening → speaking → writing →
checkpoint), the evidence behind every skill record (`GET /export`), feedback with its citations and
its dropped-point count, the decisions D-12 to D-14, `docs/GATE2_DEMO.md` for the language reviewer.
Owner exercise: write one feedback-grounding test case (a point that quotes words the learner never
said must be dropped) or run the demo script with a second person.

## M3 — Make it complete and hand over

- [x] Responsive hardening (steps at 768/390 px), keyboard operation, RTL help, loading/error/disconnected states (connection banner), failure recovery (same-request-id retry, restart of a practice session)
- [x] Budget counters with a pricing table that stays empty until Phase B (`UsagePanel` on the home page)
- [x] Azure adapters (speech REST with key or managed identity, blob with managed identity) implemented and unit-tested with recorded fixtures → `integration_pending`
- [x] Bicep (validated with the Bicep CLI) and the GitHub Actions OIDC workflow (manual, not executed); Dockerfiles
- [x] `docs/GO_LIVE.md`, `scripts/verify_live.py`
- [x] Acceptance checks A01–A06 run (CLI, API, tests); `docs/ARCHITECTURE_WALKTHROUGH.md`; final owner exercise (OWNER_ACTIONS 10)
- [ ] Owner verification on the laptop of M2/M3 (OWNER_ACTIONS 7–10) → `verified_local`; Gate 2 with the reviewer

## Gate 3 / handover (open)

Everything the owner needs is in the repository: the running example, the decisions D-01 to D-16, the
validation report with honest statuses, the go-live runbook, the demo script for the reviewer. Phase B
starts when the owner creates the Azure accounts (D-15, GO_LIVE step 0).

## Time log

| Date | Session | Elapsed | Work |
|---|---|---|---|
| 2026-09-17 | 1 | ~2 h 05 min | M1 built and verified in the build workspace; pushed to `main`; Gate 1 handed over |
| 2026-09-18 | 2 | ~1 h 30 min | Laptop checkout, conda environment, WSL fixes (Docker integration, PYTHONPATH, ffmpeg cap, sudo PATH, e2e isolation), M1 verified on the laptop |
| 2026-09-18 | 3 | ~1 h 55 min | M2 speaking loop: turn workflow, turn endpoints, fixture conversation rules, speaking step and checkpoint UI, recorder hook, 91 API tests and 21 browser tests pass; docs and decisions D-12/D-13 |
| 2026-09-18 | 3b | ~0 h 45 min | Owner's first M2 run: Ollama not running → turn now fails clearly instead of pretending (502, budget untouched), refused connections fail fast; playback rewritten to avoid the media-load abort; whisper `small` vs `medium` compared on the laptop, recorder keeps a 400 ms tail; 94 API tests |
| 2026-09-19 | 5 | ~2 h 30 min | M3 (owner asked to finish without pause, which sets the weekly session limit aside): typed-only rule, acceptance checks, Azure adapters, Bicep + workflow + Dockerfiles, go-live runbook, verify_live, connection banner, usage panel, phone/tablet coverage, walkthrough; 109 API tests, 32 browser tests |
| 2026-09-18 | 4b | ~0 h 20 min | Owner's reading-step run with Ollama: feedback truncated at 600 tokens → budget 1000, truncation retried with double, tighter prompt |
| 2026-09-18 | 4 | ~1 h 40 min | M2 completed: answer, help and writing evidence, listening clip, feedback grounded in evidence (migration 0002), export; listening/writing/feedback UI; UTC fix; 101 API tests, 24 browser tests; Gate 2 demo notes |
