# Four-skill topic practice

Each of the twelve stages includes at least 100 distinct practice situations for **each** skill:
reading, listening, speaking and writing. A situation connects the four skills while giving each a
different activity. The same situation may be revisited at a later stage with different support and
language demands. These are 4,800 stage-and-skill activities, not 4,800 unrelated real-world domains.

## Learner workflow

Open a stage and choose Lezen, Luisteren, Spreken or Schrijven. The topic browser opens by default.
Search in Dutch, English or Persian, choose a category, or filter to completed or unstarted practice.
Open a topic and work on its task. The original introductory activity is still available through
Startles; the vocabulary cards and Story Time remain separate sections.

- Reading presents an original text with questions about its details and meaning.
- Listening presents a distinct message or dialogue, replay controls, an optional transcript and
  questions about the information heard. Existing synthetic speech renders the authored script.
- Speaking gives a role, purpose and criteria, then records and transcribes a short response for
  task-based feedback. Recordings remain bounded by the existing short-audio service.
- Writing specifies the recipient and purpose. A learner can request spelling/grammar corrections,
  edit the draft and submit for task feedback. Drafts are isolated by learner, stage and topic.

English and Persian remain optional support. Short beginner tasks emphasise useful phrases; later
tasks introduce explanations, register, comparison, synthesis and qualification. Advanced activities
are focused practice, not a complete C1/C2 examination or a calibrated proficiency claim.

## What progress means

The server stores practice per learner, stage, topic and skill. Reading/listening completion depends
on the submitted answers; productive completion records a substantive attempt and feedback. A
successful practice attempt does not award a final-test pass. The latest answer and previous
completion are distinct: a later retry does not erase an earlier completion.

Topic practice can fulfil the existing stage-level practice prerequisite. Completing all 100 topics
is not required to attempt a final check. Opening a topic, replaying audio or revealing a transcript
does not mark the topic complete. All stages remain accessible to admitted learners.

## Content and maintenance

`content/practice/<stage>.json` contains the topic banks. Their deterministic source builders live
under `scripts/content_build/practice_*.py`. Rebuild the four bands with:

```bash
python scripts/content_build/practice_beginner.py
python scripts/content_build/practice_intermediate.py
python scripts/content_build/practice_upper.py
python scripts/content_build/practice_advanced.py
```

These builders use checked-in original content and make no model or translation calls. Each topic has a stable ID, multilingual title/category,
language objectives, references to its stage's word bank, two receptive activities and two productive
tasks. Reading and listening questions are scored against the server's content, not browser-provided
answer keys. Existing final assessment snapshots and results are preserved.

Published content is original and remains explicitly **unreviewed**. JSON checks, count checks,
answer-range checks and software tests do not certify Dutch naturalness, translation accuracy,
question fairness or CEFR suitability. These need a competent Belgian Standard Dutch reviewer.

## Deployment

No new cloud services are required. Existing model, speech, database and allowance controls are used;
more practice may consume more of the configured usage allowance. Topic browsing is not a model call.
The release adds a database migration for topic evidence. Apply it before starting a new production
API image through the existing migration-first release process. The local `python scripts/run.py dev`
command applies migrations automatically. This source update does not itself deploy Azure.
