# Handoff: where the October 2026 programme stands (2026-10-12)

This file is for whoever continues the work. It summarises what was done, what
is in the working tree but not committed, how to run and verify everything on this machine, the rules the
owner set, and the next steps in order. The source of truth for the plan is `docs/ROADMAP.md` (phases P0–P9,
shared contracts, migration ledger, owner decisions O1–O9, and the Progress table at the end); the step-level
designs are in `docs/plan/designs.json` (look up a step by its bracketed id, e.g. `J14`, `X11`, `A-S05`); the
architecture and conventions are in `docs/ENGINEERING.md`; every revised rule has a numbered entry in
`docs/DECISIONS.md` (D-23 to D-34 were written in this programme).

## 1. The programme in one paragraph

The owner (Mahmoud Asadi Heris, GitHub `MahmoudAsadi97/Dutch_Learning_Platform`) asked for three things:
(1) a review of the code and structure against modern practice, (2) real AI agents with Azure in production,
(3) a UX/UI overhaul (practice felt limited and boring, the start was confusing, the UI flat). A read-only
review produced `docs/CODE_REVIEW.md` and the plan in `docs/ROADMAP.md`. The plan runs in ten phases:
P0 safety net · P1 design system and five-tab shell · P2 the start (profile, onboarding, one level, glosses,
copy) · P3 exercise engine and topic sessions · P4 points for all practice, Today as one session, progress ·
P5 engine everywhere, linear path · P6 agent platform and Azure model migration (cut over before
**2027-01-31**, a dated gate set ahead of the current chat deployment's retirement on 2027-04-14) · P7 agents (tutor, conversation
partner, study guide, generated content) · P8 live voice (spike first, go/no-go) · P9 hardening.

## 2. Status

### Done and committed (P0–P3 complete, P4 started)

Every step below has a row in the Progress table of `docs/ROADMAP.md` with the details. Every step from P1
on was followed by an adversarial review whose surviving findings were fixed in an "Apply the review of …"
commit (P0 had none; the three P1 reviews are commits a0bea19, 244020d and c723e2b without Progress rows).

**Nothing is released.** Local `main` is 58 commits ahead of `origin/main` (795697b) and nothing is pushed, so
no phase release gate has run: P0–P3 and migrations 0008–0010 are not in production. The CI job that
regenerates the screenshot baselines (step 0.3) is committed locally; its PR waits for the first push. The
first release gate (end of P4) will cover P0–P4 together unless the owner wants one per phase.

**Where the code is:** the project folder `C:\Users\Nima\Desktop\MINE\My_projects\Dutch Learning
Platform\Final_Project_v1`, branch `main` (it has no `apps/api/.venv` yet: run `python scripts/run.py setup` there
first). The test runs below were made in a second local checkout of the same commits (`git worktree list`).

| Phase | Steps | What exists now |
|---|---|---|
| P0 | 0.0–0.9 | First-day checks (`docs/plan/CHECKS.md`), Prettier + Vitest/RTL, the visual freeze (`run.py e2e-visual` in the pinned Playwright container), ratchet tests (untyped routes, layer imports, CSS hex/dead selectors, hard-coded Dutch text), quick fixes, `DomainError` with `code`, one stages registry and storage-key module, TanStack Query provider, engine characterisation tests |
| P1 | 1.1–1.8 | Dead CSS removed, cascade layers and tokens (`app/styles/`), base layer (focus ring, 44 px targets), per-skill colours, primitives in `components/ui` (Button, Card, Badge, Notice, IconTile, Field, Skeleton, EmptyState, Dialog, Toast, Tabs, Stepper, ProgressRing, …), motion with reduced-motion fallbacks, the five-destination shell (Vandaag, Leren, Verhalen, Spreken, Woorden), `/dev/ui` gallery |
| P2 | 2.1–2.8 + reviews | `learner_profiles` (migration 0008), `GET/PATCH /me`, onboarding at `/welkom` behind `FIRST_RUN_GATE`, one level everywhere, the gloss layer (typed copy catalogue in `lib/copy/*`, `UiText`, English/Persian under Dutch; Persian hidden until the owner reviews each batch at `/dev/copy`), interface copy on "je", error copy from API `code`s |
| P3 | 3.1–3.9 + reviews | Activity service (`domains/activity`, migration 0009, one rules table, Brussels day, goal crossing), tolerant answer comparison, the exercise engine (`domains/exercises`, migration 0010) with twelve item kinds (choice, cloze, odd one out, match pairs, de/het, typed cloze, typed recall, sentence builder, ordering, listen-and-choose, dictation, shadowing), the web runner `components/exercise/*` at `/oefenen`, topic and lesson sessions (D-31), and the topic reader starting with a session (D-32) |
| P4 | 4.1 + review | `GET /today` only reads (`today_view`), `POST /today/prepare` keeps one unread episode queued (idempotent), one function-scoped DB session dependency for every route so a failed commit is a 500 (D-33), `last_seen_at` throttled, series insert race-safe, `lock_learner` for profile+series writes |

Last commits (all authored by the owner): `ae865bf` Finish a reading or listening topic with its last answer ·
`1e37ae2` Apply the review of the read-only Today · `fa92e61` Read Today without writing; prepare it on opening
· `c131fa4` Apply the review of the topic reader · `0bba87c` Start practice topics with a session and a start card.

### Committed, not yet reviewed: step 4.2 (points for every kind of practice, design J11)

Committed as "Give points for every kind of practice". The 29 files it changed: API sources
`api/routes_curriculum.py`, `api/routes_practice.py`, `api/routes_speech.py`, `api/routes_topic_conversations.py`,
`domains/activity/{day,rules,service}.py`, `domains/curriculum/{service,topics}.py`,
`domains/practice/{steps,turns}.py`, `domains/stories/service.py`, `domains/topic_conversations/service.py`,
`domains/videos/service.py`; tests `test_activity`, `test_coaching`, `test_curriculum`, `test_speech_api`,
`test_steps`, `test_stories`, `test_topic_conversations`, `test_topics`, `test_turns`, `test_videos`;
`apps/web/components/SpeechCheck.tsx`; docs `DECISIONS.md`, `ENGINEERING.md`, `ROADMAP.md`, `VIDEO_LESSONS.md`.

- `domains/activity`: `record_activity(..., skill=, counted=)` (an action's own skill; a day counter that moves
  by another number than the paid units), `day_bounds_utc`, eight new kinds in `rules.py`: `course_questions`
  (1/question, per activity and day), `course_task` (5), `stage_check` (15, once per attempt),
  `mission_questions` (1/question), `mission_writing` (5), `mission_turn` (2), `conversation_turn` (2),
  `speech_warmup` (2 a day).
- Awards, only in entry functions and after any paid call and every refusal: `curriculum.service.save_practice`,
  `curriculum.service.attempt_points` (called by the submit route; never an admin preview),
  `curriculum.topics.save_topic_practice` (the stored response stays unchanged; a replay adds only
  `replayed(...)`), `topic_conversations.service.turn_points` (route), the daily start limit on the Brussels day,
  `practice.steps.submit_answer` / `submit_writing`, `practice.turns.submit_turn` (dedup path says `replayed`),
  `POST /speech/transcribe` with form field `purpose=warmup` (`SpeechCheck.tsx` sends it).
- Owner decision O1: story and video questions pay per answered question; `questions_correct` still counts
  the correct ones (`counted=`).
- Ten new tests per call site in `test_activity` (2), `test_curriculum` (2), `test_topics`, `test_topic_conversations`
  (2), `test_steps`, `test_turns`, `test_speech_api`, plus assertions added to existing tests (`test_coaching`'s
  replay test, the curriculum and topic outage tests); pins updated in `test_stories` (19 and 21 points) and
  `test_videos`. `routes_practice.py` adds the award's `goal_reached` to the mission answer, writing and turn
  responses.
- Docs: D-34 in `DECISIONS.md`, the "Activity and points" section of `ENGINEERING.md`, `VIDEO_LESSONS.md`, and
  a 4.2 row in the ROADMAP Progress table.

**Verification state of 4.2:** the full API suite passes with these changes (803 passed on 2026-10-12, which
includes the 4.2 tests and the two concurrency tests of the 4.1 review); the web component tests pass (73), and
lint, types and formatting are clean. Still to do for 4.2: `npm run test:unit`, `run.py e2e` (Today's goal
numbers may change in specs that practise lessons) and an adversarial review of the 4.2 diff, whose fixes go
into an "Apply the review of …" commit.

### Also not yet re-verified (from 4.1 and the 3.9 review)

- `run.py e2e` had 145/146 green for 4.1; the failure was the overflow check at 390 px in
  `skill-topics.spec.ts` "a writing warm-up runs on its words and hands over to the task" (summary state). It
  passed in the 3.9 run, so it may be flaky; re-run it alone. `run.py` splits `E2E_ARGS` on spaces and
  ignores quotes, so use a pattern without spaces: Git Bash `E2E_ARGS='tests/e2e/skill-topics.spec.ts -g
  writing.warm-up --repeat-each=4' python scripts/run.py e2e`, PowerShell `$env:E2E_ARGS='tests/e2e/skill-topics.spec.ts
  -g writing.warm-up --repeat-each=4'; python scripts/run.py e2e`. If it fails again, find the element wider than
  the viewport in the warm-up summary at 390 px.
- `run.py e2e-visual` (screenshot comparison) was interrupted when Docker stopped; run it once.
- The e2e review-label spec moved to stage a1 (`skill-topics.spec.ts` "a reused topic says which stage it
  repeats") has not run yet.

## 3. Rules the owner set (binding)

1. **Commits:** messages describe only the change; no co-author or tool attribution lines in messages, PR
   texts or code comments. The author is always the configured git user (Mahmoud Asadi Heris). One commit per
   roadmap step, plus one "Apply the review of …" commit.
2. **Saving:** the owner works from the main folder `C:\Users\Nima\Desktop\MINE\My_projects\Dutch Learning
   Platform\Final_Project_v1` (branch `main`). Work done in another checkout must also land there (fast-forward
   with `git merge --ff-only`, never force).
3. **Push:** the owner pushes, signed in to Git Credential Manager as `MahmoudAsadi97` (the account
   `MahmoudAsadiH` cannot write to the repository). Never put an access token in a command, a URL or a file.
4. **Docker:** restarting Docker Desktop or WSL is the owner's job; never force-kill them.
5. **Owner decisions win:** when a reviewer's finding contradicts an approved decision (D-xx, O1–O9,
   `designs.json`), the decision stands.
6. **Honesty rules:** points reward doing, never a judgement of the learner's Dutch; no overall level, no
   pronunciation score, no certificate; generated or unreviewed content is labelled; the final check's answers
   never reach the browser; the API is never public.

## 4. Running and verifying on this machine (Windows 10)

- Setup once per checkout: `python scripts/run.py setup` (creates `apps/api/.venv`, installs web packages and
  Playwright). The main folder has no `apps/api/.venv` yet and an older `node_modules`, so run setup there first.
- Services: `python scripts/run.py services` (PostgreSQL + Azurite in Docker), `migrate`, `fixture`, `dev`.
- API tests: `python scripts/run.py test`, or directly from `apps/api`:
  `TEST_DATABASE_URL=postgresql+psycopg://dlp:dlp@127.0.0.1:5432/dlp_test PYTHONIOENCODING=utf-8 .venv/Scripts/python -m pytest -q`
  (use `127.0.0.1`, not `localhost`: `localhost` resolves to `::1` and every connection waits 8 s).
- Lint: `ruff check src tests` (in `apps/api`), `npx eslint . --max-warnings=0`, `npx tsc --noEmit -p tsconfig.json`
  and `-p tsconfig.test.json`, `npm run format:check` (in `apps/web`).
- Web tests: `npm run test:unit` (node test runner, `tests/unit/*.test.mjs`), `npm run test:component` (Vitest).
- `make` is not installed on this machine and the Makefile's lint target expects `.venv/bin`; run the commands
  above instead of `make lint`.
- Browser tests: `python scripts/run.py e2e` (Playwright with axe and overflow checks at 1440/390/320; pass
  options through `E2E_ARGS`), `python scripts/run.py e2e-visual` (screenshot comparison in the pinned Linux
  container; add `E2E_ARGS="--update-snapshots=all"` only after reading the diff images).
- Never run two pytest or e2e runs at once: they share `dlp_test` and deadlock on TRUNCATE.
- Write files as UTF-8 bytes with LF line endings (Python `write_text` writes CRLF on Windows and Prettier then
  fails). A blanket CRLF→LF pass must skip binary files (it once corrupted PNG baselines).
- Ratchets to respect: the hard-coded Dutch JSX text budget is exact per file (e.g. `SkillTopicPractice.tsx` 60,
  `TodayHome.tsx` 62): new interface text goes into `lib/copy/*` with nl/en/fa; routes without
  `response_model` may only shrink; CSS hex colours and dead selectors may only shrink; the layer-boundary
  import allowlist may only shrink.
- More Windows quirks and their fallbacks: `docs/plan/CHECKS.md`.

## 5. Next steps, in order

### Finish P4

1. **4.2** — run the e2e suite and review it as described above; fix what the review finds.
2. **4.3 [J14, API]** — `domains/activity/summary.py`; `GET /progress/summary` (goal, streak, twelve-week
   calendar, per-skill practice counts this week kept separate, word strength buckets new/learning/strong from
   SM-2 intervals, current stage with topic counts, recent activity, the points rules list for an explainer) and
   `GET /progress/day`; `tests/test_progress_summary.py` (new learner gets zeros and `day_one`, a typed
   conversation never counts as speaking, another learner's events excluded, `/progress/day` matches Today's goal).
3. **4.4 [J12]** — `domains/today/snapshot.py` (`learner_snapshot`) and `domains/today/planner.py`
   (`build_candidates`, `build_plan`, `validate_proposal`); move Today's routes to `api/routes_today.py`, keep
   every existing key and add `session` (contract `today-plan-v1`: ordered steps with kind, status, minutes,
   points, benefit, reason, href and exactly one primary) and `week`; add side-effect-free `GET /today/ready`;
   `ensure_buffer` stops auto-queueing while the newest episode is an unread failure (the learner retries).
   Tests in `tests/test_today_plan.py` (determinism, step order for a new learner, due words put the warm-up
   first, a step turns done after its activity event, `validate_proposal` refusals, no writes on GET).
4. **4.5 [J13 + DS-11]** — replace `TodayHome` with `components/today/*` (SessionHero with one primary button
   and minutes, SessionSteps/StepCard, GoalRing with the streak, labelled WeekStrip, WaitingCard
   queued→writing→rewriting→ready, SessionSummary, celebration that respects reduced motion); move the wish form,
   cast and memory to `/verhalen` (SeriesPanel); `ReadyNotifier` (polls `/today/ready` only while something is
   pending) and `HeaderProgressChip`. Goal per owner decision O3 (default: session length kort/gewoon/stevig).
   Update `stories.spec.ts`, `design.spec.ts` and the screenshot baselines together (the pinned strings are
   listed in the J13 and DS-11 designs).
5. **4.6 [J14, web]** — `/progress` as a dashboard: streak calendar, four skill rings labelled as practice
   frequency (never a level), word strength, stage with topic counts, recent activity, "Hoe verdien je punten?"
   from the rules; keep `CurriculumProgress` (12 rows) and mission progress in disclosures; `progress.spec.ts`.
6. **4.7 [J15]** — decision records for the journey, README navigation, LEARNING_DESIGN, LEARNING_AGENTS home
   paragraph, STORY_ENGINE and ENGINEERING lines about Today, STATUS, VERIFICATION, regenerated `docs/previews`.
7. **Release gate** (ROADMAP "Release gate"), the first one, once the owner can push: first the small PR that
   adds the CI screenshot-regeneration job (step 0.3); then one PR to `main` for P0–P4 (or one per phase if the
   owner prefers), rehearsal of migrations 0008, 0009, 0010 (and any P4 migration) on a restored production copy,
   a backup and the current image digests, a migration-first release with `bash scripts/deploy_current.sh` from WSL
   with a signed-in `az` (clean tree, green main CI for the SHA; runbook `docs/GO_LIVE.md`), then
   `scripts/verify_live.py`. The first-run redirect and the new Today ship behind an environment switch.

### P5 — engine everywhere (5.1–5.7)

Word review on the engine (typed recall mapped to SM-2, grade buttons kept as override) · Today warm-up,
"repeat your mistakes" and while-you-wait on the engine · "Oefen met deze aflevering" after an episode · linear
path page (current stage large, one "Ga verder", rail of twelve nodes; keep `data-testid=curriculum-path`) ·
linear stage page with a lesson stepper; lessons on the engine; practice answer keys no longer sent to the
browser · retire the duplicate multiple-choice renderers, VocabularyRecall and the alphabet quiz · move
missions, speech studio, videos and settings onto primitives.

### P6 — agent platform and Azure (must cut over before 2027-01-31)

OpenAPI export with generated web types, pyright, coverage floor · `LlmGateway` (reserve, call, settle; one
failure policy) and `call_claims` with DB lock/idle timeouts · retrying sites onto the gateway · remove
LangGraph (two linear graphs become plain functions; architecture test forbids vendor SDKs in domains) · model
port v2 (`respond()`, `stream()`) · Azure Responses API adapter (stateless, strict JSON schema and strict tools,
hand-written `httpx`) · side-by-side EU Data Zone deployments in Bicep with an eval gate (targets per Microsoft's
pages read 2026-10-06: gpt-5.6-luna small, gpt-5.6-terra strong; fallbacks gpt-6-luna/gpt-6-sol, then
gpt-5.4-mini/gpt-5.4; confirm names with the Models API at deploy time) · the in-house agent runtime (whole-run
budget reserved before the first call, step ceiling, read-only tools, propose tools validated by code, one
repair, deterministic fallback) · SSE end to end with JSON twins · telemetry without prompts or identifiers.
Needs owner decision O6 (EU Data Zone processing, caps, quota) before 6.6.

### P7 — agents and generated content

Tutor "Leg uit" (authored explanation first, grounded follow-ups, mini-drill) · conversation partner (a guarded
generated reaction before the authored anchor; feedback quoting the learner's own turns) · scenario scale-up ·
optional open-turn mode (O5) · study guide (the model orders code-built candidates; code pins and explains) ·
model-judged exercise kinds · generated items behind a validator and the review queue · run visibility. Every
flag off by default; Dutch quality needs a reviewer (O7).

### P8 — live voice

Spike first (`docs/LIVE_VOICE.md`), ten go/no-go criteria; without a pass, no-go unless the owner approves a
public relay (plan B, revises the single-public-entry rule).

### P9 — hardening

Remaining paid sites on claim/call/settle; provider failures as 503 with `code`; layering clean-up; split large
components; promote CI images by digest; retention jobs; docs refresh.

## 6. Open items for the owner

- Push `main` signed in as `MahmoudAsadi97`; revoke any access token that was shared outside GitHub; open the
  PR with the CI screenshot-baseline job (step 0.3).
- Run the live-voice spike (P8 step 8.0, planned during P2, not done; `docs/LIVE_VOICE.md` does not exist yet);
  it needs only Azure sign-in and the SSE check from 0.0, and decision O8 depends on it.
- Review the Persian glosses at `/dev/copy` (they stay hidden until reviewed, O2).
- Turn on `FIRST_RUN_GATE` in production after seeing onboarding live.
- Run `scripts/verify_live.py --measure-answers` on Azure (p95 answer round trip, target ≤ 300 ms).
- Decide O3 (goal as session length or points), O4 (automatic daily study-guide run), O5 (partner mode), O6
  (Azure EU Data Zone, caps, quota; needed before P6 step 6.6), O7 (who reviews generated Dutch), O8 (voice
  after the spike). O2 and O9 are settled as in the ROADMAP table; O1 is adopted (read-aloud since 0.5, D-23;
  questions per answered with 4.2, D-34, not yet committed).

### API test result at handoff

`pytest -q` in `apps/api` on the working tree (4.2 included): **803 passed** in 3 min 32 s (2026-10-12).
