# State

## Learning path expansion — 2026-09-24

Implemented a twelve-stage course path from pre-A1 through C2, with an A2 → pre-B1 → B1 bridge,
original stories and four-skill practice, multilingual support, and four-part internal final checks.
Students are gated by their own persisted results; explicit tester accounts can preview all stages.
The UI uses a calmer navy/blue design and removes system identifiers from learning feedback.

This is an authored starter curriculum, not complete coverage of every level or every scanned word.
All nine source PDFs (884 pages) have been indexed; raw OCR and candidate words remain private and
unverified. See `docs/SOURCE_COVERAGE.md` and `docs/CURRICULUM.md` for scope and review requirements.

The five review passes and full GitHub CI succeeded at `1cee6ff` (PR #5). Final release documentation reruns the same required checks before merge. The owner will deploy the update to Azure
after the GitHub release; the existing resources are sufficient. `scripts/deploy_current.sh` performs the
migration-first release and supports an explicit tester email without broadening sign-in access.


## Speech recovery and deployment preflight — 2026-09-22

Follow-up to the green merged release `26ff27d`: speech handlers use the worker pool; actual provider
invocations receive separate accounting IDs; completed turn retries still reuse the saved result.
Storage failure preserves successful transcription/playback, and a later model-limit refusal retains
consumed speech usage. Listening cache identity includes lesson content and voice. The offline Azure
parameter checker rejects incomplete bootstrap configuration without network calls or secret output.
Regression evidence is in the latest `VALIDATION_REPORT.md` entry. Azure live checks remain pending.

## Release 0.2 preparation — 2026-09-22

The learner UI is redesigned around dashboard, mission, progress, speech and settings. The Azure
template now separates foundation, migration job and runtime; the API is internal, PostgreSQL private,
runtime identities narrowly scoped, and startup does not migrate the database. Production refuses
fixtures, development identity, missing providers and unapproved paid usage. Browser regression,
accessibility and container/infrastructure checks run in CI. Follow the latest validation entry;
no live Azure deployment, phone certification or language approval is implied.

Current handoff: `docs/GO_LIVE.md`. Historical milestone notes follow and do not supersede that runbook.

## Maintenance review — 2026-09-22

The scoped reliability and learner-experience update is described in `docs/IMPROVEMENT_REVIEW.md`.
Local lint, TypeScript, production build and non-database regressions have been checked; database and
browser validation runs through GitHub CI. See the newest entry in `VALIDATION_REPORT.md` for the
verified status. This work does not close Gate 2, approve Dutch content, or execute Phase B.

**Release 0.1, Phase A complete in the build workspace.** Updated 2026-09-19 (session 5; implementation day 3). M1–M3 are built; Phase B (Azure) is written and validated but not executed, by the owner's instruction that accounts are created only when the whole project is ready for production testing.
Next action (owner): `python scripts/run.py dev` (one command after a reboot: Docker services, migrations, content, Ollama, servers); the build then walks every step with the real providers through the desktop app's browser (OWNER_ACTIONS 7–10), the owner does the spoken parts; then Gate 2 with the language reviewer (`docs/GATE2_DEMO.md`); when ready for production, `docs/GO_LIVE.md`.

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
- [x] Laptop verification with the real providers of reading, listening, writing, feedback and the typed conversation (2026-09-22, VALIDATION_REPORT "full loop") → `verified_local` for those; spoken turns and the checkpoint still the owner's (OWNER_ACTIONS 7–8)
- [ ] Gate 2 with the reviewer

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
| 2026-09-19 | 6 | ~0 h 15 min | Laptop after a reboot: migrate failed with the database down → `dev` now brings up Docker, migrations, content and Ollama itself; containers restart with Docker Desktop |
| 2026-09-22 | 7 | ~1 h 10 min | Full loop on the laptop with the real providers through the desktop app's browser (reading, listening, writing, feedback, typed conversation); two real defects found and fixed with tests (a named slot not taken as chosen; replies closing or announcing a booking the code had not made); lenient feedback citations; 112 API tests, 32 browser tests |
| 2026-09-19 | 5 | ~2 h 30 min | M3 (owner asked to finish without pause, which sets the weekly session limit aside): typed-only rule, acceptance checks, Azure adapters, Bicep + workflow + Dockerfiles, go-live runbook, verify_live, connection banner, usage panel, phone/tablet coverage, walkthrough; 109 API tests, 32 browser tests |
| 2026-09-18 | 4b | ~0 h 20 min | Owner's reading-step run with Ollama: feedback truncated at 600 tokens → budget 1000, truncation retried with double, tighter prompt |
| 2026-09-18 | 4 | ~1 h 40 min | M2 completed: answer, help and writing evidence, listening clip, feedback grounded in evidence (migration 0002), export; listening/writing/feedback UI; UTC fix; 101 API tests, 24 browser tests; Gate 2 demo notes |
