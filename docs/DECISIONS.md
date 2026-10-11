# Decisions

What was decided, why, and what it costs. Newest last. Numbers are kept so that code comments and
older notes still resolve.

## D-01 · Provisional mission content and the fixture-integrity check

The first mission (*Een afspraak verzetten*, A2: a dentist base scenario and a hairdresser transfer
scenario), its four provisional language targets, the evidence expectations and acceptance check
**A01 = fixture integrity** (the file validates, the stored copy matches by hash, normalised steps
agree, the pack stays under its word limit, every text is labelled, four skills are covered, both
variants resolve, the help ladder is Persian/RTL and absent in the checkpoint, authoritative dates are
coherent) were written from the release scope. All of it stays provisional until a language reviewer
has seen it.

## D-02 · What counts toward the 300-word fixed Dutch pack

The pack is the Dutch the learner reads or hears as lesson content: reading text, listening
transcript, questions and options, speaking/checkpoint goals, writing prompt, character lines,
reason options and slot notes (regex `PACK_PATH` in `content/schemas.py`). Titles, instructions,
roles, settings, can-do statements and success criteria are interface guidance shown bilingually
and are counted separately (`interface_word_count`). The pack is 297 words; the limit is enforced
at load time and by A01.

## D-03 · Assertion between web and API: HS256 shared secret

A short-lived HS256 JWT with a 32+ character server-only secret, issuer/audience/expiry/jti, and
the allowlist checked again in the API. Asymmetric keys (the API holding only a public key) would
stop a compromised API from minting assertions, but both tiers sit inside the same trust boundary
and the extra key handling would burden the laptop setup. The verifier is one function
(`identity/assertions.py::validate_assertion`); switching to RS256/EdDSA later is a configuration and
key-loading change, not a redesign.

## D-04 · CSRF: custom header plus origin checks, no cookies

The API uses no cookies, so classic CSRF cannot ride on ambient credentials; the defence still
matters because the web proxy attaches identity server-side. Unsafe methods must carry
`X-Requested-With: fetch` (a header a cross-site form cannot set), and the proxy also checks
`Sec-Fetch-Site`/`Origin`. The API enforces the header again so the rule holds even if the proxy is
bypassed.

## D-05 · Fixture identity is accepted in `development` and `test`, refused elsewhere

The automated test suite runs as `APP_ENV=test` and needs the same principal path as development.
`production` refuses `DEV_AUTH_ENABLED=true` at startup in both tiers, and the web tier additionally
binds the fixture to requests whose `Host` is localhost.

## D-06 · Same Azure SDK adapter for Azurite and Azure Blob Storage

`AzureBlobStore` talks to Azurite (connection string) locally and to a private container (account
URL + managed identity) in the cloud. One adapter, one set of tests; the difference is credentials.

## D-07 · Usage counters enforced in SQL

`used + reserved + amount <= limit_value` is checked inside the `UPDATE`, in one transaction for
the daily and the total counter, with a nested transaction so a refusal leaves nothing behind. The
concurrency test (20 threads, 120-second daily budget, 10 seconds each) shows exactly 12 successes.
Cost: two rows per learner, metric and day; negligible.

## D-08 · Azure speech adapters declared early, verified later

`AzureSpeechToText` / `AzureTextToSpeech` exist as classes so configuration, the registry and
preflight know them. They use the Speech REST endpoints for short audio (push-to-talk turns are
≤ 30 s) and are unit-tested with recorded fixtures; they stay `integration_pending` until a live run.

## D-09 · Storage of files

Committed: source, tests, migrations, content, the two small synthetic WAV fixtures (a tone for
the API tests, a tone for the browser's fake microphone), docs, CI. Ignored: `.env`, `instructions/`,
`D/` and any PDF, `.local/` (whisper cache, Piper voices), benchmark results, recordings, Playwright
output, dependencies. No real recording is committed.

## D-10 · Two verification environments

The API suite and the browser suite run anywhere with PostgreSQL 16, ffmpeg and headless Chromium
(fake microphone), using fixture providers. Ollama, faster-whisper models and Piper voices only run
on the development laptop. `docs/VERIFICATION.md` keeps the two apart: `verified_local` is reserved
for behaviour exercised with the real local providers; CI evidence is called what it is.

## D-11 · Cross-platform task runner instead of shell-only scripts

Development happens on Windows with Docker Desktop and WSL 2. `scripts/run.py` (plain Python) runs
every routine task on Windows, WSL, macOS and Linux; the `Makefile` only delegates to it.

## D-12 · The shape of the conversation turn

The conversation turn is one small LangGraph graph with typed state (`domains/practice/workflow.py`):
`propose_action` (model, structured output `ProposedActionReply`) → `validate_action` (code,
`apply_action` against the scenario's authoritative slots) → `compose_reply` (model, structured
output `CharacterReply`, anchored on the scenario's fixed line for the current phase). The model
interprets and phrases; it never decides. If the *reply* call fails, or if the reply announces a booking
the code did not accept, the fixed line is used and the turn records `reply_source = fixed_line` plus
the error text. If the *first* call fails (model unreachable, timeout) the turn fails with 502: without
the model's reading no action can be recognised, so a fixed-line answer would only simulate a
conversation and, in the checkpoint, burn the single attempt. Failed turns do not count against the
step's turn limit. A refused connection to the chat endpoint is reported at once as unavailable, without
the retry backoff meant for transient errors. Two model calls per turn (`MODEL_CALLS_PER_TURN`) and
1 800 tokens are reserved before the call, the measured usage is committed after it, and a failure
releases both reservations. Prompt templates carry version tags that are stored with every turn.
Alternative considered: one call that both decides and replies; rejected because the reply would then
have to be parsed to find out what the model "did", and the code could no longer be the authority on
the appointment.

Typed and spoken turns share `submit_turn`; the spoken path only adds upload → canonical WAV →
transcript in front of it. Evidence is written per turn: `transcript` (speech) or `typed_text`
(typed, labelled as such) plus `action_result`; the skill record for speaking moves to
`in_progress` on the first turn and to `practised` (speaking step) or `checkpoint_passed`
(checkpoint) when the required actions are done.

## D-13 · Session semantics: resume, one attempt at the checkpoint, failed turns kept

One active practice session per learner, mission and variant: `POST /practice/sessions` resumes the
active session of that variant instead of opening a second one, and the lesson page loads active
sessions on every visit, so a reload never loses a conversation. `POST …/abandon` closes a session
without completing it. A variant whose checkpoint declares `retry: false` gets exactly one session:
once it is `completed`, `ended` (turns exhausted) or `abandoned`, a new one is refused with 409.
A retry with the same request id returns the stored turn (or repeats its 502 when that turn failed)
and never runs the model twice; a failed turn is kept as a row with its error so the failure is
visible and countable, and the response is returned rather than raised so the transaction commits.
The browser client reuses the request id after a network failure and mints a new one after a 502.

## D-14 · Evidence for the other three skills, feedback that can only cite evidence, the export

Reading and listening answers are judged on the server against the mission document (`practice/steps.py`)
and stored as `answer` evidence with the attempt number; the browser only collects choices. Every help
rung opened is `help_used` evidence (refused in the checkpoint, capped by `help_policy.max_level`). The
writing draft autosaves into the session state (`state.drafts`, not evidence); the submitted message is
`typed_text` evidence with its word count and the required words found or missing, refused outside the
word bounds. The listening clip is synthesised once from the transcript with the local voice, stored
under the step's `audio_key` in the blob store with a sidecar that carries its label, and served from
there afterwards; the cloud release overwrites that object with the Azure `nl-BE` voice.

Feedback (`domains/feedback/service.py`, one model call) is only produced when the mission's
`evidence_expectations` for the skill are met, including at least one code-validated action for
speaking. The model sees the step's evidence as numbered handles (E1, E2, …) and must cite them per
point; the code resolves handles to evidence ids and drops every point without a valid citation or with
a quote that does not occur in the cited evidence. Dropped points are stored and counted, never shown.
Reports live in `feedback_reports` (migration 0002); the skill record notes the report id. This is
feedback on a step, never an assessment of the skill. The export (`GET /export`, allowlisted accounts)
is one JSON document with the learner, the four skill records, every session with turns, evidence and
feedback, and the usage snapshot.

Every database connection is pinned to UTC (`options=-c timezone=UTC`): the API's ISO timestamps must
compare the same whether a value was just written or loaded from PostgreSQL (whose server time zone can
be Europe/Brussels), and the browser merges concurrent updates by instant.

## D-15 · First Azure shape (superseded by D-17)

Historical. One resource group, one Container Apps environment (consumption, scale to zero): `dlp-web`
with external ingress and the platform's built-in Microsoft Entra authentication (the proxy reads the
`X-MS-CLIENT-PRINCIPAL-*` headers and applies the allowlist), `dlp-api` with internal ingress only, so
the web app stays the single public entry. PostgreSQL Flexible Server `Standard_B1ms`, Storage
`Standard_LRS` with shared-key access disabled, Azure AI Speech `S0` with local authentication disabled
and a custom subdomain, Key Vault (RBAC) for the signing key and the database password, Container
Registry `Basic`, Log Analytics. The Speech adapters use the REST endpoints for short audio with a key
or an Entra token, because every turn is at most 30 s and the streaming SDK would add a native
dependency for nothing. Deployment is a manual GitHub Actions workflow authenticated with OpenID
Connect (federated credential; no cloud secret stored in GitHub).

## D-16 · Typed input never counts as speaking practice; acceptance checks over the data

The goal of the speaking step can be reached with typed text (the practice step allows the typed
fallback), but the speaking skill record only moves to `practised`/`checkpoint_passed` when the step has
at least one spoken (`transcript`) evidence record; a typed-only completion is recorded as such and the
page offers a fresh practice session. Checks A02–A06 (`domains/practice/acceptance.py`) are read-only
queries over the stored data — separate skill records, no typed credit, feedback citations resolve to
the step's evidence, checkpoint independence, settled usage — runnable at any time from the CLI, the
API and `scripts/verify_live.py`, so the claims in the verification notes can be re-checked by anyone.

## D-17 · Learner experience and controlled Azure release

The product label is Taalstudio, with one desktop/mobile shell, separated learning and technical
settings, four evidence-based skill records and local recording replay. No fictitious scores,
certificates or reviewed-content claims are added. Primary app navigation waits for writing autosave;
automated accessibility checks supplement, not replace, manual review.

The cloud profile uses a warm 0.25-vCPU API for its PostgreSQL job loop; the web can scale to zero.
PostgreSQL is VNet-private. An explicit, bounded migration job uses a separate identity and
administrator connection, while the API uses a DML-only role. Azure chat is required in production,
authenticated through managed identity, with a pinned, region-supported deployment. Separate per-secret
Key Vault grants prevent the web/API from reading migration credentials. Create foundation, images and
migration job first; run migrations; deploy the apps privately; configure and verify sign-in; publish
explicitly. The release workflow requires exact-commit main CI and protected OIDC deployment approval.
A budget alert is not a hard currency cap. Paid use is switched on deliberately (`PAID_USAGE_ENABLED`),
never by the presence of credentials.

## D-18 · A generated serial instead of more templated stories — 2026-10-02

The static libraries (1 200 Story Time texts, 4 800 topic activities) are templated and heavily reused:
from A2 upward every story in a stage asks the same question, and neighbouring stages share most texts.
Rather than hand-writing more of the same, the model now writes a continuing serial per learner
(`domains/stories`): a fixed, original cast and town, the learner's level and saved words as input,
one episode written ahead of time by the job loop. The model proposes; a deterministic validator
(`stories/validator.py`) decides: Dutch, length and sentence complexity per stage, vocabulary
coverage against the stage banks plus the learner's own words, every comprehension question backed by a
sentence copied from the text, regional `gij/ge` only when labelled. A failed draft is rewritten once
with the validator's findings; a second failure is shown to the learner as a failure, never as a story.
Each episode ends with a two-way choice that is fed to the next one; the next episode is not written
until the choice is made or twelve hours have passed. Episodes are labelled as generated content and
remain unreviewed by a teacher. Usage is reserved per attempt through the existing counters; two model
calls per episode at most.

## D-19 · Daily plan, points and spaced repetition — 2026-10-02

Reading an episode, answering its questions, choosing, reading aloud and reviewing words earn points
for the day (`learning_days`, one row per learner per Europe/Brussels day). A streak counts consecutive
active days; the daily goal is twenty points. Points reward doing and are never a judgement of the
learner's Dutch. Saved words (`vocab_items`) are scheduled with SM-2 (ease 1.3–∞, intervals 1 → 6 →
ease-multiplied days); a lapse brings the card back after ten minutes within the same session. The word
bank is the learner's own choice: nothing enters it unless they save it.

## D-20 · Read-aloud compares words, it does not score pronunciation — 2026-10-02

Reading a paragraph aloud sends the recording through the normal transcription path (no storage) and
reports which target words the transcriber recognised and which it did not. Points are awarded once
per paragraph when at least half the words are recognised. No accent or pronunciation score is
computed or shown, because a transcript cannot carry one.

## D-21 · A direct order is not a mistake — 2026-10-02

The first live lunch conversation answered *"Ik wil graag een broodje kip en een water"* with *"Dat kan
niet. Kies uit het aanbod."*: the rules required the need to be stated before an option could be chosen,
the model had labelled the sentence a choice, and the refusal borrowed the line meant for an option that
is not on offer. Three changes. A valid option named straight away now counts as stating the need, and
a stated need that names an option selects it, so nobody repeats themselves and the character asks for
confirmation next. A scenario can set `reason_before_choice` (the shop return does, in both variants):
the option is kept but the character asks what the problem is before anything can be confirmed. And the
"not on offer" line is only used for an option that is not on offer; a premature "yes" simply gets the
question of the current phase. The interpretation prompt is `propose-action-v3`.

## D-22 · Video lessons are rendered by the Azure avatar, written by the same gate — 2026-10-02

The learner wanted short videos on a chosen level and topic. Generative video models were considered
and set aside: they are English-first, produce clips of seconds without Dutch narration, cost
$0.10–0.50 per second and are not offered in the region used here. Azure's text-to-speech avatar (batch
synthesis) speaks the Belgian Dutch voice the platform already uses, times its own subtitles, runs in
West Europe on the existing Speech resource with the managed identity, and costs a known $1 per minute
of video. The script goes through the story validator plus a minimum of twenty seconds of speech, so a
video is a checked lesson, not a clip. Seconds of video are a usage counter like model calls; a failed
render gives them back. On a laptop the same script renders as drawn scene cards with the local voice,
so the feature works without any paid service.

## D-23 · Read-aloud points reward the attempt, not a recognition rate — 2026-10-06

D-20 awarded the read-aloud points only when the first attempt at a paragraph reached half the words,
and never afterwards: a learner who improved on a second try earned nothing, and a learner whose speech
the transcriber recognises poorly earned nothing at all, which made the threshold act as an accent proxy.
Points are now given once per paragraph on the first attempt in which any word was recognised,
whichever attempt that is; the recognised-word count is still shown and still is not a score. This is
the first application of the October 2026 rule that points reward effort and never judge the learner's
Dutch (owner decision O1 in `docs/ROADMAP.md`).

## D-24 · One colour system: brand blue for actions, one hue per skill and section, green and red for feedback — 2026-10-06

The interface had three stacked stylesheets with 356 colour literals and colour only on the episode
covers; the rest was sage and navy chosen file by file. From this change every colour is a token in
`apps/web/app/styles/tokens.css`: brand blue is the colour of every action, each skill and each section
has one hue (reading blue, listening teal, speaking violet, writing indigo, words plum, stories rose,
videos teal, conversations violet, progress neutral slate, Today and the path blue), set with
`data-accent` on a container and resolved by `lib/design/identity.ts`. Green, amber, red and the warm
orange are reserved for feedback so a tinted section never reads as right, wrong or warned; the token
test refuses an accent that borrows one of those ramps. (The first cut gave writing orange, words amber
and progress green; the adversarial review of 7 October 2026 caught the collision before release.) Every text pair the tokens promise is held to 4.5:1 and
every graphic pair to 3:1 by `tests/unit/design-tokens.test.mjs`, in `:root` and in each accent. The
"restrained navy palette" rule in LEARNING_DESIGN is replaced by this one; high-contrast text, the
generous reading measure and few technical labels stay.

## D-25 · Shared primitives own the common classes; one icon package behind `Icon` — 2026-10-07

`.button`, `.card`, `.label`, `.error` and the lesson feedback blocks were each defined in two or three
legacy stylesheets, so the winner depended on import order. From this change each primitive has one
definition in `app/styles/ui` (layer `components`) with a typed wrapper in `components/ui`; legacy
stylesheets may add contextual rules but never a bare one, which `tests/unit/css-usage.test.mjs`
enforces. The hand-drawn icon set is replaced by `lucide-react`, the first runtime UI dependency of the
web app: pinned to an exact version, imported by name so only the used glyphs ship, and kept behind
`components/Icon.tsx` so call sites never depend on the package.

## D-26 · The interface says "je"; honesty is one chip per surface and a page — 2026-10-09

The interface addressed the learner as "u" on some screens and "je" on others. From this change every
interface sentence uses "je", the register Belgian Dutch courses use with adult learners, and a unit
test refuses "u" and "uw" outside practice content. Practice phrases keep their own register: "Kunt u
dat herhalen?" is what a learner says to a stranger. The repeated notes saying that content was written
by a language model or not yet reviewed are replaced by one `HonestyChip` per generated or unreviewed
surface, which opens a short explanation in the learner's languages and links to `/over`; no surface
lost its label. Model names, check counts, the local run command and the recording format help whoever
runs the app and now show only outside production.


## D-27 · Every point comes from one recorded action; the day keeps its goal — 2026-10-09

Points used to be added to the learner's day directly from eleven places in the story, video and word
code, each guarding against double awards in its own way. From this change every award goes through one
activity service: the action is recorded as an append-only event (kind, what it was about, the Brussels
day), unique per learner, kind and a key that follows the kind's rule (once for good, once a day, or once
per request), and only a new event moves the day. A retried or simultaneous request therefore finds the
event and earns nothing, and a day's points always equal the sum of its events; days from before the
change carry one `legacy` event with their points. Point values, the day counter an action moves and its
skill live in one rules table (`domains/activity/rules.py`), unchanged for now; D-19's "points only for
story and word actions" is revised when the other practice kinds get rules (roadmap step 4.2). The day
stores the goal in force at its latest activity, and changing the goal updates the current day, so the
dot a past day shows is the goal Today showed for it. Points, streaks and goals count by the Brussels
calendar; usage allowances keep their UTC day. The streak rule is unchanged (owner decision O9).

## D-28 · Practice is graded on the server, and what the learner answered is kept — 2026-10-10

Practice items so far carried their answers to the browser and were judged there, or not at all. From this
change practice also runs as exercise sessions generated and graded by the API: a session's items are made
once from a seed and stored, the browser sees each item without its answer, and the answer comes back only
in the response to an answer. Answers, the mistakes made on words the learner had met before and the words
offered for the word bank are now stored, exported and deleted with the learner; the data rule "no learner
free text stored beyond attempts" is revised accordingly, and retention follows in P9. A word met for the
first time is never a mistake, and only the learner adds a word to the word bank (D-19's word-bank rule
stands). Every item earns one point with its first real answer, right or wrong, and a session with five
answered items earns five; a skip is not an answer, and stopping early never pays right answers more than
wrong ones: points reward practising, never a judgement of the learner's Dutch (D-19 as revised in D-27). A
stage offers sessions only above a stated content threshold, so thin material is not presented as practice;
a stage that repeats an earlier word list is offered, and labelled as review (roadmap 3.9). The keys still
sent by the stage view and Story Time are withdrawn when the lessons move onto the engine (roadmap 5.5).

## D-29 · The learner may overrule the check; "almost" is not wrong — 2026-10-10

Typed answers and sentences built from tiles are checked by code (step 3.4): a typed answer through the
tolerant comparison (ENGINEERING, "Judging an answer"), a built sentence word by word against the authored
order. Dutch often allows another right answer that no check knows (a synonym, another word order), so on
those kinds the learner may say "mijn antwoord klopt ook". The item then closes as accepted, its mistake row
is removed and it no longer appears among the missed words; it keeps the point it already earned by being
answered, and it never counts towards completing a topic or a stage. A missing accent or an article the item
forgives is correct with a note; "almost" (a slip of the keyboard, a wrong de/het where the article is
optional, two neighbouring sentences swapped) closes the item in a neutral colour and is never a mistake. A
word copied from the support-language cue is not a slip: an English spelling such as "passport" for
"paspoort" counts as another word. A flashcard is the learner's own say and writes no mistake; neither does
putting a Story Time paragraph back in order, nor a built sentence, whose other right orders the check does
not know. Boards (match pairs, de/het) are submitted whole and judged per part, so a mistake names the word
that was missed.

## D-30 · Exercise speech is cached and shadowing is heard or not heard — 2026-10-10

Exercises with speech (step 3.5) speak course text only: a word or a sentence of the library, the same for
every learner. The sound is made once per text, voice and provider and kept under `tts-cache/`; hearing it
again, or another learner hearing it, costs no audio allowance, and the cache never holds a learner's own
words. A session plans speech only while enough of the learner's audio allowance is left, and a sound that
does not play, or a microphone that does not work, closes the item without counting it as missed.
Shadowing ("zeg het na") is judged like reading aloud (D-20, D-23): the speech service's transcript is
compared with the sentence, the outcome is heard or not heard, there is no score or percentage, any
recognised word counts as heard (no threshold, as for reading aloud), heard speech earns the item's point
(D-28), and a not-heard take is never a mistake: as with reading aloud, the point comes with the take in
which speech was recognised, so a take not heard may be tried once more at once, and the second take closes
the item. The recording is not kept. The lesson, topic and
final-check listening parts are course text too and come from the same cache.

## D-31 · Topic and lesson sessions keep the course's completion rule — 2026-10-11

A topic's or the stage lesson's reading and listening run as exercise sessions (step 3.8) without changing
what completes them (CURRICULUM, TOPIC_PRACTICE): only the first answer to each authored question counts, at
finish, through the same `objective_result` (75 %, so both of a topic's two questions and all three of a
lesson's). The engine shows each answer at once and asks a miss again, so a miss put right on its second try
is practice, not a pass; a question skipped the first time counts as answered wrong; a session ended with a
question never tried records nothing (the classic form cannot be sent half-filled either). Completion is
sticky as before, a topic session records the same practice observation as the classic form (one per
session), and a lesson records none, as before. A retry session on the missed questions alone completes
nothing: a subset would loosen the 75 % rule; a full session again may. Content changed between start and
finish counts for nothing, rather than checking old answers against new questions. Speaking and writing
sessions are warm-ups on the topic's words: completion still comes from the open task and its feedback, and
typed input is never tagged as speaking. The passage's translation, or the listening transcript, joins it
once every question is answered (the browser could read the translation from the topic page before; the
session keeps the order read, answer, then check). Authored questions earn the engine's point per first
answer like every item (D-28); step 4.2 decides topic points and must not pay these twice. Final-check
content is never a source: a lesson session reads `stage.lesson` only. A topic is labelled as review of an
earlier stage only for a skill whose text it repeats word for word: the same situation with a new text is
new practice.

## D-32 · A topic starts on a card; the questions come one at a time — 2026-10-11

A practice topic (step 3.9) opens on a start card that says what will happen and whether the topic already
counts, then reading and listening run as a practice session (D-31): the passage, kept beside every
question, then the questions one at a time with feedback after each. The passage's translation, or the
transcript, can be read once every question is answered; an option's gloss appears only with its verdict,
also in the classic forms that remain (Startles, grammar, Story Time; never in the final check), because a
gloss under each option gives the answer away. Speaking and writing offer a warm-up on the topic's words or
the task straight away, and a learner sent to the task (a coach's link, a conversation choice, a writing
draft already begun) arrives at it directly, without the card. The summary says what the session did for the
topic, never in a miss colour, and offers the missed questions first; that short session never counts, so
the topic still asks for a first right answer to every question in one full session. The classic receptive
form leaves the page; its endpoint stays.
