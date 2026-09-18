# State

**Release 0.1, Phase A.** Updated 2026-09-18 (session 3; implementation day 2). Gate 1 passed on the owner's word ("start M2"); M2 is in progress.
Next action: finish the speaking loop in the web app (session 3), then the remaining M2 steps.

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
- [ ] Push-to-talk turn in the web app: record → send → reply bubble → play (in progress)
- [x] Typed conversation labelled as typed evidence (API); web input pending
- [ ] Reading, listening, writing steps record evidence; autosave
- [ ] Persian text-help ladder usage recorded as evidence
- [ ] Feedback with cited evidence (`domains/feedback`)
- [ ] Transfer variant; independent checkpoint with API- and tool-level restrictions
- [ ] Owner-only JSON export
- [x] Turn and request ids, retry recovery (same request id → same turn, failed turns kept), code-validated appointment actions in the turn loop; cancellation in the web app pending

## M3 — Make it complete and hand over

- [ ] Responsive hardening, keyboard operation, RTL help, loading/error/disconnected states, failure recovery
- [ ] Budget counters with a pricing table that stays empty until Phase B
- [ ] Azure adapters (speech, blob with managed identity) implemented and unit-tested with recorded fixtures → `integration_pending`
- [ ] Bicep and the GitHub Actions OIDC workflow (not executed)
- [ ] `docs/GO_LIVE.md`, `scripts/verify_live.py`
- [ ] Every 0.1 acceptance check run; architecture walkthrough; final owner exercise

## Time log

| Date | Session | Elapsed | Work |
|---|---|---|---|
| 2026-09-17 | 1 | ~2 h 05 min | M1 built and verified in the build workspace; pushed to `main`; Gate 1 handed over |
| 2026-09-18 | 2 | ~1 h 30 min | Laptop checkout, conda environment, WSL fixes (Docker integration, PYTHONPATH, ffmpeg cap, sudo PATH, e2e isolation), M1 verified on the laptop |
| 2026-09-18 | 3 | ~0 h 40 min so far | M2: turn workflow, turn endpoints, fixture conversation rules, 16 tests (91 API tests pass) |
