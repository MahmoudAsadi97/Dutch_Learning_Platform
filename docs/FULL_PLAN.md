# Taalstudio — the full plan, what is done and what is next

*Generated 2026-10-12 from `docs/ROADMAP.md` (the executable plan and its Progress table), `docs/HANDOFF.md` (the
state at handoff) and the approved plan document kept outside the repository (§4's review findings, §14's risks
and per-phase checks, and the fuller wording of steps, contracts, decisions and rules come from it). ROADMAP and HANDOFF stay the source of truth; the step-level designs
are in `docs/plan/designs.json`, the decisions in `docs/DECISIONS.md` (D-23 to D-34 were written in this programme,
D-34 with step 4.2; the next free number is D-35), the architecture in `docs/ENGINEERING.md`.*

**Contents:** 1. Status at a glance · 2. Where the work stands now · 3. The owner's rules · 4. What the plan
is for · 5. Decisions confirmed with the owner · 6. Key technical choices · 7. Shared contracts · 8. Migration
ledger · 9. All phases and steps with their status · 10. Next steps in detail · 11. Release gate ·
12. Owner decisions · 13. Rules consciously revised · 14. Risks and verification · 15. Running and verifying
on this machine · 16. Open items for the owner · 17. Appendix: what each finished step delivered

## 1. Status at a glance

| Phase | Status |
|---|---|
| P0 — Safety net (slim) | ✅ Done locally (not yet released) |
| P1 — Design system and the five-destination shell (first visible change) | ✅ Done locally (not yet released) |
| P2 — The start: profile, onboarding, one level, glosses, copy | ✅ Done locally (not yet released) |
| P3 — Exercise engine core and topic sessions (the practice fix) | ✅ Done locally (not yet released) |
| P4 — Points for all practice, Today as one session, progress | 🔄 In progress |
| P5 — Engine everywhere, linear path and stage pages | ⬜ Not started |
| P6 — Agent platform and Azure model migration (cut over before 2027-01-31) | ⬜ Not started |
| P7 — Agents and generated content | ⬜ Not started |
| P8 — Live voice conversation | ⬜ Not started |
| P9 — Hardening and close-out | ⬜ Not started |

Done so far: P0, P1, P2 and P3 completely, and step 4.1 of P4; every step from P1 on was followed by an adversarial review whose fixes were applied (P0 had none). Local `main` is 58 commits ahead of `origin/main` (795697b); nothing is pushed or released yet. Step 4.2 is committed and passes the API suite (803 tests); its e2e run and review are still to do. Left: the rest of P4 (4.3–4.7), the first release gate, then P5 to P9.

## 2. Where the work stands now

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

## 3. The owner's rules (binding)

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

## 4. What the plan is for

The owner (Mahmoud Asadi Heris, GitHub `MahmoudAsadi97/Dutch_Learning_Platform`) asked for three things:
(1) a review of the code and structure against modern practice, (2) real AI agents with Azure in production,
(3) a UX/UI overhaul (practice felt limited and boring, the start was confusing, the UI flat). A read-only
review produced `docs/CODE_REVIEW.md` and the plan in `docs/ROADMAP.md`. The plan runs in ten phases:
P0 safety net · P1 design system and five-tab shell · P2 the start (profile, onboarding, one level, glosses,
copy) · P3 exercise engine and topic sessions · P4 points for all practice, Today as one session, progress ·
P5 engine everywhere, linear path · P6 agent platform and Azure model migration (cut over before
**2027-01-31**, a dated gate set ahead of the current chat deployment's retirement on 2027-04-14) · P7 agents (tutor, conversation
partner, study guide, generated content) · P8 live voice (spike first, go/no-go) · P9 hardening.

The approved plan for the three asks of October 2026: a structure review against modern practice
(see [CODE_REVIEW.md](CODE_REVIEW.md)), bounded AI agents on Azure, and a UX/UI overhaul. `docs/ROADMAP.md` is
the executable version: phases, steps, shared contracts, owner decisions, the migration ledger and the
map from each step to its detailed design. The step-level designs (files, tests, data models, API
contracts, risks per step) live in `docs/plan/designs.json`; the red-team findings that reshaped the
plan are in `docs/plan/redteam.json`.

How to read a step id in brackets: `A-S01` = `designs.json` track `agents`, judged final design, step
`S01`; `S01` = track `structure`; `X01` = track `exercise-engine`; `J01` = track `learner-journey`;
`DS-01` = track `design-system`; `V-0` = track `live-voice` step `P7.0`.

Extract one step's full design with a read-only one-liner from the repository root:

```bash
node -e "const d=JSON.parse(require('fs').readFileSync('docs/plan/designs.json','utf8'));const t=d.tracks.find(x=>x.key==='exercise-engine');const s=(t.design||t.judged.final_design).steps.find(s=>s.id==='X04');console.log(JSON.stringify(s,null,2))"
```

### What the review found (the reasons for the plan)

The owner asked for three things on the Dutch learning platform (Next.js 16 web + FastAPI API, Azure in production):

1. Review the code and structure against modern techniques.
2. Decide whether real AI agents would level it up (production on Azure).
3. Improve the UX/UI: the practices feel "very limited, boring", the start is confusing, it is unclear how the app helps learn Dutch, and the UI should be more interactive and more colourful while staying professional.

A read-only review (a code review, a verification pass that confirmed 46 of 70 claims and corrected 24, six track designs and a red-team pass over the merged plan) found:

- **Why the start is confusing.** No onboarding, placement or explanation of the method. The first screen is all Dutch, shows a 1–3 minute "writer is busy" wait and a wall of zeros. Nine navigation destinations overlap (two story systems, two word systems, two conversation systems). The level is set in three places that disagree: a new learner gets A1 stories but a pre-A1 path.
- **Why practice is boring.** 4,800 topic activities use three mechanics (2-option multiple choice, record-and-submit, type-and-submit). Nothing is shuffled or adaptive, typed recall is never checked, and English glosses under the options give answers away. The banks are templated and reused across stages. Points and streak count only stories, videos and word review, so course work shows "0 / 20".
- **Why it looks flat.** Three CSS redesigns are stacked by import order (conflicting `:root` blocks, 356 hex colours, about 610 dead lines, one `@keyframes`, no `:active` state). Colour appears only on episode covers.
- **Agents today.** Every model feature is a validated single call or a fixed pipeline. There is no tool calling, strict structured output, streaming or learner memory, and the production chat deployment (gpt-4.1-mini, NoAutoUpgrade) stops serving on 2027-04-14 per Microsoft's retirement schedule.
- **Structure.** Strong security, cost control and tests. Weak spots: provider calls inside database row locks, paid-call and error boilerplate duplicated across about 11 call sites with differing failure policy, an untyped HTTP contract, a single-threaded job loop without lease renewal, every page a client island with hand-rolled fetching, components with 3,000-character lines.

## 5. Decisions confirmed with the owner

| Question | Decision |
|---|---|
| Scope | All three tracks, implemented phase by phase in reviewable steps |
| Interface language | Dutch stays, with English/Persian shown underneath for beginners; onboarding fully bilingual |
| Agent features | Tutor ("explain my mistake"), study guide on Today, free conversation partner, live voice conversation |
| Agent hosting | Bounded, tool-using agents inside the existing FastAPI app; code keeps validating everything |
| Motivation | Effort-based and non-punitive: points for all practice, streaks, summaries, progress rings. No hearts, no overall level, no pronunciation score |

## 6. Key technical choices

- **Agent architecture: a small in-house loop on the existing model port, no framework.** The judge scored it 60 against 52 (LangGraph agents with a Postgres checkpointer) and 51 (Microsoft Agent Framework in-process): it keeps every rule literally testable (reserve before call, one request per step, never replay), keeps CI on fixtures and local runs on Ollama, and adds no dependency. LangGraph is removed (it only runs two linear three-step graphs). Tool and agent definitions map one-to-one onto Agent Framework function tools, which stays the documented exit path.
- **Honest description of the agents.** The tutor is a real tool loop (at most 3–4 model steps over read-only, learner-scoped tools). The study guide is one ranking call shaped as a "propose" tool over code-built candidates. The conversation partner is a two-request pipeline (interpret, then a guarded reaction) rather than an open chat; an open-turn mode is an owner decision in P7. Voice uses one forced tool call per turn. This is the right shape for "models propose, code decides"; it is stated plainly so nobody expects free-form autonomy.
- **Azure: stateless Responses API through a hand-written `httpx` adapter**, strict JSON-schema output and strict function tools, proven first against the existing deployment. New EU Data Zone deployments run side by side with the current one and are switched after an eval gate, **before 2027-01-31**. Target per Microsoft's pages read on 2026-10-06: gpt-5.6-luna (small) and gpt-5.6-terra (strong); first fallback gpt-6-luna/gpt-6-sol; last resort gpt-5.4-mini/gpt-5.4 (retires 2027-09). Names and versions are confirmed with the Models API at deploy time.
- **Streaming: FastAPI's built-in SSE (present in the locked 0.141.1) on twin `.../stream` routes**, driven by a runner thread that settles usage even if the browser disconnects. Every stream has a plain JSON twin. The proxy's timeout applies to time-to-headers only; long streams roll over through `?after=` resume.
- **Practice: a server-owned exercise engine.** Sessions are generated from a seed and graded on the server; the browser never receives an answer key before answering. Twelve item kinds come from existing content with no new authoring; generated and validated content follows in P7.
- **One learner profile** (`learner_profiles`) is the only source of level, daily goal and support language. **One activity service** (`record_activity`) awards all points. **One paid-call gateway** (`LlmGateway`) owns reserve, call and settle. See Shared contracts.
- **Styling: design tokens and cascade layers, not Tailwind.** Token-driven global classes in `@layer`s with typed wrappers in `components/ui`; the roughly 70 class selectors the e2e suite depends on stay on the same elements. Motion is CSS-only. Icons move to `lucide-react` behind the existing `Icon` component.
- **Web data: TanStack Query** over the existing `apiFetch`; generated TypeScript types from an OpenAPI export arrive with the agent platform, when new routes start consuming them; Vitest + React Testing Library for components.
- **Live voice: the API brokers the session.** One outbound WebSocket to Azure Voice Live; the browser uses the existing signed proxy (SSE down, sequenced audio chunk POSTs up). The partner's reply is produced as text, gated sentence by sentence, and only then spoken through the TTS port, so nothing unapproved is heard. No new public ingress: a ticketed relay container app would revise the single-public-entry rule and needs an owner decision; without it a failed spike is a no-go.

## 7. Shared contracts (one owner each; other tracks adopt these)

| Seam | Contract |
|---|---|
| `GET /me` | Returns the profile and, from day one, `features: {}` (agent and voice switches land there later). A development/test-only reset clears `onboarded_at` for e2e. |
| Activity | `domains/activity/`: `record_activity(session, learner_id, *, kind, ref, request_id, skill=None, meta=None)`; append-only `activity_events` with `UNIQUE(learner_id, kind, dedupe_key)`; one rules table owns point values and scopes for every kind, including exercise kinds and shadow; `learning_days` gains `goal_target`, `exercise_items`, `exercise_sessions`. Awards happen after `_record_episode` returns, never inside it (a unit test calls it with `session=None`). |
| Mistakes | `domains/exercises/taxonomy.py` is the single category list (vocabulary_meaning, vocabulary_form, article, spelling, word_order, grammar_form, missing_word, listening_discrimination, comprehension, punctuation, word_choice, preposition); `learner_mistakes` carries the superset columns `source, source_id, stage_id, skill, kind, category, given, expected, quote, assessed, request_id, resolved_at`. `content/tutor/categories.json` is validated against the module. |
| Snapshot | `domains/today/snapshot.py` built in P4; the agent platform extends it with mistakes; no second snapshot module. |
| Today payload | One `session` block (`today-plan-v1`: ordered steps with kind, status, minutes, points, benefit, reason, href, one primary). Warm-up and mistakes candidates and the study guide all feed this contract; there is no separate `practice` or `guide` block. `GET /today` is read-only from P4 step 4.1; the page loads through idempotent `POST /today/prepare`. |
| Gateway | `domains/llm/gateway.py` as judged (A-S01): legacy sites reserve in the caller's transaction; agent runs reserve the whole budget on their own connection before the first call; no audit row for single calls. Structure steps S09 and S12 are superseded; what survives from them is the `call_claims` helper and database timeouts (P6 step 6.1), `ProviderRejected`, and no total proxy timeout on streams. |
| Migrations | Numbered in landing order: 0008 learner_profiles, 0009 activity_events, 0010 exercises (sessions, items, mistakes, suggestions), then agent, scenario and voice tables as they land. One ledger in `docs/ROADMAP.md`. |
| Screens | The journey track owns the structure of the shell, Today, path and stage pages; design-system steps are style passes that follow. The shell is laid out once (P1 step 1.7) and the path once (P5). |
| Word review | Engine word kinds keep the four grade buttons as the visible override after the code check; the word-review spec is rewritten once (P5 step 5.1). |
| Gloss on tabs | Five tabs; Dutch label plus a short gloss key from 360 px, none at 320 px; tested in nl-fa at 320 and 390. |

As implemented (4.2): `record_activity(session, learner_id, *, kind, ref, request_id="", units=1, counted=None, skill=None, meta=None, now=None)`.

## 8. Migration ledger

| Revision | Table(s) | Step |
|---|---|---|
| 0008 | `learner_profiles` | P2 2.1 |
| 0009 | `activity_events`; `learning_days` + `goal_target`, `exercise_items`, `exercise_sessions` | P3 3.1 |
| 0010 | `exercise_sessions`, `exercise_items`, `learner_mistakes`, `word_suggestions` | P3 3.3 |
| 0011 | `agent_runs` | P6 6.7 |
| 0012 | `tutor_threads`, `tutor_messages`, `writing_reviews` | P7 7.1 |
| 0013 | `study_plans` | P7 7.7 |
| 0014 | `topic_conversations` + `engine_version`, `max_turns`, `feedback`, `feedback_request_id` | P7 7.3 |
| 0015 | `conversation_scenarios` | P7 7.5 |
| 0016 | `generated_items` | P7 7.9 |
| 0017 | `voice_sessions`; pricing entries for voice | P8 8.3 |

Numbers are claimed here before a migration is written; a step that lands out of order takes the next
free number and updates this table.

## 9. All phases and steps with their status

Each step is one reviewable pull request of one to four commits, with the test suites green at the end
of the step. Commits and pushes happen only on the owner's say-so.

Status legend: ✅ done · ⬜ to do.

### P0 — Safety net (slim) — ✅ Done locally (not yet released)

| Step | Status | What changes |
|---|---|---|
| 0.0 | ✅ done | First-day checks on a throwaway branch, results recorded in `docs/plan/CHECKS.md` with the fallback for each: `python scripts/run.py setup` in this worktree (no `node_modules`, no `.env` today); `next build` with one stylesheet wrapped in `@layer` under Turbopack; a pytest proving commit timing of yield dependencies on FastAPI 0.141.1 with and without `scope='function'`; `alembic check` on a fresh database; a throwaway SSE route through `next start` (compression); whether eslint flags state-setting inside effects; the pinned Playwright Linux container running against host servers via `E2E_BASE_URL`. |
| 0.1 | ✅ done | Commit the three session result files verbatim under `docs/plan/` (review, verification, designs), plus `docs/CODE_REVIEW.md` (findings with the verification corrections and the judge's error list applied) and `docs/ROADMAP.md` (this plan with the migration ledger). Note that web line anchors refer to commit 795697b; locate by selector, test title or quoted string after 0.2. |
| 0.2 [S01] | ✅ done | Prettier one-off format commit over ts/tsx/mjs, excluding legacy `app/*.css`, listed in `.git-blame-ignore-revs`; all Playwright specs pass with zero spec edits; Vitest + React Testing Library; `tsconfig.test.json` so tests are type-checked. |
| 0.3 [DS-01] | ✅ done | Visual freeze: `aa-visual.spec.ts` at 1440/390/320 for eight screens, plus `run.py e2e-visual` that runs it inside the pinned Playwright 1.56 Linux container against host servers, so baselines compare locally on Windows; local before/after snapshots are git-ignored until the P1 baselines are committed; a small PR to `main` adds the CI regeneration job first. (the CI regeneration job is committed locally; its PR to `main` waits for the first push) |
| 0.4 | ✅ done | Ratchet tests only: routes without `response_model` may only shrink; layer-boundary imports may only shrink; CSS hex/dead-selector budgets may only shrink. (OpenAPI types, pyright and the coverage floor move to P6 step 6.0.) |
| 0.5 [S03] | ✅ done | Quick fixes: one `register_all()` for job handlers (the CLI misses the video handlers), unknown job kinds dead-lettered, `settings.job_max_attempts` honoured, bounded read-aloud upload, complete owner export, `scripts/check_model_lifecycle.py` wired into the release script and preflight so every release warns about retiring deployments; read-aloud points per owner decision O1. |
| 0.6 [S04, part] | ✅ done | `DomainError(code, status, persist)` base, one set of exception handlers, `code` added to error bodies; existing status codes unchanged; web copy for codes waits for the catalogue (P2 step 2.8). |
| 0.7 [S05] | ✅ done | One stages/skills registry; one storage-key module (fixes topic and conversation drafts surviving sign-out); proxy forwards the abort signal and applies a timeout to response headers only. |
| 0.8 [S06, part] | ✅ done | TanStack Query provider and typed query keys; no mass migration of readers. |
| 0.9 [X01] | ✅ done | Characterisation tests pinning what the engine must preserve (answer-key withholding, completion rules, final-check isolation) and content-pool invariants per stage, including the sentence-frame collision check that step 3.3 relies on; extract `_persist_topic_result`. |

### P1 — Design system and the five-destination shell (first visible change) — ✅ Done locally (not yet released)

| Step | Status | What changes |
|---|---|---|
| 1.1 [DS-02] | ✅ done | Delete confirmed-dead CSS by selector under a usage test; live rules inside those ranges stay. |
| 1.2 [DS-03] | ✅ done | Cascade layers and `app/styles/tokens.css` with compatibility aliases reproducing today's values: zero pixel change by local comparison; a unit test asserts AA contrast for every token pair. |
| 1.3 [DS-04] | ✅ done | Base layer: one focus ring, 12 px type floor, z-index scale, 44 px targets. |
| 1.4 [DS-05 + part of DS-14] | ✅ done | Palette flip through tokens: brand blue for actions; one hue per skill and section (reading blue, listening teal, speaking violet, writing orange, words amber, stories rose, progress green); green/red reserved for feedback; sage-green leftovers mapped; the four literal-colour files (library, topics, phrase-audio, learning-agents/-tools) tokenised now so the screens the owner looked at change colour in this phase. |
| 1.5 [DS-06] | ✅ done | Primitives: Button, Card, Badge, Notice, IconTile, Field, Skeleton, EmptyState; `lucide-react` behind `Icon`; dev-only gallery page. |
| 1.6 [DS-07] | ✅ done | Motion (press, lift, pop, 4 px shake, pulse, shimmer, flip, burst) with reduced-motion fallbacks; Dialog, Toast, Tabs, Stepper; optional answer and goal tones through Web Audio (no asset files, a setting, off under reduced motion). |
| 1.7 [J05 + DS-08] | ✅ done | Shell split and five destinations in one pass: Vandaag, Leren, Verhalen (stories + videos), Spreken (conversations, missions, speech studio), Woorden; progress and settings in the sidebar and profile menu; plain Dutch labels now, glosses in 2.4; coloured section identity; e2e nav assertions updated in the same step; the navigation guard still wraps every link. |
| 1.8 [DS-09] | ✅ done | ProgressRing, ProgressBar, four-segment SkillMeter, Cover, a small inline-SVG illustration set; applied where data exists (goal fill in the streak ring). Baselines regenerated and committed at the end of P1. |

### P2 — The start: profile, onboarding, one level, glosses, copy — ✅ Done locally (not yet released)

| Step | Status | What changes |
|---|---|---|
| 2.1 [J01] | ✅ done | `learner_profiles` (migration 0008), `GET/PATCH /me` with `features`, `POST /me/onboarding` (pre-queues episode 1 at the chosen level), dev/test-only profile reset; `stories.default_stage` reads the profile. |
| 2.2 [J02 + S07, part] | ✅ done | Web profile client; support language synced with the server; e2e auto-fixture that onboards and sets glosses off; server-side prefetch of `/me` with skeletons, disabled under e2e so browser mocks keep working. |
| 2.3 [J03] | ✅ done | One level everywhere (competing selectors removed); learning preferences in settings. |
| 2.4 [J04 + DS-10] | ✅ done | Gloss layer: typed copy catalogue (every key needs nl, en, fa), `UiText`, `gloss.css`, glosses on shell and navigation per the tab rule; a second axe and overflow pass with glosses on and nl-fa-en at 1440/390/320. |
| 2.5 [J06] | ✅ done | Onboarding at `/welkom` with `FirstRunGate`: support language, plain-language self-placement (sets a starting stage, never passes anything), goal, "how Taalstudio works", a first activity while episode 1 is written (alphabet at pre-A1, starter words otherwise; replaced by an engine session in P5). |
| 2.6 [J07] | ✅ done | Interface copy on "je"; one honesty chip and an "about the content" page instead of repeated notices; empty states with one action; developer hints hidden from learners. |
| 2.7 | ✅ done | Adopt `UiText` on the existing daily-loop screens (episode reader, video player, word review, missions, speech studio) with a ratchet test on hard-coded Dutch JSX strings; Persian glosses ship off by default until the owner reviews each batch (O2). |
| 2.8 | ✅ done | Web error copy from error codes, now that the catalogue exists. |

Owner action in this phase: run the voice spike (P8 step 8.0); it needs only Azure sign-in and the SSE check from 0.0.

### P3 — Exercise engine core and topic sessions (the practice fix) — ✅ Done locally (not yet released)

| Step | Status | What changes |
|---|---|---|
| 3.1 [J10] | ✅ done | Activity service per the shared contract (migration 0009); the eleven `add_points` calls move over with unchanged values; one Brussels-day helper; read-aloud and question-point rules per O1. `record_activity` reports when an award crosses the day's goal, and the screen that earned it plays the goal tone (moved here from Today by the review of 1.6, where it could not fire). (the question half of O1 moved to 4.2) |
| 3.2 [X03] | ✅ done | Tolerant comparison (case, punctuation, diacritics, optional article, near-miss "almost", token diff) and a generic read-aloud comparison endpoint with no score. |
| 3.3 [X04] | ✅ done | Engine core (migration 0010): sessions, items, mistakes, suggestions; create/answer/skip/finish API; kinds: choice (4 options for vocabulary; authored comprehension keeps its options, shuffled), cloze by choice, odd one out. Rules added by the red team: a distractor is illegal when its own example sentence equals the target with it filled in (at A2–B1 every sibling shares the frame); if fewer than three legal distractors remain, cue with the support-language translation or drop cloze; an ungraded "nieuwe woorden" intro card before first exposure; no mistake row for a word the learner has not met; a content gate that generates sessions for all twelve stages and enables only stages above a variety threshold. |
| 3.4 [X05] | ✅ done | Kinds: match pairs, de/het sort, typed cloze, typed recall, sentence builder, sentence ordering, flashcard; "my answer was also right" override that never affects completion; a non-red "bijna" outcome. |
| 3.5 [X06] | ✅ done | Audio kinds with cached speech (a cache hit costs no allowance): listen-and-choose, dictation, shadow (heard or not heard, shown in a neutral colour, never red). |
| 3.6 [X07 + DS-12] | ✅ done | Web kit: reducer-driven session runner, feedback bar, progress, summary, one `AnswerOption` with correct/incorrect/almost/reveal states; keyboard and screen-reader behaviour; `lang=nl` and autocapitalize off on typed inputs; a "report this exercise" control; match-pairs and de/het boards submitted whole; a measured p95 answer round trip of 300 ms or less locally and on Azure. |
| 3.7 [X08] | ✅ done | Remaining renderers, in two parts: 3.7a tap kinds (match pairs and de/het sorting submitted whole, tiles, ordering) and the gallery card with every option state (the flashcard is not planned in sessions, `blueprints.py`, so it has no renderer here; word review decides in 5.1); 3.7b typed kinds (inputs with `lang=nl`, autocapitalize, autocorrect and spellcheck off, the hint, "mijn antwoord klopt ook", the token diff), listen-and-choose with its sound, shadowing with the recorder. |
| 3.8 [X09] | ✅ done | Topic and lesson sessions with unchanged completion rules (first-attempt answers to the authored questions, 75 %); a missed authored question can be retried in a short new session; final-check content is never a source. |
| 3.9 [X10] | ✅ done | A topic starts with a session; the open speaking or writing task follows; option glosses hidden until answered; reused topics labelled as review. |

### P4 — Points for all practice, Today as one session, progress — 🔄 In progress

| Step | Status | What changes |
|---|---|---|
| 4.1 [S08] | ✅ done | First: `today_view` (read-only) plus idempotent `POST /today/prepare`; `GET /today` causes no writes; tests switch through one helper; `last_seen_at` throttled; commit-before-response scope per the 0.0 result. |
| 4.2 [J11] | ✅ done | Points for lessons, topics, missions, conversations and speech warm-up, from code-observable facts only; episode and video questions per answered (O1). |
| 4.3 [J14, API] | ⬜ to do | `GET /progress/summary` and `GET /progress/day`. |
| 4.4 [J12] | ⬜ to do | Learner snapshot and deterministic planner producing the `session` contract (warm-up and mistakes candidates included); `GET /today/ready`. |
| 4.5 [J13 + DS-11] | ⬜ to do | Today page as one guided session with one primary button, goal ring, labelled week strip, staged waiting card, ready notification, celebration (copy says what was done, never a level); goal expressed per O3. |
| 4.6 [J14, web] | ⬜ to do | Progress dashboard: streak calendar, four separate skill rings labelled as practice frequency, word strength buckets, "how do I earn points?". |
| 4.7 [J15] | ⬜ to do | Decision records, documentation, regenerated previews. |

### P5 — Engine everywhere, linear path and stage pages — ⬜ Not started

| Step | Status | What changes |
|---|---|---|
| 5.1 [X11] | ⬜ to do | Word review on the engine (typed recall mapped to SM-2, grade buttons kept as override); word suggestions from missed items; saving library words. |
| 5.2 [X12] | ⬜ to do | Today warm-up, "repeat your mistakes" (a mistake resolves only on a later Brussels day; two older correct refs re-asked), while-you-wait; planner lesson steps and onboarding's first activity re-pointed at engine sessions; done-ness read from exercise events. |
| 5.3 | ⬜ to do | New source: "Oefen met deze aflevering" after reading an episode (match pairs and listen-and-choose from the glossary, dictation and sentence builder from validated sentences; mechanical kinds only, labelled generated). |
| 5.4 [J08 + DS-13] | ⬜ to do | Linear path page: current stage large, one "Ga verder", a compact rail of twelve nodes on a connector (keeps `data-testid=curriculum-path` with twelve `li`). |
| 5.5 [J09 + X13] | ⬜ to do | Linear stage page with a lesson stepper and persistent next step; path lesson and grammar on the engine; practice answer keys no longer sent to the browser. |
| 5.6 [X14] | ⬜ to do | Retire the five duplicate multiple-choice renderers, VocabularyRecall and the alphabet quiz; hide Story Time duplicates; label reused word lists; flip word cards. |
| 5.7 [DS-14, part] | ⬜ to do | Move the screens no other track rewrites (missions, speech studio, videos, settings) onto primitives and delete their legacy CSS. |

### P6 — Agent platform and Azure model migration (cut over before 2027-01-31) — ⬜ Not started

| Step | Status | What changes |
|---|---|---|
| 6.0 [S02, rest] | ⬜ to do | OpenAPI export with generated web types, pyright on an include-list, coverage floor. |
| 6.1 [A-S01 + S10, part] | ⬜ to do | `LlmGateway` with one failure policy under the one-request call sites; the `call_claims` helper and database lock/idle timeouts so every new paid endpoint runs claim, call, settle without row locks across provider calls. |
| 6.2 [A-S02] | ⬜ to do | Retrying sites onto the gateway; attempt-accurate token accounting; the failure-policy decision record (allowance is no longer refunded after timeouts). |
| 6.3 [A-S03] | ⬜ to do | Remove LangGraph; plain pipelines; architecture test forbidding vendor SDK imports in domain code. |
| 6.4 [A-S04] | ⬜ to do | Model port v2, additive: `respond()` and `stream()` beside the untouched `complete`/`complete_once`; scripted fixture; Ollama tools. |
| 6.5 [A-S05] | ⬜ to do | Azure Responses adapter, stateless, strict output and tools, proven against the existing deployment; a probe command that records real payloads as test fixtures. |
| 6.6 [A-S09] | ⬜ to do | Side-by-side EU Data Zone deployments in Bicep, lifecycle check, daily and lifetime caps with a priced monthly envelope from the retail prices API, a paid probe recording a two-step tool run so run budgets are set from measured tokens (until then tutor and guide run single-call), eval gate on both candidate pairs, temperature probe on gpt-6. |
| 6.7 [A-S06 + A-S07] | ⬜ to do | Agent runtime (whole-run budget reserved and audited before the first call, step ceiling, read-only tools, propose tools validated by code, one repair, deterministic fallback, never replayed), tool catalogue over existing functions, snapshot extended with mistakes, grounding helpers, authored trilingual category notes. |
| 6.8 [A-S10 + S11] | ⬜ to do | SSE end to end (runner thread, built-in SSE, pure ASGI middleware, proxy forwards Last-Event-ID, browser helper with JSON fallback, `/health/stream`); job runner heartbeat, handler context, retention, deferral of video claims while a stream or voice session is live, API size parameters. |
| 6.9 [A-S08 + S13] | ⬜ to do | Metadata-only spans with an allow-list and a canary test; JSON logs with request and trace ids; eval harness on production prompts (fixtures in CI, Azure on demand); feature switches populated in `GET /me` and an e2e run with all flags on. |

### P7 — Agents and generated content — ⬜ Not started

| Step | Status | What changes |
|---|---|---|
| 7.1–7.2 [A-S11, A-S12] | ⬜ to do | **Tutor "Leg uit"** on a wrong exercise item, a writing correction, a comprehension question or conversation feedback: authored explanation first (free); grounded model answers for why-follow-ups (cap 3); a mini-drill from the generator; recurring categories remembered; hidden when the flag is off. |
| 7.3–7.4 [A-S15, A-S16] | ⬜ to do | **Conversation partner**: a short generated reaction before the authored anchor behind a contradiction guard with authored fallback; feedback after the conversation that must quote the learner's own turns. |
| 7.5 [A-S17] | ⬜ to do | Scenario scale-up: the 10-conversation cap lifted; generated scenarios through a code validator and the review queue, or on demand and labelled generated. |
| 7.6 | ⬜ to do | Optional open-turn partner mode per O5: the model proposes the next question through a propose tool, code validates vocabulary, facts and goals, authored fallback, gated on the reply-guard eval. |
| 7.7 [A-S13, A-S14] | ⬜ to do | **Study guide**: the model picks and orders candidate activities and reason codes; code pins mandatory steps and writes the reasons; cached per day; planner fallback. `POST /coach/plan` and its button stay until the flag is on in production, then retire in one commit. Automatic daily run per O4. |
| 7.8 [X15] | ⬜ to do | Model-judged exercise kinds: translate-to-Dutch and error correction from the learner's own corrections. |
| 7.9 [X16] | ⬜ to do | Generated items behind a validator and the review queue (migration 0016); a verb bank; the queue also lists the learners' exercise reports (admin only, without the learner: kind, ref, prompt, answer, reason, note), read until then with `python -m dlp.cli exercise-reports`. |
| 7.10 [A-S18] | ⬜ to do | Run visibility in the usage panel, export of the new tables, documentation. |

### P8 — Live voice conversation — ⬜ Not started

Go only if all ten spike criteria from the design are recorded and latency passes on the target small model, including: Belgian Dutch recognition on hesitant beginner speech, end-of-speech to first approved audio through both ingress hops, push-to-talk commit without server turn detection, forced per-response tool choice, Entra sign-in on the existing Speech account, whether reasoning effort can be lowered, a stream over 300 s through sign-in and ingress, cost per five-minute session. A relay container app (plan B) needs an owner decision revising the single-public-entry rule; otherwise a failed spike is a no-go.

| Step | Status | What changes |
|---|---|---|
| 8.0 [V-0] | ⬜ to do | Spike (run during P2) and go/no-go record in `docs/LIVE_VOICE.md`. |
| 8.1–8.3 [V-1..3] | ⬜ to do | Flag, settings, `voice_seconds`/`voice_tokens` allowances; `RealtimeVoice` port with a fixture adapter; session table, reservation and settlement. |
| 8.4–8.5 [V-4..5] | ⬜ to do | Turn director: a forced tool call proposes an interpretation that code validates with the partner's rules; the reply pass produces text, the guard gates each sentence, approved text is spoken through the TTS port; runtime and streaming routes with rollover every ~200 s. |
| 8.6–8.7 [V-6..7] | ⬜ to do | Azure Voice Live adapter (nl-BE transcription, Belgian voices, managed identity); local cascade adapter. |
| 8.8 [V-8] | ⬜ to do | Evidence (transcripts only, no audio stored, no pronunciation score), points, post-conversation feedback. |
| 8.9–8.11 [V-9..11] | ⬜ to do | Browser audio engine, live conversation UI with captions and glosses, push-to-talk default, fallback to the recorded-turn flow. |
| 8.12–8.13 [V-12..13] | ⬜ to do | Bicep and release wiring; hardening and cost reconciliation. |

### P9 — Hardening and close-out — ⬜ Not started

| Step | Status | What changes |
|---|---|---|
| [S10, rest] | ⬜ to do | Legacy paid sites onto claim, call, settle; provider failures unified on 503 with `code`, the web retry branch on `code` instead of status, four assertions and the decision record in one PR. |
| [S14] | ⬜ to do | Layering clean-up: break the curriculum/coaching cycle, shared writer loop for stories and videos, typed responses for the remaining routes. |
| [S15] | ⬜ to do | Split the surviving large components by view state; lazy-load heavy panels. |
| [S16] | ⬜ to do | Delivery: promote CI-built images by digest, app revisions through Bicep (what-if output checked by the owner first), storage lifecycle. |
| [DS-14 rest, DS-15] | ⬜ to do | Remaining screens onto primitives; retire the legacy CSS layer; dry-run dark tokens. |
| Data | ⬜ to do | Retention job for abandoned sessions, old tutor threads and writing reviews; a learner-facing delete for those items; retire the classic receptive practice branch; jti replay check. |
| Docs | ⬜ to do | Refresh ENGINEERING, ARCHITECTURE_WALKTHROUGH, GO_LIVE (data paragraph: writing submissions and tutor threads are stored), STATUS, VERIFICATION. |

## 10. Next steps in detail

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

## 11. Release gate (end of every phase)

One pull request to `main`; rehearse the phase's migrations on a restored copy of production; take a database backup and record the current image digests; release migration-first; run `scripts/verify_live.py`; rollback is forward-only once the migration head moves. The first-run redirect and the new Today page ship behind an environment switch so the owner can turn them on after seeing them live.

Release with `bash scripts/deploy_current.sh` from WSL with a signed-in `az` (clean tree, green main CI for the SHA; runbook `docs/GO_LIVE.md`). No gate has run yet: nothing is pushed.

## 12. Owner decisions (defaults the plan takes if not told otherwise)

| Id | Decision | Default |
|---|---|---|
| O1 | Non-punitive points: episode and video questions pay per answered instead of per correct; read-aloud pays any attempt with recognised speech instead of a 50 % threshold | Adopt both: read-aloud in 0.5 (D-23); questions per answered in 4.2 (D-34) |
| O2 | Persian and English interface glosses are written during implementation and unreviewed; who checks them? | Persian off by default until reviewed; English on |
| O3 | Daily goal: state it as the day's session length (kort / gewoon / stevig, ring fills against the session's points) or keep a point target scaled to the planner (about 30/50/80) | Session length |
| O4 | May the study guide make one automatic paid run on the first Today visit each day? | Off; manual refresh button |
| O5 | Partner: reaction-only, or add the open-turn mode (7.6)? | Reaction-only first; 7.6 after the eval |
| O6 | Azure: accept EU Data Zone processing (anywhere in the EU, not only West Europe); approve daily and lifetime caps with the priced monthly envelope; request quota | Needed before 6.6 |
| O7 | Who judges Dutch correctness of generated explanations, reactions and scenarios? | A fluent reviewer; otherwise the flags stay off |
| O8 | Voice: go, plan B (public relay, revises single-public-entry), or no-go after the spike | No-go unless criteria pass |
| O9 | Streak: keep "a missed day resets" or allow one rest day per week | Keep as is |

Recurring owner tasks: regenerate and review screenshot baselines after each visible step (local container run, then CI); approve generated comprehension items in the review queue; a first-week comparison of recorded usage with Azure billing; the phone check.

## 13. Rules consciously revised

Each becomes a new numbered entry in `docs/DECISIONS.md` (after D-22), written in the step that changes the behaviour.

| Existing rule | Revision | Step |
|---|---|---|
| D-19: points only for story and word actions; fixed goal of 20 | Points for every kind of practice; still reward doing, never judge Dutch; goal per O3. Word bank still fills only by the learner's choice (suggestions offered) | 3.1, 4.2 |
| D-20: read-aloud points once per paragraph at 50 % recognised | Any attempt with recognised speech (O1); the no-score rule extends unchanged to shadow items and the generic endpoint | 0.5, 3.5 |
| "Interface is in Dutch"; "restrained navy/blue palette"; "support tools add no main navigation" | Gloss layer under Dutch chrome; per-skill colour system; five destinations with a Spreken hub | 1.4, 1.7, 2.4 |
| Recall rounds are self-assessed | Typed recall is checked by code; self-assessment remains only as an override | 5.1 |
| Practice keys travel with the stage view | Practice answers withheld until answered, like the final check | 5.5 |
| LEARNING_AGENTS: no tool loop; coach reorders three; replies authored only; one call per turn; ten pilots | Bounded tool loops over read-only tools plus code-validated proposals; a guarded generated reaction; 1–400 scenarios | 6.7, 7.3, 7.5, 7.7 |
| "Reading the plan makes no model call" | One bounded guide run per day only if O4 says yes | 7.7 |
| D-12 failure policy and LangGraph graph; D-12/D-13 failed turn is 502 | One conservative policy for every paid chat call (audio and video seconds keep D-22); plain functions; failed turn 503 with `code turn_failed` | 6.2, 6.3, P9 |
| GO_LIVE: Chat Completions, JSON mode, regional Standard model | Stateless Responses API on EU Data Zone deployments | 6.5, 6.6 |
| Usage day is UTC while the learner day is Brussels | One learner-day helper for points; allowances documented as UTC | 3.1 |
| Data: no learner free text stored beyond attempts | Writing submissions, tutor threads, mistake rows, exercise answers and transcripts are stored, exported, deletable and retained per P9 | 3.3, 7.1, P9 |
| LEARNING_AGENTS: no tool loop; coach reorders three; replies authored only; one call per turn; ten pilots, six actions, three goals | Bounded tool loops over read-only tools plus code-validated proposals; a guarded generated reaction (two single requests per turn when on); 1–400 scenarios, turn limit per row | 6.7, 7.3, 7.5, 7.7 |

Rules that stay untouched: models propose and code decides; reserve before every paid call; no pronunciation score, overall level or certificate; typed input never counts as speaking; final-check withholding; generated and unreviewed content stays labelled; the API is never public; telemetry carries no prompts, text or identifiers; the accessibility gate.

## 14. Risks and verification

### Risks to watch

- **Test churn is deliberate.** Navigation names change in P1, five e2e specs are rewritten in P3–P5, and the P7 gate "earlier specs pass with flags off" admits the listed deletions only. Each surface keeps at least one test against the real API.
- **Content is still thin.** Twelve mechanics run over the same bank until 7.9 (the same 500 words serve three consecutive stages); the content gate in 3.3 keeps weak stages off and reused material is labelled as review. Topic completion stays guessable (two options) until generated options are approved.
- **Point inflation.** Values live in one rules table and are tuned after a week of real use.
- **Local agent quality.** `llama3.1:8b` tool calling is unreliable; local agent runs often end in the deterministic fallback. Behaviour is verified on scripted fixtures in CI and by the eval run on Azure.
- **Generated Dutch reaches the learner unreviewed** in tutor explanations, partner reactions and scenarios; guards catch ungrounded quotes and contradicted facts, not unnatural Dutch (O7).
- **Streaming behind the real stack** (Next compression, sign-in sidecar, ingress) is checked by `/health/stream` in e2e and in the live verifier; every stream has a JSON twin.
- **Model retirement date** is hard; the migration has a dated gate and the lifecycle check warns from 0.5 on.
- **Voice** depends on recognition quality and latency measured only in the spike; the 0.25 vCPU single replica also runs ffmpeg jobs, so the spike measures lag against a video job.
- **Single replica.** The job loop, the voice registry and the replay check assume one API replica.

### Verification (as run in this repository)

After every step: `make lint`; `python scripts/run.py test`; `cd apps/web && npm run test:unit` (and
`test:component` from 0.2); `python scripts/run.py e2e`; `run.py e2e-visual` when a baselined screen
changed. The per-phase acceptance checks from the approved plan follow. `docs/STATUS.md` has not been updated since 2026-10-02; step 4.7 refreshes it. On this Windows machine `make` is not installed: run the lint commands of §15.

### Verification and per-phase acceptance checks (approved plan)

Environment first: `python scripts/run.py setup`, then `services`, `migrate`, `fixture` (this worktree has no `node_modules` or `.env`).

After every step:

- `make lint` (ruff, eslint, tsc) and, from 0.2 on, `npm run format:check`.
- `python scripts/run.py test` for the API suite on the `_test` database with fixture providers.
- `cd apps/web && npm run test:unit` and, from 0.2 on, `npm run test:component`.
- `python scripts/run.py e2e` (Playwright with axe at 1440/390/320 and the no-overflow check) and `run.py e2e-visual` when a baselined screen changed.

Per phase:

- **P1:** zero pixel diff through 1.1–1.3 by local comparison; intended diffs only afterwards; token contrast test green; shell shows five destinations and section colours at 1440, 390 and 320.
- **P2:** as a brand-new learner in the browser, `/` redirects to `/welkom`; after onboarding, Today, path, stories and videos show the chosen level; glosses appear under labels at A1 (English on, Persian per O2) and disappear at B2; the gloss-on nl-fa-en axe pass is green.
- **P3:** a topic session shows instant per-item feedback with the "almost" and "not heard" states, re-asks missed items, ends with a summary and points; no answer key in any payload before answering; final-check content never appears; the p95 round trip is at or under 300 ms.
- **P4:** completing a topic, a mission step and a conversation each moves the goal; `GET /today` causes no writes.
- **P5:** word review, warm-up and the stage lesson all run on the engine; the old renderers are gone and the pinned specs pass through the adapters.
- **P6:** the one-request tests pass untouched; a scripted agent that keeps calling tools stops at the step ceiling; closing a stream settles usage exactly once; the canary marker appears in no exported telemetry; the eval gate passes on the new deployment before the switch.
- **P7:** with every agent flag off, earlier specs pass except the listed deletions; with flags on, tutor, partner and guide pass on scripted fixtures; the reply-guard eval rejects every seeded contradicting reply.
- **P8:** spike numbers recorded; fixture sessions run in CI; a live five-minute session settles seconds and tokens that reconcile with Cost Management.

## 15. Running and verifying on this machine

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

## 16. Open items for the owner

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

## 17. Appendix: what each finished step delivered

The Progress table of `docs/ROADMAP.md`, as it stands. Reviews from P2 on are listed after their steps; P0 had no review, and the three P1 reviews are commits a0bea19, 244020d and c723e2b without rows.

| Step | State | What was delivered |
|---|---|---|
| 0.0 | done | `docs/plan/CHECKS.md`; the Windows-only UTF-8 test failure fixed on the way |
| 0.1 | done | `docs/plan/*.json`, `CODE_REVIEW.md`, `docs/ROADMAP.md` |
| 0.2 | done | Format commit + tooling commit; 96 e2e, 27 unit, 1 component test green |
| 0.3 | done | 24 baselines rendered in the Playwright container (`run.py e2e-visual`), deterministic on re-run; CSS ratchet; shared story fixtures |
| 0.4 | done | Ratchets: 61 untyped operations frozen, import-boundary allowlists exact, `alembic check` in CI |
| 0.5 | done | `register_all()`, dead-lettered unknown kinds, lease sweep, bounded read-aloud upload, complete export, model lifecycle check (release + preflight), D-23 read-aloud points |
| 0.6 | done | `DomainError` base with stable `code`, one set of handlers, `code` in every error body; status codes unchanged |
| 0.7 | done | `lib/domain/registry.ts` (stages, skills), `lib/client/storage.ts` (keys + sign-out sweep), proxy forwards aborts and bounds time-to-headers (504 `upstream_timeout`), `x-proxy-error` marks proxy-made answers |
| 0.8 | done | TanStack Query provider, typed keys, `useUsage` and `useCurriculumCatalog`; UsagePanel and CurriculumProgress read through the cache |
| 0.9 | done | `test_practice_contracts.py`, `test_content_exercise_pool.py` (recorded per-stage facts incl. frame collisions at A2–B1); `_persist_topic_result`, `_persist_core_practice` extracted |
| 1.1 | done | 646 dead lines removed from design.css, globals.css and learning.css under `css-usage.test.mjs` (every selector must appear in a component or a dynamic class pattern); the 24 screenshot baselines compare pixel-identical |
| 1.2 | done | `app/styles/layers.css`, `tokens.css` (ramps, semantic tokens, `[data-accent]` sets, compat aliases with today's effective values), `reset.css`; the ten legacy files wrapped in `@layer legacy`, their `:root` blocks removed; `design-tokens.test.mjs` contrast gate; css-guard covers `app/styles`; baselines pixel-identical |
| 1.3 | done | `app/styles/base.css`: element defaults and type scale from tokens, one `:focus-visible` ring, skip link at `--z-skip`, `.visually-hidden`; legacy focus, body, heading and helper rules removed; 59 sizes under 12px raised to `--text-xs`; z-index literals tokenised; six controls lifted to 44px; `design.spec.ts` checks the skip link stacks on top and the ring colour on buttons, links and text fields; baselines regenerated (first visible change) |
| 1.4 | done | every colour literal in the ten legacy stylesheets (372) is a token (review fixes of 7 Oct: writing indigo, words plum, progress neutral; deeper cover stops; recording tokens; muted inks; keyword colours; wider ratchets); compat aliases point at semantic tokens; `lib/design/identity.ts` + `data-accent` replace the four palette classes (skill tiles, lesson sections); brand mark and app icon in brand blue; covers from the ramps; D-24; colour budgets at zero; baselines regenerated |
| 1.5 | done | `components/ui` (Button/ButtonLink, Card, Badge, Notice, IconTile, Field+Input/Select/Textarea, Skeleton, EmptyState) over `app/styles/ui/*.css` in `@layer components`; legacy bare rules for .button/.card/.label/.error/.icon-tile/.empty-state/.information-callout/.practice-*/.path-loading deleted (css-usage: one bare definition per primitive); `lucide-react` 1.52.0 behind `Icon` (52 names); `/dev/ui` gallery outside production with axe/overflow spec and a baseline |
| 1.6 | done | `app/styles/motion.css` (pop, shake 4px, pulse, shimmer, rise, flip, burst, dots as `data-anim`, press/lift) with explicit reduced-motion states; `lib/client/motion.ts`; Dialog (native, in the frame), ToastProvider in the shell, Tabs, Segmented, Stepper; shimmer on Skeleton, pulse on recording states, dots on the writer; optional Web Audio tones for answers and the daily goal (a device preference in Instellingen, silent under reduced motion; the goal tone waits for 3.1); gallery and spec extended |
| 1.7 | done | `components/shell` (AppShell, nav.ts, SectionTabs) and `app/styles/shell.css` replace the old shell; five destinations Vandaag, Leren, Verhalen (+ video's), Spreken (hub: korte gesprekken, praktijkgesprekken, spraakstudio), Woorden; Voortgang and Instellingen as rooms in the sidebar and behind the profile button at every width; coloured section identity via `data-accent` on the workspace; `navigation.spec.ts` + `nav.test.mjs`; nav assertions in design, resilience and videos specs updated; baselines regenerated |
| 1.8 | done | ProgressRing (goal fill inside the streak ring, still `img` 'N dagen op rij'), ProgressBar (goal bar, finished levels, topic progress), SkillMeter (four separate segments on every stage card), Cover (the six pairs), five inline illustrations; seven loading boxes are SkeletonPanels with a status label; three plain-text empty states are EmptyStates; gallery extended; `progress.test.mjs`; baselines regenerated at the end of P1 |
| 2.1 | done | migration 0008 `learner_profiles`; `domains/profile` (ensure, view, update, set_stage, reset) and `onboarding.complete` (stores the choices once, syncs the serial, queues episode 1); `GET/PATCH /me` with `features: {}`, `POST /me/onboarding`, `POST /me/reset` outside production; `stories.default_stage` reads the profile, and a level set through `PATCH /me` or `/stories/level` moves both the profile and the serial; explicit nulls for required fields are 422; profile in the export and the cleanup tables; `test_profile.py` |
| 2.2 | done | `lib/client/profile.ts` (`useProfile`, `useUpdateProfile`, `completeOnboarding`, key `['me']`), `profile-sync.ts` (`reconcileMode`: server wins, a server without a value adopts the device once), `LanguageProvider` writes every change to the server and keeps the cached profile in step; the root layout prefetches `/me` on the server through the proxy's identity and assertion path (1.5 s cap, null on any failure) and seeds the query cache, so the first paint knows the profile; `tests/e2e/fixtures/test.ts` resets and onboards the learner through the browser page before every spec (all specs import it; the visual container resolves localhost only inside Chromium); `curriculum.spec` asserts the server mode after reload |
| 2.3 | done | the coach and the serial read `profile.stage_id` and the videos default to the serial's level, which follows it (the coach select, the Today level select and the `practice-stage` device key are gone); a learner who already reads the serial keeps its level when the profile row is created; the path marks the profile stage current; `LearningPreferences` in Instellingen: level with a plain-language name, daily goal, support language, glosses, and a move-up offer when a higher stage is earned; `settings.spec.ts` |
| 2.4 | done | `lib/ui-copy.ts` (every key nl/en/fa, placeholders checked, 'je' enforced), `components/ui/UiText` with tiers chrome/guide/always, `lib/client/gloss.ts` (`glossLevelFor`: auto = everything to A2, guides at pre-B1/B1, nothing above), the language context carries the level from the profile; the sidebar and bottom tabs show one gloss line (Persian when selected), hidden under 360px, and the content and toasts keep clear of the taller glossed bar; `gloss.spec.ts` runs axe, overflow and the bar clearance in nl-fa-en at three widths; the Persian glosses await a fluent check (O2) |
| 2.5 | done | `/welkom` in a bare frame (no sidebar or tabs): support language shown in all three languages, four plain-language starting points or any stage (never passes anything), a reason and kort/gewoon/stevig, then `POST /me/onboarding`, "Zo werkt Taalstudio" in four cards, and the first episode's progress beside a first activity (the alphabet at pre-A1, otherwise eight library words the learner may tick to keep, saved with `source_kind: library`, and a recall round); `FirstRunGate` sends a learner without `onboarded_at` there, exempts /welkom, /settings, /over and /dev and stays open when the profile is unknown; behind `FIRST_RUN_GATE` (on outside production, off in production until the owner turns it on); Instellingen links to the explanation; `onboarding.spec.ts` walks the real flow, `first-run-gate.test.tsx` and `first-run.test.mjs` pin the gate |
| 2.1–2.4 review | done | adversarial review of 9 Oct (45 findings, 35 kept): the move-up offer follows the highest passed check at or above the current stage and names the stage earned (`earned_stage_id`); the daily goal from the profile drives Today, the day rows and the goal dots; `stated_goal` is a closed list; reset moves the serial too; the export carries the profile's switches; the support language uploads only an explicit device choice, retries a change the server never confirmed, saves in order and renders the server's value first; profile saves are optimistic and ordered; passing a check refreshes the profile and the path; the coach waits for the profile; inline glosses keep a real space; new API, unit, component (offer, prefetch) and e2e (gloss off, six glossed screens) tests |
| 2.6 | done | interface Dutch on "je" (missions, banner, speaking, writing, listening, speech studio, feedback, the coach's reasons on the API) with `je-form.test.mjs` and a coach test refusing "u"; practice phrases keep their register; `HonestyChip` (generated, video, unreviewed, feedback, voice, check) replaces the course notes on Today, the reader, the player, the video library, the path, the check, the lesson, the alphabet and the feedback panel, opening an explanation in the support languages that links to `/over` (five sections); model names, check counts, the run command and the recording format only outside production (`DeveloperDetailsProvider`); Woorden, video's and the practice history have empty states with one action; `honesty.spec.ts`; D-26 |
| 2.7 | done | five screen batches in `lib/copy/` (episode, video, words, missions, speech) registered with the catalogue; the reader, the player, word review, the missions (catalogue, shell, steps, feedback, help ladder) and the speech studio render their interface text through `UiText`; `dutch-text.test.mjs` counts Dutch still written into components (JSX text and spoken attributes) against a per-file budget that may only go down; Persian per batch behind `lib/copy/review.ts`, every batch off until the owner reads it at `/dev/copy` (English stands in, Persian-only learners see Dutch alone); a translation check against the Dutch corrected 50 English and Persian glosses |
| 2.8 | done | learner-reachable conflicts carry a code on the API (`episodes_busy`, `videos_busy`, `not_ready`, `already_answered`, `session_closed`, `turn_limit`, `no_retry`, `in_progress`, `evidence_short`, `paid_not_approved`); `errorFor` maps code, then status, to `errors` copy and `errorCopy` adds a screen's own fallback; the reader, the player, Today, both libraries, word review, the mission shell and steps, feedback, the speech studio and the usage panel no longer show the API's English sentence; failed episodes and videos say why by failure code; `errors.test.mjs` fails when the API sends a code without copy |
| 2.5–2.8 review | done | adversarial review of 9 Oct (31 findings, 27 kept): the first-run gate waits while the profile loads and onboarding re-stamps a still-queued first episode with the chosen level; the welcome keeps a goal and reason set earlier, says when another tab already finished it, words the start step from the episode's real state, stops claiming progress after the poll limit, has singular word forms, and shows Persian sentences only once reviewed (the language's own name stays); error copy claims "Je invoer blijft staan" only where the input stays, loads keep their own "kon niet worden geladen", the API's 502 is worded by the screen, a recording nobody heard says so; validator output, provider and voice names only for developers; the video chip and /over say translations come from the model; the chip label, the mission labels (help ladder, feedback, questions) and "Jij" go through the catalogue; whole sentences in the reader; the remove button's name starts with its visible label; a failed profile save rolls back to what the server holds; /over sits in the settings room; the hard-coded-text ratchet uses the TypeScript parser and an exact budget (recounted at 780) and the je-form test reads single words and text beside expressions; a goal changed mid-day flipping that day's dot is fixed in 3.1 by storing the day's goal |
| 3.1 | done | `domains/activity` (day, rules, models, service) and migration 0009 (`activity_events` unique per learner, kind and dedupe key; `learning_days` + `goal_target`, `exercise_items`, `exercise_sessions`; existing days backfilled as one `legacy` event each); the eleven story, video and word awards go through `record_activity` with unchanged values (question points stay per correct answer until 4.2; read-aloud already pays any recognised attempt, D-23); the day stores its goal and a goal change updates today, so a past dot matches what Today showed; the award that crosses the goal returns `goal_reached`, and the shell plays the goal tone with a toast on any screen; the events are in the export and both cleanup lists, and a test now requires every learner-scoped table in both; `test_activity.py` (two requests at once award once, retries, daily scope across Brussels midnight and both DST changes, sums, goal crossing); D-27 |
| 3.2 | done | `domains/exercises/compare.py`: fold, accent-blind matching with an `accents` note, article policy (missing forgiven or required, wrong de/het `almost`), optimal-string-alignment slips by word length with a real-word guard, one missing or extra word in longer sentences, a token diff, the kindest of several accepted answers; `domains/speech/compare.py` shared by the story reader and the new `POST /speech/read-aloud` (typed response without a score, recording not kept, no points, allowance and outage answer with codes); the story reader's own not-ready conflict carries `not_ready`; `test_exercise_compare.py` (the specification table) and `test_read_aloud_generic.py` |
| 3.1–3.2 review | done | adversarial review of 10 Oct (16 findings, 11 kept): `activity_events.request_id` takes the 80 characters the request bodies allow (an 80-character id failed with a 500); the goal crossing is kept with its event and repeated when the same request is retried, the goal tone waits for the screen's answer tone and plays once a day, and a read-aloud upload finishes when the learner leaves the episode; `POST /speech/read-aloud` refuses text without words (`nothing_to_read`) before counting audio; tolerant comparison: articles only for term items (a sentence's first word counts), negations and numbers never slips, only function words may be missing or extra, the lexicon read without articles and accents, quotation marks, apostrophes and hyphens forgiven, a split compound is a slip, changed words paired with their closest counterpart, the closest accepted answer shown |
| 3.3 | done | migration 0010 (`exercise_sessions`, `exercise_items`, `learner_mistakes`, `word_suggestions`); `domains/exercises` pool, generators, blueprints, graders, mistakes, taxonomy (the twelve categories) and service; `POST /exercises/sessions` (seeded, idempotent, resumable, `fresh`), `GET`, answer, skip, finish with typed responses; kinds choice (four options for words, three directions; authored questions keep their options, shuffled), cloze by choice, odd one out (pre-A1 to B1) and the ungraded intro card; the frame rule with the translation cue or no cloze; no mistake row for a first encounter; two attempts, a miss comes back once at the end; 1 point per closed item and 5 per session of five (`exercise_item`, `exercise_session`); missed words offered as suggestions; the content gate (200 choice words and two kinds; every stage passes and is recorded); export and both cleanup lists; `test_exercise_generators.py` (200 sessions per stage) and `test_exercises_api.py`; D-28 |
| 3.3 review | done | adversarial review of 10 Oct (29 findings, 23 kept): an item earns its point with its first real answer, so an early finish no longer pays right answers only, and the session bonus needs five answered items (not skips); a retried finish repeats its points; the export hides an item's ref until its answer was shown; audio skip reasons are refused on items without audio; an odd-one-out mistake names the chosen word; every cloze shows its translation (siblings such as colours fit the same blank), the cue check also finds the word written as two words or without its hyphen, and no cloze shows another form of its answer; one cloze per example and sentence frame, and no cloze answer in another cloze; odd one out keeps one word class, leaves out the group's theme (`themes.py`) and the word that names the topic; no definition item contains its word; a five-item session no longer introduces a word it never asks; items about one word are spread wherever possible; the content gate also needs 150 distinct example sentences and 50 items per kind, and records frames and new words per stage; create answers 201; the concurrency and requeue tests now fail without the behaviour they name |
| 3.4 | done | kinds `cloze_typed` and `typed_recall` (judged by `compare.py`, a hint on request, a synonym of the stage right too), `flashcard` (self-assessed, for word review), `match_pairs` and `de_het` (boards submitted whole, judged per part, three de and three het, up to pre-C1), `sentence_builder` (tiles or chunks; `sentences.py` takes only sentences that open with their subject, word tiles without commas, en/of or movable words) and `sentence_order` (Story Time paragraphs: pre-B1 and from pre-B2); `POST .../override` ("mijn antwoord klopt ook") on typed answers and built sentences: closes as accepted, removes the mistake row, never completes anything; `almost` closes without a mistake; a mistake per missed pair or noun; up to two boards per session; retries reshuffle pieces, never into the solution; the availability matrix per stage recorded; `test_exercise_typed_kinds.py`, `test_exercise_sentences.py`; D-29 |
| 3.4 review | done | adversarial review of 10 Oct (25 findings, 22 kept): word tiles only from sentences that open with their subject, without en/of and without the movable adverbs and time phrases the first filter missed, and a built sentence writes no mistake; de/het leaves out nouns that take both articles; the first piece keeps its capital only for a name; typed recall accepts another word only with the same English and Persian gloss and word class, never runs where the meaning spells the word, and a word copied from the cue is not a slip; boards are built from the words the session keeps (a new word on a board is introduced), an ordering paragraph shares no sentence with the session's examples, and the closing sentence put first is almost; retries never show a board solved (checked per kind, by text); a while-you-wait session has no typing; attempts keep the learner's answer and the export carries it with `overridden_at`; the summary names each missed word of a board; the docs say what almost is and where ordering runs; the tests now fail without the behaviour they name |
| 3.5 | done | `speech.service.synthesize_cached` (course text per provider and voice under `tts-cache/`, a hit costs no allowance); kinds `listen_choose`, `dictation` (typed, judged tolerantly; the word alone at pre-A1) and `shadow` (heard or not heard, recording not kept, no score, no mistake, heard speech earns the point); `POST .../audio` (from the cache) and `POST .../recording` (transcribed before the session row lock); speech planned only while 60 audio seconds are left, no dictation or shadowing in a while-you-wait session (listen-and-choose is tapped); audio skips close without a miss; the typed-route ratchet counts a declared audio body as typed; `test_exercises_audio.py`; D-30 |
| 3.5 review | done | adversarial review of 10 Oct (26 findings, 17 kept): recordings of one item are handled one at a time (an advisory lock before anything is read), so a retry never pays for a second transcription, and a refusal after the transcription is returned with its usage kept (`DomainError.persist`, honoured by `_run`; `session_closed` when the session closed meanwhile); simultaneous misses of one sound are synthesised once (double-checked advisory lock); a dictated sentence stands nowhere else in the session (intro card, word cards, boards), else the dictation becomes another kind; a dictation missed elsewhere in the sentence is no mistake or suggestion for the word; a listened noun is offered among nouns of its article; the pool keeps the spoken sentences (no name in a dictation, no quotation, counts recorded) and the word count is counted as answers are compared; a take not heard may be tried once more at once; a skipped shadowing closes and is not listed as missed, and heard counts as right the first time; lesson, topic and final-check listening come from the speech cache; the docs say which locks the speech call holds and that listen-and-choose runs in a while-you-wait session |
| 3.6 | done | web kit: `/oefenen` in focus mode with `ExerciseSession` (pure reducer, request ids kept per answer, a 409 reloads), `AnswerOption` (native radio, `data-state` with icon and words, no glosses before the answer), the feedback bar, the summary with word-bank suggestions, a report dialog; keys 1 to 4, Enter and Escape, focus to each question and then to Verder, a polite live region, tones only after the verdict; the `exercise` copy batch (Persian unreviewed); API `kinds` on create (the runner asks only for choice, cloze by choice and odd one out until 3.7) and `POST .../items/{id}/report`; "Oefen terwijl je wacht" on Today's pending card; answer round trips checked at p95 <= 300 ms through the proxy (e2e, Playwright request timing); on Azure `verify_live.py --measure-answers` (script wall-clock time over one kept-alive connection) is an owner action, result pending; component, unit and e2e tests (axe and overflow at 1440/390/320 on the intro, question, feedback, report, exit and summary states); moved to 3.7: typed-input attributes, boards submitted whole, the gallery card |
| 3.6 review | done | adversarial review of 10 Oct (35 findings, 33 kept): no stale error above a saved summary, "Nog een oefening" resets and shows its own failure, a 409 on finish shows what the server holds; focus goes to a missed item that comes straight back, returns to the opener when a dialog closes (both kept mounted), and lands on the stopped-elsewhere notice; the number keys work on AZERTY and Persian keyboards, only while focus is in the item, and move focus to the option; Escape leaves other dialogs alone; forced-colours focus and selection; the nudge and the report confirmation are announced; a skip shows no option as chosen; "Verder" reads out the correction; the keys hint is hidden on touch screens; a saved suggestion keeps its example and library source and its button keeps focus; a word missed twice is listed once; a report's request id is tied to its reason and note, and `python -m dlp.cli exercise-reports` reads them without the learner; the sound reason only for items with a sound; honest copy for the while-you-wait entry and for stopping; `--measure-answers` times one kept-alive connection and never touches a real session |
| 3.7a | done | (the flashcard is not planned in sessions, so it has no renderer here; word review decides in 5.1) tap kinds in the runner: match pairs, de/het, the sentence builder and the ordering, answered whole (the runner keeps a draft answer, and "Controleer" before the board is complete says "Maak eerst alles af"); no dragging (buttons and native radios, focus kept on the moved piece), each part's result and the right answer shown after the verdict; the gallery card with every answer-option state and its check (words and an icon per verdict); no focus ring on headings that only take focus for a screen reader; component tests per board, an e2e run through the four boards by keyboard with axe and overflow at 1440/390/320 before and after each answer; the gallery baselines regenerated (a new card and the up-arrow icon) |
| 3.7a review | done | adversarial review of 11 Oct (34 findings, 30 kept, many found by several lenses): a skipped board shows its answers (each word's meaning, every article, the right sentence, the right order without marks for an order never sent) and de/het turns read-only; an "almost" ordering is neutral, never in the miss colours, and each misplaced sentence says where it stood; a board that comes straight back starts again from the server's reshuffled prompt (renderers keyed per asking and per verdict), so an ordering can be checked as it stands; the same pairs or articles are the same answer (one key order, so a resend keeps its request id); the built sentence's verdict has an icon, a dashed border and words at the first difference; the de/het focus ring shows on the chosen half too, and forced colours show the chosen article, focus and the waiting pair word; tiles are at least 44px and long words wrap at 320px; pair names say what they go with once, each language in its own span; the ordering's translation follows the learner's languages; the board e2e run is keyboard-only and checks the live region |
| 3.7b | done | typed, listening and speaking kinds in the runner: typed cloze, typed recall and dictation in a Dutch field the device leaves alone (`lang=nl`, autocapitalize, autocorrect, spellcheck and autocomplete off), Enter to check, the hint on request reported with the answer, a word-by-word comparison and the comparison's notes in words, "Mijn antwoord klopt ook" (override) after a typed answer or a built sentence the check did not accept; listen-and-choose and dictation with the item's sound (`ItemAudio` over the audio route, one sound at a time, kept for the tab, a test tone labelled), "Ik kan nu niet luisteren"; shadowing recorded with one press and stopped with another, heard or not heard with the words heard and never a score, "Ik kan nu niet spreken", a second take at once when not heard; the audio route names its voice; unit, component and e2e tests (a mocked session through each typed, listening and speaking kind by keyboard with the fake microphone, the recording route mocked and its multipart contract covered by the API tests; axe and overflow at 1440/390/320) |
| 3.7b review | done | adversarial review of 11 Oct (28 findings, 24 kept): "almost" and an overruled answer are neutral in the word comparison (only a miss is drawn in the miss colours), and an overruled answer or sentence shows the check's answer as what it expected, not as the right one; after "Mijn antwoord klopt ook" focus moves to "Verder" and the answer's point stays on screen; the hint keeps focus in the field, is announced in a region that was already there and describes the field, and is reported with its own item's answer only (it leaked to the next item after a 409); the hint gives the letters of each word (spaces and hyphens are not letters) and an answer of several words is asked for as words; a skipped shadowing item says nothing about what was heard; the recording instruction is given before the take (nothing is announced while the microphone listens); a browser that cannot record is not given shadowing; "Verder" also reads out the item's own verdict; the listening-limit copy no longer promises tomorrow; the accent note no longer says accents were missing; the speech e2e answers like the server (a miss comes back, a take not heard is tried again, the override earns nothing) and runs every control by keyboard, including a typed cloze of two words |
| 3.8 | done | topic and lesson sessions (API, D-31): `source: topic` with `topic_id` and `skill`, and the stage lesson's reading or listening as `source: stage_skill` with `skill`; a passage step (`read_passage`, `listen_passage` over the existing `/listening` routes; translation or transcript once every question is answered) and the authored questions as shuffled choice items; at finish the first answers go through the unchanged `objective_result` into `_persist_topic_result` (with one `topic_practice` observation, request id `exercise:<session id>`) or `_persist_core_practice`, shown as the summary's `completion`; a first-try skip is wrong, a question never tried records nothing, changed content counts for nothing; `retry` asks only the missed questions and completes nothing; speaking and writing are warm-ups on the topic's words that complete nothing; resume keyed on topic, skill and retry; `review_of` on topic lists and details; `tests/test_exercises_topic_completion.py`, `tests/test_exercises_final_check_isolation.py` (the final check sealed off while lesson and topic sessions run, and no final-check sentence or question in any item at any stage) |
| 3.8 review | done | adversarial review of 11 Oct (21 findings, 12 kept): a topic or lesson session built on content changed since is abandoned instead of resumed (it could never count); a retry keeps the session it came from (`retry_of`) and one left open is not resumed once a newer session finished; a warm-up's boards keep to the topic's words; `review_of` follows the design (per skill, the same reading or listening text as an earlier stage's, never by title alone; none for speaking and writing) and reads the earlier texts once per file version instead of validating and keeping every earlier bank on each request; web copy for `nothing_to_retry`; the warm-up test now covers typed and spoken items over many seeds with the words already met |
| 3.9 | done | topic reader on sessions (web, D-32): a start card (what happens, "Herhaling van …" when the text repeats an earlier stage's, already practised); reading and listening run `ExerciseSession` embedded (heading level, no page title or second chip, Escape within the session, the host's way out, activity and finish callbacks, `sessionRequest`); `PassagePanel` keeps the passage (text or `CurriculumAudio`) in one node from its step through every question, and the summary reads it again with its translation or transcript; the summary says what counted (`completion.ts`) and offers the missed questions first (`retry`), or all of them again; speaking and writing offer a warm-up or the task straight away, and links, conversations and drafts open the task; authored questions show their stem's gloss and sound, options' glosses only with the verdict, also in `CurriculumQuestions`; `SpokenPassage` in its own module; a `topics` copy batch; tests: unit (`topic-session`, reducer), component (`topic-session`, the `/oefenen` pins), e2e `skill-topics.spec.ts` rewritten (mocked sessions for reading, retry, the warm-up, late listening, 320 px, the review label; the real A2 topic through the API) |
| 3.9 review | done | adversarial review of 11–12 Oct (24 findings, 10 kept): an authored question is part of its radio group's name again (the Dutch stem, not its play button); a session inside a topic that cannot start moves focus to its notice; the task's warm-up button is disabled rather than removed while recording, coaching or sending, so the recorder and the text box never move; a retry's stop dialog says the round does not count and promises no later resume (`exitLeadRetry`); the translation button is an action whose name says what it does (no `aria-pressed`); the task's own headings sit under "Jouw opdracht"; after an early finish or changed content all the questions again lead, not a retry that cannot count; a reading or listening topic sends its finish with the last verdict (under the id "Verder" sends again, reported to the host once), so leaving before "Verder" still counts the first answers; the review-label e2e runs on a1 repeating pre-A1, as the API does; kept as designed (D-31, D-32): "Ik kan nu niet luisteren" on the passage, the translation or transcript after any finished session, the retry first after a counted round |
| 4.1 | done | Today reads without writing (D-33): `GET /today` builds the plan from what is stored (`today_view`; a learner without a series sees the series to come) and creates, locks and queues nothing (only the throttled `last_seen_at` of every signed-in request); `POST /today/prepare` (opening Today, CSRF-checked, idempotent) keeps one unread episode queued or ready and answers the same `TodayPlan`; the page prepares when it opens, on its retry and on the stalled refresh, and otherwise reads; one function-scoped session dependency (`api/deps.db_session`) for every route and `context_dep`, so a request's writes commit before the response and a failed commit is a 500; `last_seen_at` written at most every ten minutes; fastapi 0.141 or later; `tests/test_today_contract.py` (no write statement on three reads, prepare queues one episode once, a failed commit answers 500 with nothing kept, every route shares one function-scoped session); API suite 791 passed; e2e 145 of 146 (the writing warm-up summary's overflow check at 390 px failed once and is re-run when the database is back), screenshots to compare |
| 4.1 review | done | adversarial review of 12 Oct (5 findings, 3 kept): with "last seen" throttled nothing serialized one learner's requests any more, so two first prepares could both insert the series and one answered 500; the series is now inserted with ON CONFLICT DO NOTHING and the winner's row read back, and the writes that change both the profile and the series (a level change, onboarding) take `lock_learner` first so they never lock in opposite orders; D-33, ENGINEERING, the route and the page say what really happens (GET /today creates, locks and queues nothing but may refresh "last seen"; the stalled "Vernieuwen" and the retry prepare); `test_today_contract.py` adds two prepares at once and a read after "last seen" went stale (both pass in the 803-test API run of 2026-10-12) |
| 4.2 | done | API 803, web unit and component tests pass; `run.py e2e` and the adversarial review are still to run. Points for every kind of practice (D-34, revising D-19 and amending D-20): the lesson's and the topic's classic forms pay per question answered or the assessed open task, once per activity and Brussels day (`course_questions`, `course_task`); a submitted stage check 15 once per attempt, passed or not, never an admin preview (`stage_check`); missions per question of a done step, the message and each stored turn (`mission_questions`, `mission_writing`, `mission_turn`); a topic conversation's answer turns (`conversation_turn`, help turns nothing); the microphone warm-up 2 a day with `purpose=warmup` and recognised speech (`speech_warmup`); typed turns under writing, spoken under speaking (`record_activity(skill=...)`); story and video questions per answered one (O1), the day still counting the correct ones (`counted=`); awards only in entry functions after the paid call, never in helpers a session shares; replays repeat `goal_reached` only; conversations' daily start limit on the Brussels day (`day_bounds_utc`); tests per call site in the existing suites |
