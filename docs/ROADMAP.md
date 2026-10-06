# Roadmap — October 2026

The approved plan for the three asks of October 2026: a structure review against modern practice
(see [CODE_REVIEW.md](CODE_REVIEW.md)), bounded AI agents on Azure, and a UX/UI overhaul. This file is
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

## Decisions confirmed with the owner

| Question | Decision |
|---|---|
| Scope | All three tracks, implemented phase by phase in reviewable steps |
| Interface language | Dutch stays, with English/Persian shown underneath for beginners; onboarding fully bilingual |
| Agent features | Tutor ("explain my mistake"), study guide on Today, free conversation partner, live voice conversation |
| Agent hosting | Bounded, tool-using agents inside the existing FastAPI app; code keeps validating everything |
| Motivation | Effort-based and non-punitive: points for all practice, streaks, summaries, progress rings. No hearts, no overall level, no pronunciation score |

## Key technical choices

- **Agent architecture: a small in-house loop on the existing model port, no framework.** The judge
  scored it 60 against 52 (LangGraph agents with a Postgres checkpointer) and 51 (Microsoft Agent
  Framework in-process): it keeps every rule literally testable (reserve before call, one request per
  step, never replay), keeps CI on fixtures and local runs on Ollama, and adds no dependency. LangGraph
  is removed (it only runs two linear three-step graphs). Tool and agent definitions map one-to-one onto
  Agent Framework function tools, which stays the documented exit path.
- **Honest description of the agents.** The tutor is a real tool loop (at most 3–4 model steps over
  read-only, learner-scoped tools). The study guide is one ranking call shaped as a "propose" tool over
  code-built candidates. The conversation partner is a two-request pipeline (interpret, then a guarded
  reaction) rather than an open chat; an open-turn mode is an owner decision in P7. Voice uses one forced
  tool call per turn.
- **Azure: stateless Responses API through a hand-written `httpx` adapter**, strict JSON-schema output
  and strict function tools, proven first against the existing deployment. New EU Data Zone deployments
  run side by side with the current one and are switched after an eval gate, **before 2027-01-31**
  (the current deployment stops serving on 2027-04-14). Target per Microsoft's pages read on 2026-10-06:
  gpt-5.6-luna (small) and gpt-5.6-terra (strong); first fallback gpt-6-luna/gpt-6-sol; last resort
  gpt-5.4-mini/gpt-5.4. Names and versions are confirmed with the Models API at deploy time.
- **Streaming: FastAPI's built-in SSE (present in the locked 0.141.1) on twin `.../stream` routes**,
  driven by a runner thread that settles usage even if the browser disconnects. Every stream has a plain
  JSON twin. The proxy's timeout applies to time-to-headers only; long streams roll over through
  `?after=` resume.
- **Practice: a server-owned exercise engine.** Sessions are generated from a seed and graded on the
  server; the browser never receives an answer key before answering. Twelve item kinds come from existing
  content with no new authoring; generated and validated content follows in P7.
- **One learner profile** (`learner_profiles`) is the only source of level, daily goal and support
  language. **One activity service** (`record_activity`) awards all points. **One paid-call gateway**
  (`LlmGateway`) owns reserve, call and settle.
- **Styling: design tokens and cascade layers, not Tailwind.** Token-driven global classes in `@layer`s
  with typed wrappers in `components/ui`; the roughly 70 class selectors the e2e suite depends on stay on
  the same elements. Motion is CSS-only. Icons move to `lucide-react` behind the existing `Icon`.
- **Web data: TanStack Query** over the existing `apiFetch`; generated TypeScript types from an OpenAPI
  export arrive with the agent platform; Vitest + React Testing Library for components.
- **Live voice: the API brokers the session.** One outbound WebSocket to Azure Voice Live; the browser
  uses the existing signed proxy (SSE down, sequenced audio chunk POSTs up). The partner's reply is
  produced as text, gated sentence by sentence, and only then spoken through the TTS port. No new public
  ingress without an owner decision.

## Shared contracts (one owner each; other tracks adopt these)

| Seam | Contract |
|---|---|
| `GET /me` | Returns the profile and, from day one, `features: {}` (agent and voice switches land there later). A development/test-only reset clears `onboarded_at` for e2e. |
| Activity | `domains/activity/`: `record_activity(session, learner_id, *, kind, ref, request_id, skill=None, meta=None)`; append-only `activity_events` with `UNIQUE(learner_id, kind, dedupe_key)`; one rules table owns point values and scopes for every kind, including exercise kinds and shadow; `learning_days` gains `goal_target`, `exercise_items`, `exercise_sessions`. Awards happen after `_record_episode` returns, never inside it. |
| Mistakes | `domains/exercises/taxonomy.py` is the single category list (vocabulary_meaning, vocabulary_form, article, spelling, word_order, grammar_form, missing_word, listening_discrimination, comprehension, punctuation, word_choice, preposition); `learner_mistakes` carries `source, source_id, stage_id, skill, kind, category, given, expected, quote, assessed, request_id, resolved_at`. `content/tutor/categories.json` is validated against the module. |
| Snapshot | `domains/today/snapshot.py` built in P4; the agent platform extends it with mistakes; no second snapshot module. |
| Today payload | One `session` block (`today-plan-v1`: ordered steps with kind, status, minutes, points, benefit, reason, href, one primary). Warm-up and mistakes candidates and the study guide all feed this contract. `GET /today` is read-only from P4 step 4.1; the page loads through idempotent `POST /today/prepare`. |
| Gateway | `domains/llm/gateway.py` as judged (A-S01): legacy sites reserve in the caller's transaction; agent runs reserve the whole budget on their own connection before the first call; no audit row for single calls. Structure steps S09 and S12 are superseded; what survives from them is the `call_claims` helper and database timeouts (P6 step 6.1), `ProviderRejected`, and no total proxy timeout on streams. |
| Migrations | Numbered in landing order; see the ledger below. |
| Screens | The journey track owns the structure of the shell, Today, path and stage pages; design-system steps are style passes that follow. The shell is laid out once (P1 step 1.7) and the path once (P5). |
| Word review | Engine word kinds keep the four grade buttons as the visible override after the code check; the word-review spec is rewritten once (P5 step 5.1). |
| Gloss on tabs | Five tabs; Dutch label plus a short gloss key from 360 px, none at 320 px; tested in nl-fa at 320 and 390. |

## Migration ledger

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

## Phases

Each step is one reviewable pull request of one to four commits, with the test suites green at the end
of the step. Commits and pushes happen only on the owner's say-so.

### P0 — Safety net (slim)

| Step | What changes |
|---|---|
| 0.0 | First-day checks on a throwaway branch, results recorded in `docs/plan/CHECKS.md` with the fallback for each: `python scripts/run.py setup` in a fresh worktree; `next build` with one stylesheet wrapped in `@layer` under Turbopack; a pytest proving commit timing of yield dependencies on FastAPI 0.141.1 with and without `scope='function'`; `alembic check` on a fresh database; a throwaway SSE route through `next start` (compression); whether eslint flags state-setting inside effects; the pinned Playwright Linux container running against host servers via `E2E_BASE_URL`. |
| 0.1 | Commit the session result files under `docs/plan/`, plus `docs/CODE_REVIEW.md` and this roadmap. Web line anchors in those files refer to commit 795697b; locate by selector, test title or quoted string after 0.2. |
| 0.2 [S01] | Prettier one-off format commit over ts/tsx/mjs, excluding legacy `app/*.css`, listed in `.git-blame-ignore-revs`; all Playwright specs pass with zero spec edits; Vitest + React Testing Library; `tsconfig.test.json` so tests are type-checked. |
| 0.3 [DS-01] | Visual freeze: `aa-visual.spec.ts` at 1440/390/320 for eight screens, plus `run.py e2e-visual` that runs it inside the pinned Playwright 1.56 Linux container against host servers, so baselines compare locally on Windows; local before/after snapshots are git-ignored until the P1 baselines are committed; a small PR to `main` adds the CI regeneration job first. |
| 0.4 | Ratchet tests only: routes without `response_model` may only shrink; layer-boundary imports may only shrink; CSS hex/dead-selector budgets may only shrink. (OpenAPI types, pyright and the coverage floor move to P6 step 6.0.) |
| 0.5 [S03] | Quick fixes: one `register_all()` for job handlers (the CLI misses the video handlers), unknown job kinds dead-lettered, `settings.job_max_attempts` honoured, bounded read-aloud upload, complete owner export, `scripts/check_model_lifecycle.py` wired into the release script and preflight; read-aloud points per owner decision O1. |
| 0.6 [S04, part] | `DomainError(code, status, persist)` base, one set of exception handlers, `code` added to error bodies; existing status codes unchanged; web copy for codes waits for the catalogue (P2 step 2.8). |
| 0.7 [S05] | One stages/skills registry; one storage-key module (fixes topic and conversation drafts surviving sign-out); proxy forwards the abort signal and applies a timeout to response headers only. |
| 0.8 [S06, part] | TanStack Query provider and typed query keys; no mass migration of readers. |
| 0.9 [X01] | Characterisation tests pinning what the engine must preserve (answer-key withholding, completion rules, final-check isolation) and content-pool invariants per stage, including the sentence-frame collision check that step 3.3 relies on; extract `_persist_topic_result`. |

### P1 — Design system and the five-destination shell (first visible change)

| Step | What changes |
|---|---|
| 1.1 [DS-02] | Delete confirmed-dead CSS by selector under a usage test; live rules inside those ranges stay. |
| 1.2 [DS-03] | Cascade layers and `app/styles/tokens.css` with compatibility aliases reproducing today's values: zero pixel change by local comparison; a unit test asserts AA contrast for every token pair. |
| 1.3 [DS-04] | Base layer: one focus ring, 12 px type floor, z-index scale, 44 px targets. |
| 1.4 [DS-05 + part of DS-14] | Palette flip through tokens: brand blue for actions; one hue per skill and section (reading blue, listening teal, speaking violet, writing orange, words amber, stories rose, progress green); green/red reserved for feedback; sage-green leftovers mapped; the four literal-colour files (library, topics, phrase-audio, learning-agents/-tools) tokenised now. |
| 1.5 [DS-06] | Primitives: Button, Card, Badge, Notice, IconTile, Field, Skeleton, EmptyState; `lucide-react` behind `Icon`; dev-only gallery page. |
| 1.6 [DS-07] | Motion (press, lift, pop, 4 px shake, pulse, shimmer, flip, burst) with reduced-motion fallbacks; Dialog, Toast, Tabs, Stepper; optional answer and goal tones through Web Audio (no asset files, a setting, off under reduced motion). |
| 1.7 [J05 + DS-08] | Shell split and five destinations in one pass: Vandaag, Leren, Verhalen (stories + videos), Spreken (conversations, missions, speech studio), Woorden; progress and settings in the sidebar and profile menu; plain Dutch labels now, glosses in 2.4; coloured section identity; e2e nav assertions updated in the same step; the navigation guard still wraps every link. |
| 1.8 [DS-09] | ProgressRing, ProgressBar, four-segment SkillMeter, Cover, a small inline-SVG illustration set; applied where data exists. Baselines regenerated and committed at the end of P1. |

### P2 — The start: profile, onboarding, one level, glosses, copy

| Step | What changes |
|---|---|
| 2.1 [J01] | `learner_profiles` (migration 0008), `GET/PATCH /me` with `features`, `POST /me/onboarding` (pre-queues episode 1 at the chosen level), dev/test-only profile reset; `stories.default_stage` reads the profile. |
| 2.2 [J02 + S07, part] | Web profile client; support language synced with the server; e2e auto-fixture that onboards and sets glosses off; server-side prefetch of `/me` with skeletons, disabled under e2e so browser mocks keep working. |
| 2.3 [J03] | One level everywhere (competing selectors removed); learning preferences in settings. |
| 2.4 [J04 + DS-10] | Gloss layer: typed copy catalogue (every key needs nl, en, fa), `UiText`, `gloss.css`, glosses on shell and navigation per the tab rule; a second axe and overflow pass with glosses on and nl-fa-en at 1440/390/320. |
| 2.5 [J06] | Onboarding at `/welkom` with `FirstRunGate`: support language, plain-language self-placement (sets a starting stage, never passes anything), goal, "how Taalstudio works", a first activity while episode 1 is written (replaced by an engine session in P5). |
| 2.6 [J07] | Interface copy on "je"; one honesty chip and an "about the content" page instead of repeated notices; empty states with one action; developer hints hidden from learners. |
| 2.7 | Adopt `UiText` on the existing daily-loop screens (episode reader, video player, word review, missions, speech studio) with a ratchet test on hard-coded Dutch JSX strings; Persian glosses ship off by default until reviewed (O2). |
| 2.8 | Web error copy from error codes, now that the catalogue exists. |

Owner action in this phase: run the voice spike (P8 step 8.0).

### P3 — Exercise engine core and topic sessions (the practice fix)

| Step | What changes |
|---|---|
| 3.1 [J10] | Activity service per the shared contract (migration 0009); the eleven `add_points` calls move over with unchanged values; one Brussels-day helper; read-aloud and question-point rules per O1. |
| 3.2 [X03] | Tolerant comparison (case, punctuation, diacritics, optional article, near-miss "almost", token diff) and a generic read-aloud comparison endpoint with no score. |
| 3.3 [X04] | Engine core (migration 0010): sessions, items, mistakes, suggestions; create/answer/skip/finish API; kinds: choice (4 options for vocabulary; authored comprehension keeps its options, shuffled), cloze by choice, odd one out. Rules: a distractor is illegal when its own example sentence equals the target with it filled in; if fewer than three legal distractors remain, cue with the support-language translation or drop cloze; an ungraded "nieuwe woorden" intro card before first exposure; no mistake row for a word the learner has not met; a content gate that enables only stages above a variety threshold. |
| 3.4 [X05] | Kinds: match pairs, de/het sort, typed cloze, typed recall, sentence builder, sentence ordering, flashcard; "my answer was also right" override that never affects completion; a non-red "bijna" outcome. |
| 3.5 [X06] | Audio kinds with cached speech (a cache hit costs no allowance): listen-and-choose, dictation, shadow (heard or not heard, neutral colour). |
| 3.6 [X07 + DS-12] | Web kit: reducer-driven session runner, feedback bar, progress, summary, one `AnswerOption` with correct/incorrect/almost/reveal states; keyboard and screen-reader behaviour; `lang=nl` and autocapitalize off on typed inputs; a "report this exercise" control; boards submitted whole; p95 answer round trip of 300 ms or less. |
| 3.7 [X08] | Remaining renderers. |
| 3.8 [X09] | Topic and lesson sessions with unchanged completion rules; a missed authored question can be retried in a short new session; final-check content is never a source. |
| 3.9 [X10] | A topic starts with a session; the open speaking or writing task follows; option glosses hidden until answered; reused topics labelled as review. |

### P4 — Points for all practice, Today as one session, progress

| Step | What changes |
|---|---|
| 4.1 [S08] | `today_view` (read-only) plus idempotent `POST /today/prepare`; `GET /today` causes no writes; tests switch through one helper; `last_seen_at` throttled; commit-before-response scope per the 0.0 result. |
| 4.2 [J11] | Points for lessons, topics, missions, conversations and speech warm-up, from code-observable facts only; episode and video questions per answered (O1). |
| 4.3 [J14, API] | `GET /progress/summary` and `GET /progress/day`. |
| 4.4 [J12] | Learner snapshot and deterministic planner producing the `session` contract; `GET /today/ready`. |
| 4.5 [J13 + DS-11] | Today page as one guided session with one primary button, goal ring, labelled week strip, staged waiting card, ready notification, celebration; goal expressed per O3. |
| 4.6 [J14, web] | Progress dashboard. |
| 4.7 [J15] | Decision records, documentation, regenerated previews. |

### P5 — Engine everywhere, linear path and stage pages

| Step | What changes |
|---|---|
| 5.1 [X11] | Word review on the engine (typed recall mapped to SM-2, grade buttons kept as override); word suggestions; saving library words. |
| 5.2 [X12] | Today warm-up, "repeat your mistakes" (a mistake resolves only on a later Brussels day), while-you-wait; planner lesson steps and onboarding's first activity re-pointed at engine sessions. |
| 5.3 | New source: "Oefen met deze aflevering" after reading an episode (mechanical kinds only, labelled generated). |
| 5.4 [J08 + DS-13] | Linear path page with a compact rail of twelve nodes on a connector. |
| 5.5 [J09 + X13] | Linear stage page with a lesson stepper; path lesson and grammar on the engine; practice answer keys no longer sent to the browser. |
| 5.6 [X14] | Retire the five duplicate multiple-choice renderers, VocabularyRecall and the alphabet quiz; hide Story Time duplicates; label reused word lists; flip word cards. |
| 5.7 [DS-14, part] | Missions, speech studio, videos and settings onto primitives; delete their legacy CSS. |

### P6 — Agent platform and Azure model migration (cut over before 2027-01-31)

| Step | What changes |
|---|---|
| 6.0 [S02, rest] | OpenAPI export with generated web types, pyright on an include-list, coverage floor. |
| 6.1 [A-S01 + S10, part] | `LlmGateway` with one failure policy under the one-request call sites; `call_claims` helper and database lock/idle timeouts. |
| 6.2 [A-S02] | Retrying sites onto the gateway; attempt-accurate token accounting; failure-policy decision record. |
| 6.3 [A-S03] | Remove LangGraph; plain pipelines; architecture test forbidding vendor SDK imports in domain code. |
| 6.4 [A-S04] | Model port v2, additive: `respond()` and `stream()`; scripted fixture; Ollama tools. |
| 6.5 [A-S05] | Azure Responses adapter, stateless, strict output and tools, proven against the existing deployment; a probe command. |
| 6.6 [A-S09] | Side-by-side EU Data Zone deployments in Bicep, lifecycle check, caps with a priced monthly envelope, a paid probe for run budgets, eval gate on both candidate pairs. |
| 6.7 [A-S06 + A-S07] | Agent runtime (migration 0011), tool catalogue, snapshot extended with mistakes, grounding helpers, authored category notes. |
| 6.8 [A-S10 + S11] | SSE end to end; job runner heartbeat, handler context, retention, deferral of video claims while a stream or voice session is live, API size parameters. |
| 6.9 [A-S08 + S13] | Metadata-only spans with a canary test; JSON logs; eval harness; feature switches populated in `GET /me` and an e2e run with all flags on. |

### P7 — Agents and generated content

| Step | What changes |
|---|---|
| 7.1–7.2 [A-S11, A-S12] | Tutor "Leg uit" (migration 0012): authored explanation first; grounded why-follow-ups (cap 3); a mini-drill; recurring categories remembered; hidden when the flag is off. |
| 7.3–7.4 [A-S15, A-S16] | Conversation partner: guarded generated reaction before the authored anchor (migration 0014); feedback after the conversation quoting the learner's own turns. |
| 7.5 [A-S17] | Scenario scale-up (migration 0015). |
| 7.6 | Optional open-turn partner mode per O5. |
| 7.7 [A-S13, A-S14] | Study guide (migration 0013); `POST /coach/plan` and its button stay until the flag is on in production. Automatic daily run per O4. |
| 7.8 [X15] | Model-judged exercise kinds. |
| 7.9 [X16] | Generated items behind a validator and the review queue (migration 0016); a verb bank. |
| 7.10 [A-S18] | Run visibility, export of the new tables, documentation. |

### P8 — Live voice conversation

Go only if all ten spike criteria from the design are recorded and latency passes on the target small
model. A relay container app (plan B) needs an owner decision revising the single-public-entry rule;
otherwise a failed spike is a no-go.

| Step | What changes |
|---|---|
| 8.0 [V-0] | Spike (run during P2) and go/no-go record in `docs/LIVE_VOICE.md`. |
| 8.1–8.3 [V-1..3] | Flag, settings, allowances; `RealtimeVoice` port with a fixture adapter; session table (migration 0017), reservation and settlement. |
| 8.4–8.5 [V-4..5] | Turn director (forced tool call, code validation, text gated per sentence then spoken through the TTS port); runtime and streaming routes with rollover every ~200 s. |
| 8.6–8.7 [V-6..7] | Azure Voice Live adapter; local cascade adapter. |
| 8.8 [V-8] | Evidence (transcripts only), points, post-conversation feedback. |
| 8.9–8.11 [V-9..11] | Browser audio engine, live conversation UI, push-to-talk default, fallback. |
| 8.12–8.13 [V-12..13] | Bicep and release wiring; hardening and cost reconciliation. |

### P9 — Hardening and close-out

| Step | What changes |
|---|---|
| [S10, rest] | Legacy paid sites onto claim, call, settle; provider failures unified on 503 with `code`; web retry branch on `code`; decision record. |
| [S14] | Layering clean-up. |
| [S15] | Split the surviving large components; lazy-load heavy panels. |
| [S16] | Delivery: promote CI-built images by digest, app revisions through Bicep (what-if checked by the owner first), storage lifecycle. |
| [DS-14 rest, DS-15] | Remaining screens onto primitives; retire the legacy CSS layer; dry-run dark tokens. |
| Data | Retention job and learner-facing delete for the new learner-text stores; retire the classic receptive practice branch; jti replay check. |
| Docs | Refresh ENGINEERING, ARCHITECTURE_WALKTHROUGH, GO_LIVE, STATUS, VERIFICATION. |

## Release gate (end of every phase)

One pull request to `main`; rehearse the phase's migrations on a restored copy of production; take a
database backup and record the current image digests; release migration-first; run
`scripts/verify_live.py`; rollback is forward-only once the migration head moves. The first-run redirect
and the new Today page ship behind an environment switch.

## Owner decisions (defaults the plan takes if not told otherwise)

| Id | Decision | Default |
|---|---|---|
| O1 | Non-punitive points: episode and video questions pay per answered instead of per correct; read-aloud pays any attempt with recognised speech instead of a 50 % threshold | Adopt both (P0 0.5, P3 3.1) |
| O2 | Persian and English interface glosses are written during implementation and unreviewed; who checks them? | Persian off by default until reviewed; English on |
| O3 | Daily goal: state it as the day's session length (kort / gewoon / stevig) or keep a point target scaled to the planner | Session length |
| O4 | May the study guide make one automatic paid run on the first Today visit each day? | Off; manual refresh button |
| O5 | Partner: reaction-only, or add the open-turn mode (7.6)? | Reaction-only first; 7.6 after the eval |
| O6 | Azure: accept EU Data Zone processing; approve daily and lifetime caps with the priced monthly envelope; request quota | Needed before 6.6 |
| O7 | Who judges Dutch correctness of generated explanations, reactions and scenarios? | A fluent reviewer; otherwise the flags stay off |
| O8 | Voice: go, plan B (public relay), or no-go after the spike | No-go unless criteria pass |
| O9 | Streak: keep "a missed day resets" or allow one rest day per week | Keep as is |

Recurring owner tasks: regenerate and review screenshot baselines after each visible step; approve
generated comprehension items in the review queue; a first-week comparison of recorded usage with
Azure billing; the phone check.

## Rules consciously revised

Each becomes a new numbered entry in `DECISIONS.md` (after D-22), written in the step that changes the
behaviour.

| Existing rule | Revision | Step |
|---|---|---|
| D-19: points only for story and word actions; fixed goal of 20 | Points for every kind of practice; still reward doing, never judge Dutch; goal per O3. Word bank still fills only by the learner's choice | 3.1, 4.2 |
| D-20: read-aloud points once per paragraph at 50 % recognised | Any attempt with recognised speech (O1); the no-score rule extends unchanged to shadow items | 0.5, 3.5 |
| "Interface is in Dutch"; "restrained navy/blue palette"; "support tools add no main navigation" | Gloss layer under Dutch chrome; per-skill colour system; five destinations with a Spreken hub | 1.4, 1.7, 2.4 |
| Recall rounds are self-assessed | Typed recall is checked by code; self-assessment remains only as an override | 5.1 |
| Practice keys travel with the stage view | Practice answers withheld until answered, like the final check | 5.5 |
| LEARNING_AGENTS: no tool loop; coach reorders three; replies authored only; one call per turn; ten pilots | Bounded tool loops over read-only tools plus code-validated proposals; a guarded generated reaction; 1–400 scenarios | 6.7, 7.3, 7.5, 7.7 |
| "Reading the plan makes no model call" | One bounded guide run per day only if O4 says yes | 7.7 |
| D-12 failure policy and LangGraph graph; D-12/D-13 failed turn is 502 | One conservative policy for every paid chat call; plain functions; failed turn 503 with `code turn_failed` | 6.2, 6.3, P9 |
| GO_LIVE: Chat Completions, JSON mode, regional Standard model | Stateless Responses API on EU Data Zone deployments | 6.5, 6.6 |
| Usage day is UTC while the learner day is Brussels | One learner-day helper for points; allowances documented as UTC | 3.1 |
| Data: no learner free text stored beyond attempts | Writing submissions, tutor threads, mistake rows, exercise answers and transcripts are stored, exported, deletable and retained per P9 | 3.3, 7.1, P9 |

Rules that stay untouched: models propose and code decides; reserve before every paid call; no
pronunciation score, overall level or certificate; typed input never counts as speaking; final-check
withholding; generated and unreviewed content stays labelled; the API is never public; telemetry carries
no prompts, text or identifiers; the accessibility gate.

## Verification

After every step: `make lint`; `python scripts/run.py test`; `cd apps/web && npm run test:unit` (and
`test:component` from 0.2); `python scripts/run.py e2e`; `run.py e2e-visual` when a baselined screen
changed. Phase acceptance checks are listed with each phase in the approved plan and repeated in
`STATUS.md` as phases complete.

## Progress

| Step | State | Notes |
|---|---|---|
| 0.1 | done | `docs/plan/*.json`, `CODE_REVIEW.md`, this file |
