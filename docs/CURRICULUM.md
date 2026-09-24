# Curriculum and learning progression

The curriculum is published as structured, versioned content in
[`content/curriculum/path.json`](../content/curriculum/path.json). The learning
path has twelve stages:

`pre-A1 → A1 → pre-A2 → A2 → pre-B1 → B1 → pre-B2 → B2 → pre-C1 → C1 → pre-C2 → C2`

The `pre-` stages are internal preparation stages. A3 is not used. Stage names
describe the intended learning direction, not an independently validated CEFR
award. A final stage check assesses the particular material and communication
tasks in that unit. Completing one unit is not evidence that every descriptor of
the corresponding CEFR level has been mastered.

## A repeatable learning loop

Each stage contains:

1. An original Dutch story, with English and Persian support available according
   to the learner's selected display mode.
2. Reading comprehension questions with explanations of the answer.
3. A separate listening text and comprehension questions. Synthesised playback is
   labelled; a script is not described as a human recording from the source PDFs.
4. Grammar explanations, contextual examples and interactive checks.
5. Vocabulary definitions and examples in all three languages, plus recall
   practice in the learner interface.
6. A speaking task with an observable communication goal and a sample response
   for practice.
7. A writing task with a purpose, recipient or context, criteria and a sample
   response. Advanced examples marked `sample_is_excerpt` demonstrate part of an
   answer; the interface labels them as excerpts and retains the full task's word
   target.
8. A final check with a new reading text, new listening text and new productive
   tasks. The check reuses the learned functions in a different situation.

All stages are open to every authenticated, admitted learner. The recommended order remains visible,
but a previous pass is no longer required to open a stage. A stage's final check still requires its own
four practice skills. There is no aggregate score that can conceal an unpassed skill. Tester previews
remain separate from student results. Identity and ownership checks are unchanged.

Practice may show translations, explanations and sample responses. Assessment
responses must not include answer indices, answer explanations or model
responses before submission. A learner sees meaningful feedback and skill
results, not model identifiers, prompt versions or internal evidence IDs.

## Content coverage in this release

The extended vocabulary and Story Time banks live separately in `content/library/`, with paginated
API access. Every stage has at least 500 cards and 100 short stories of at least two paragraphs.
Cards include Dutch definitions, English/Persian meanings and contextual examples. Stories reuse
target words, add comprehension questions and support sentence replay. Adjacent stages deliberately
reuse some word families and story situations as graded retellings. These counts do not imply
6,000 different lexical roots or 1,200 unrelated plots. See `PRACTICE_LIBRARY.md`.

The current bundle contains 54 grammar activities with 55 practice questions,
326 vocabulary entries, twelve original story or scenario texts, twelve separate
practice listening scripts, and 96 objective final-check questions. Every stage
also has speaking and writing practice and final tasks. These counts describe
authored items, not reviewed mastery coverage.

| Stage | Original setting and communication focus | Grammar progression |
|---|---|---|
| pre-A1 | A newcomer finds the right group in a club; introduces themselves. | Forms of `zijn` and `heten`, name spelling, personal and possessive pronouns, basic present forms. |
| A1 | A lost key at the market; prices, shops and opening hours. | Articles, questions, clock times, ordinals, spatial prepositions, plurals and possession. |
| pre-A2 | Neighbours begin a shared garden; a cooking group changes its arrangements. | Negation, modals, preferences, plans with `gaan`, progressive forms, coordinators, requests and `hoeven te`. |
| A2 | A disrupted journey becomes a shared outing; a swimming visit needs a new plan. | Perfect tense, separable verbs, adjective endings, comparison, presentational `er`, reflexive verbs and irregular participles. |
| pre-B1 | A resident reports a leak accurately; neighbours need reliable lift updates. | Reasons with `want/omdat`, sequencing and inversion, regular and irregular past forms, `toen` and `terwijl`. |
| B1 | Volunteers adapt an event for access and capacity; students correct a study-room rumour. | Relative clauses, conditional proposals, purpose clauses, middle-field patterns, clausal reference, posture constructions, impersonal pronouns, argument connectors and quantifiers. |
| pre-B2 | A library for different users: weigh alternatives and explain a qualified recommendation. | Concessive `hoewel` clauses and cautious proposals with `zou/zouden`. |
| B2 | A new working arrangement: combine evidence and competing concerns in a clear argument. | Causal, result and exception clauses; relative clauses with prepositions. |
| pre-C1 | Redesigning a square: interpret institutional communication and distinguish claims from implications. | Nominalisation, agency and attribution in indirect speech. |
| C1 | From consultation to influence: synthesize positions for a reader who needs a defensible decision. | Precise restrictions and conditions; emphasis with `niet zozeer … als wel`. |
| pre-C2 | Public choices: preserve meaning and uncertainty when mediating a difficult text. | Concession and qualification in connected discourse; source distance with reportative `zou`. |
| C2 | Authority and interpretation: evaluate implicit positions and communicate a nuanced conclusion. | Scope of negation and restriction; conditional inversion and counterfactual consequences. |

The Dutch complexity increases through vocabulary, information density,
inference, register and the relationship between claims. Word count alone does
not define difficulty. Recorded speaking tasks are deliberately short enough for
the current audio route; they are focused oral checks rather than full advanced
oral examinations.

## Relationship to the supplied scans

The supplied collection contains 884 scanned pages across nine PDFs. Source
processing is described in [`SOURCE_COVERAGE.md`](SOURCE_COVERAGE.md) and in
[`content/source-index`](../content/source-index/). The
deduplicated concept inventory identifies 40 grammar concepts and vocabulary
domains with page references from targeted visual checks. Page-level OCR is
unverified extraction, not approved teaching content.

The published stories, questions, explanations and examples are original. They
use useful instructional patterns identified in the scans: information gaps,
reading and acting on a message, sequencing events, correcting misunderstandings,
changing register for a recipient, explaining a problem, and distinguishing
independent work from assisted practice. Textbook pages and recordings are not
redistributed through this curriculum.

The `source_coverage.grammar` map links all 40 source concept IDs to an actual
published grammar activity. These are introductory treatments, not mastery
certificates. The vocabulary coverage fields compare the curated seed lemmas to
published entries after removing leading Dutch articles and the reflexive marker
`zich`; they do not count raw OCR tokens as reviewed vocabulary. All 93 curated
seed lemmas currently have a published entry. This is deliberately distinct from
the much larger unverified OCR candidate list.

The first six stages explicitly practise the main beginner and intermediate
grammar concepts identified in the inventory. Some inventory labels cover more
than a short drill can teach: for example, the alphabet/spelling unit does not
establish acoustic mastery of every Dutch vowel. Middle-field order is taught as
a context-sensitive pattern rather than an inflexible rule. Advanced content is
an authored extension; the source collection is not presented as proof that the
advanced stages have been calibrated to CEFR standards.

This release is not an exhaustive transcription of every word in all 884 pages,
and it is not a complete A1–C2 course. It is a functional staged path with original
material, an indexed source backlog and a stable format for adding further units.
Claims of complete vocabulary coverage require verified extraction, sense
deduplication, example review and an item-by-item coverage audit. OCR output must
not be silently promoted into the reviewed lexicon: the scans include handwriting,
deliberately incorrect examples and incomplete audio references.

## Language and assessment review

The authored content remains `unreviewed` until a competent Belgian Standard
Dutch reviewer checks its naturalness, register, grammar explanations, answer
keys, question fairness and productive rubrics. English and Persian support also
require review. Tests of JSON validity, translation-field presence and answer
ranges catch structural errors; they do not certify linguistic or educational
quality.

Practice criteria describe communicative evidence. They do not assess accent
identity or turn a speech-recognition transcript into a validated pronunciation
score. A missing or uncertain provider assessment must not produce a passing
result. Deployment and provider smoke tests are recorded separately from local
content validation.

Before treating this as a complete level course, expand each stage into several
reviewed units, add delayed retrieval and independent transfer tasks, pilot item
difficulty with learners, and review assessment consistency. Keep all four skill
records separate during that expansion.

## Later video work

Future videos should be supplementary lesson assets attached to the same learning
contract: approved script, intended vocabulary and grammar, captions, transcript,
audio description where needed, comprehension activity and production-review
status. A video should not introduce new assessment facts that are missing from
the lesson data. Creating video infrastructure is not required for this release.


## Four-skill topic expansion

The four skill tabs now default to [topic practice](TOPIC_PRACTICE.md). Each stage has at least
100 distinct situations for reading, listening, speaking and writing, with a separate activity for
each skill. Topic browsing replaces the single introductory task as the default entry point;
Startles preserves that task. Existing final checks stay separate. Adjacent stages may revisit
related situations with different language demands; counts are per stage and skill.
