# Learning support

This release adds three focused roles to the existing course. No new Azure service is needed.
The original 100 topics per skill per stage remain available; **ten** now also have a short,
turn-by-turn conversation. The coach recommends existing activities across all twelve stages.
The editing queue is available only to explicitly configured administrators.

## What the learner sees

- Home: **Jouw volgende oefening**. Choose a stage and open any of three suggested activities.
  Reading this plan is free of model calls. After practice, an explicit button can request a model
  ordering of the same vetted activities; uncertainty returns the useful deterministic plan.
- Stage → Spreken → a supported topic → **Oefen dit gesprek**. Choose typed preparation or
  microphone responses. Hear the partner using the existing play button; playback is deliberate.
  Follow-up questions, a hint and repetition support a concrete communication goal.
- Each conversation lasts at most six learner actions and has three goals. Asking for a hint or
  repetition counts as assistance and a turn. Finishing early records partial practice; it does not
  invent a failure. The summary distinguishes accomplished, assisted and remaining goals.
- Dutch, English and Persian support follows the existing top-bar choice. Raw model names, prompt
  identifiers and evidence UUIDs stay out of learner-facing feedback.

| Stage | Topic | Conversation |
|---|---|---|
| A1 | `a1-t004` | Introduce yourself to a neighbour and arrange a visit. |
| A1 | `a1-t019` | Ask at the station, request repetition and confirm the platform. |
| A1 | `a1-t026` | Check a classroom instruction, borrow a pencil and return it. |
| A2 | `a2-t002` | Resolve conflicting dates and prepare the requested documents. |
| A2 | `a2-t016` | Find a kitchen object and agree where to leave it. |
| A2 | `a2-t027` | Ask for workplace guidance and wait for an explanation. |
| B1 | `b1-t034` | Correct an empty attachment and request confirmation. |
| B1 | `b1-t049` | Explain a poor fit and compare two shirts. |
| B2 | `b2-t003` | Propose a fair rota within an actual availability constraint. |
| B2 | `b2-t014` | Allocate shared rooms and agree how to evaluate the arrangement. |

The extra facts are explicitly introduced as a fictional rehearsal, so they do not silently alter
the reading/listening activity attached to the same topic. These are original, **unreviewed** scripts.
Script/schema checks and model reviews cannot establish native-language quality or calibrated difficulty.

## Responsibilities and limits

| Role | Model may do | Application decides |
|---|---|---|
| Conversation partner | Interpret the current learner response and quote supporting words. | Ownership, turn order, factual options, assistance, canonical replies and completion. |
| Practice coach | Reorder exactly three allowed activities with their supplied evidence references. | Candidates, reasons, stale-content filtering, links and four separate skill histories. |
| Content review assistant | Suggest issues in grounding, ambiguity, language, translation, difficulty or repetition. | Admin permission, bounded batch, cache version, exact quoted location and review status. |

The conversation graph is `interpret → validate → compose`. It has no open tool loop, arbitrary
database tool, web access or ability to write lesson files. Language understanding remains fallible;
required anchors and factual choices provide a conservative check, not a semantic proof. A valid
unanticipated paraphrase may need clarification. Typed work is labelled typed preparation; a speech
transcript is never treated as evidence of accent, pronunciation or speaking fluency.

No helper awards a final-check pass, locks a stage or declares CEFR mastery. Attempt history is
append-only from this release onward; historical overwritten attempts cannot be reconstructed.
The coach uses a bounded window of 100 recent observations and needs at least two separate assessed
attempts before describing repeated difficulty. Changed source versions are not used to diagnose
the current task. The learner can ignore the plan and choose any open level or topic.

## Cost and recovery

- Browsing, starting a conversation, explicit hint/repeat actions and the default coach plan make
  no model call. A submitted conversation response uses one `complete_once` request with a 400-token
  output ceiling. Speech recognition and explicit playback use the existing separate allowances.
- Coach ordering uses at most one request with a 600-token output ceiling and caches the settled
  result against history and policy. No-response and malformed-response paths fall back visibly.
- Editorial batches contain one to five topics, one job per topic and one provider attempt per
  generation, with at most 1,600 output tokens. Input size and returned issue count are bounded.
  The stronger configured model is reused; if absent, the existing small deployment is reused.
- Stable client identifiers make completed conversation turns and explicit topic submissions
  replayable without double-scoring. Conflicting payloads are refused. Retries after uncertain provider
  failures remain deliberate; conservative usage is retained when a response may have been billed.
- Editorial work commits a durable running claim and reservations before calling the provider.
  A recovered interrupted job never silently repeats that call. Inspect and explicitly retry a failed
  review. An interrupted reservation may need operator reconciliation rather than automatic refund.
- Allowances are application counters, not an exact invoice or universal financial hard cap. A process
  crash between a conversation/coach call and its database commit can leave uncertain accounting;
  compare provider billing during live testing. Legacy retrying workflows retain their existing limits.

## Admin editing workflow

In Settings, **Redactiewachtrij** shows authored topics and their cached suggestions. Access requires
membership in `CURRICULUM_ADMIN_EMAILS`; ordinary admitted learners cannot call its API. Request a
small selection, refresh its status and inspect quoted issues. Only authored content is sent to this
reviewer; learner answers, recordings and learner history are not included. Cache keys include the
content version, review policy and configured model identity. Old findings never attach to new content.

Every result still needs human review, including a result with no findings. Apply verified edits through
the versioned content source and rebuild process; the reviewer has no publishing authority. This pilot
reviews the four-skill topic packs, not every vocabulary card, story or conversation script.

## Updating an existing installation

Pull main after its checks pass and restart `python scripts/run.py dev`. It applies migration
`0005_learning_support`. For Azure, build both images and run the existing migration-first deployment;
do not ship only the web image. The API image packages `content/conversations/pilot.json` and validates
all conversation/topic references before the migration job changes the database. The existing warm
API job loop handles editorial requests. No new queue service or agent hosting resource is needed.

Tests cover forced invalid facts, learner isolation, replay conflicts, provider failures, allowance
rejection, interrupted editorial jobs, versioned cache behavior and migration permissions. Browser
tests cover retries, resumed turns, draft preservation, audio/navigation guards, accessible 320-pixel
layouts, language support and coach deep links. These use fixtures; live Azure, physical-phone audio
and qualified Belgian Dutch review remain separate owner checks.
