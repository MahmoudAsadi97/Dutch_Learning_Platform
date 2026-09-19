# Architecture walkthrough (release 0.1)

Read this once, top to bottom, with the repository open; every path is real and every claim has a test
or a report row behind it. It is the hand-over narrative that `docs/ENGINEERING.md` (reference) and
`DECISIONS.md` (why) do not give.

## 1. One request, end to end

A learner presses the talk button on the speaking step.

1. `apps/web/lib/client/recorder.ts` records with `MediaRecorder` (container chosen with
   `isTypeSupported`), keeps a 400 ms tail after release, and hands the blob to
   `components/SpeakingStep.tsx`, which posts it as multipart to `/api/practice/sessions/{id}/turns/speech`
   with a fresh request id (`lib/client/api.ts`, `X-Requested-With: fetch`).
2. `apps/web/app/api/[...path]/route.ts` is the only door to the API: it drops any identity header the
   browser sent, resolves the principal (fixture identity bound to `localhost` in development, the
   platform's `X-MS-CLIENT-PRINCIPAL-*` headers in production), applies the owner allowlist, checks the
   anti-CSRF rules (custom header, `Sec-Fetch-Site`, `Origin`), signs a 60-second HS256 assertion
   (`lib/server/assertion.ts`) and forwards the body to the API, which is reachable only from here.
3. `apps/api/src/dlp/api/deps.py` validates the assertion (issuer, audience, expiry, key), maps the
   principal to a `learners` row and gives the route a `RequestContext` with the request id.
4. `api/routes_practice.py::speech_turn` runs the cheap refusals first (`ensure_turn_allowed`: session
   active, step is a conversation step of this variant, modality allowed, turn budget), then
   `domains/speech/service.py::transcribe_upload`: ffprobe, ffmpeg to mono 16 kHz PCM under a time,
   size and memory cap, usage reserved, faster-whisper (or Azure Speech), the canonical WAV stored under
   `recordings/{learner}/{request id}.wav`.
5. `domains/practice/turns.py::submit_turn` reserves two model calls and 1 800 tokens, writes a pending
   `practice_turns` row, and runs `domains/practice/workflow.py`: the LangGraph graph
   `propose_action` (model, structured) → `validate_action` (`actions.py`, code: the only authority over
   slots and commitments) → `compose_reply` (model, anchored on the scenario's fixed line, replaced by the
   fixed line on failure or contradiction). Usage is committed with the measured tokens; on a model
   failure the turn is marked failed, the reservations are released and a 502 is *returned* so the row
   commits.
6. Evidence rows are written (`transcript` + `action_result`), the session state (`appointment`,
   `step_progress`) and the speaking skill record are updated (only spoken evidence moves it, D-16),
   the reply is synthesised and stored, and the response carries the turn view; the browser appends the
   bubbles, plays the character line on its own `Audio` object and refreshes the skill records.

## 2. Where the truth lives

| Question | Answer in code |
|---|---|
| What is a mission, what must it contain? | `domains/content/schemas.py` (`MissionDocument`, strict, every fixed text labelled) |
| Which slots exist, what counts as accepted or confirmed? | `domains/practice/actions.py`; the model never decides |
| What evidence must exist before feedback? | `evidence_expectations` in the mission file, enforced by `domains/feedback/service.py::check_expectations` |
| What may feedback say? | only points that cite evidence handles the code resolves; the rest is dropped and counted |
| What counts as speaking practice? | `turns.py::_update_skill_record` — spoken evidence only |
| How much may a learner spend? | `domains/usage/service.py`, enforced in SQL before every provider call |
| Who may enter? | the web proxy's allowlist; in Azure the platform sign-in in front of it |

## 3. What is fixed and what is model output

Fixed: every Dutch text in the mission file (labelled until the reviewer approves it), the scenario's
fixed lines (opening, ask for the reason, offer of slots, confirmation, closing), the questions and
their answers, the help ladders. Model output: the reading of the learner's utterance (a proposal),
the character's free replies (labelled *antwoord van het model* in the UI, replaced by fixed lines
when they contradict the code), and feedback (labelled, with citations). Synthetic voices are labelled
`synthetic-development` locally and `azure-neural` in Azure.

## 4. What changes for Azure

Nothing in the domains. `providers/registry.py` builds Azure Speech and Blob adapters instead of the
local ones, the chat provider becomes Azure OpenAI (optional) or the fixture, the web proxy reads the
platform's identity headers instead of the fixture principal, and `infra/main.bicep` gives each tier a
managed identity so no storage or speech key exists at all (D-15).

## 5. How to check a claim

- Content: `python scripts/run.py acceptance` (A01) — the file on disk, the stored copy and the word budget agree.
- Data: the same command (A02–A06) — records, credit rules, citations, checkpoint rules and usage.
- Behaviour: `python scripts/run.py test` (API) and `python scripts/run.py e2e` (browser, fixture providers).
- Live: `scripts/verify_live.py` once deployed.
- Everything the platform knows about the learner: `GET /api/export`.
