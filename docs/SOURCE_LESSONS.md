# From source language to original practice

The supplied Dutch scans now inform a small, additive learning pack. I use their vocabulary,
grammar patterns and communication goals to author new stories and exercises, rather than
publishing scanned pages or copying textbook passages into the course.

The first pack deliberately covers **pre-A1 through B1**. The source material does not establish
a complete B2–C2 curriculum, so those stages keep their existing content and separate review needs.
The stage assignments below are provisional teaching choices, not a validated CEFR classification.

## What is added

Each of the six stages receives two connected units. Each unit has a two-paragraph Story Time story,
a reading activity, a listening activity with an original script, a speaking task and a writing task.
The same useful language returns across the four skills, with different information to communicate.

| Stage  | Unit                                    | Language focus                  | Communication goal                                                                                           |
| ------ | --------------------------------------- | ------------------------------- | ------------------------------------------------------------------------------------------------------------ |
| pre-A1 | **Een naam op de kaart**                | Alphabet and spelling           | Recognise a name, spell it and give simple personal details.                                                 |
| A1     | **Woensdag om twee uur**                | Days and clock times            | Understand and confirm an appointment's day, time and place.                                                 |
| pre-A2 | **Geen koffie, wel water**              | Negation with _niet_ and _geen_ | State a preference and clarify what is wanted.                                                               |
| A2     | **Een tas na de markt**                 | Perfect tense                   | Recount a short everyday event and describe a practical problem.                                             |
| pre-B1 | **Toch met de trein**                   | Reasons with _omdat_            | Explain a travel choice and distinguish changed from unchanged details.                                      |
| B1     | **De tas die op de bus bleef**          | Relative clauses                | Describe a lost object clearly enough for another person to identify it.                                     |
| pre-A1 | **Hallo, ik ben Sara**                  | Personal pronouns               | Greet someone, introduce yourself and recognise details from a new speaker.                                  |
| A1     | **Waar ligt het boek?**                 | Spatial prepositions            | Describe where objects are and update their locations from a spoken message.                                 |
| pre-A2 | **Mag ik met Rosa werken?**             | Modal verbs                     | Distinguish a requirement from permission, ask politely and request repetition.                              |
| A2     | **Een bericht voor twee mensen**        | Separable verbs and register    | Explain an absence to a friend, then confirm changed classroom details in a formal email.                    |
| pre-B1 | **Toen de ketting brak**                | Past events with _toen_         | Recount a bicycle problem and communicate a changed collection time while keeping the price unchanged.       |
| B1     | **Samen, maar niet op dezelfde plaats** | Suggestions with _zou/zouden_   | Propose a workable group meeting, explain a refusal and distinguish an agreed time from an unconfirmed room. |

Together the pack adds:

- **12 stories**, each with two paragraphs and comprehension questions.
- **48 four-skill activities:** one reading, listening, speaking and writing activity per unit.
- **36 grammar examples and 12 grammar questions**, attached to existing grammar topics.
- **12 additional vocabulary cards** with meanings and example sentences; target words already present in a
  stage are reused through their existing IDs instead of being duplicated.

The second set adds six units, six stories, 24 skill activities, 18 grammar examples, six questions
and **three** new cards: _opbellen_, _meebrengen_ and _de verbinding_. Its other targets reuse existing
cards. The effective banks now contain:

| Stage  | Vocabulary cards | Stories | Topics in each skill |
| ------ | ---------------: | ------: | -------------------: |
| pre-A1 |              501 |     102 |                  102 |
| A1     |              502 |     102 |                  102 |
| pre-A2 |              500 |     102 |                  102 |
| A2     |              505 |     102 |                  102 |
| pre-B1 |              500 |     102 |                  102 |
| B1     |              504 |     102 |                  102 |

The six higher stages retain their existing 500-card, 100-story and 100-topic banks. These totals
measure available content, not native-language approval, distinct new lemmas across the whole course
or demonstrated learner mastery.

Dutch, English and Persian fields follow the existing language selector. The new cards and Dutch
practice text use the existing audio controls and configured speech provider. Any generated audio
remains synthetic; these additions do not create a pronunciation score or a language certificate.

## Where to find the units

In **Leren**, choose one of the six stages above. Select **Van woord naar gesprek** in the topic
category filter for reading, listening, speaking or writing. The same category is available in
**Story Time**. The unit title helps connect its story, listening script and communication tasks.

This is an additive pack. Existing 500-word banks, 100-story banks, skill-topic banks, stable item IDs,
saved progress and final-test content are preserved. The new content does not silently replace a
learner's previous exercise or mark unreviewed work as mastered.

The first units keep their existing `-t-source-01` and `-s-source-01` IDs. The second units append
`-t-source-02` and `-s-source-02` items instead of replacing the first ones. Each new unit adds one
grammar question and three examples to its existing grammar topic. Familiar vocabulary uses the
stage's current word IDs; a repeated target does not become a second card or new mastery evidence.

After pulling the update on the laptop, stop the running development process and restart it:

```bash
git pull --ff-only origin main
python scripts/run.py dev
```

Refresh the browser after the development server is ready. Pulling GitHub changes does not update
Azure; use the separate [release guide](GO_LIVE.md) after the release checks pass.

## Source processing and provenance

All **884 supplied PDF pages** have been processed. Processing means that each page is inventoried
and considered for text extraction; it does not mean that every photographed word is a verified
transcription. Poor scans, rotated pages, handwritten answers and intentionally wrong examples need
individual treatment. The latest run recovered nonempty text on all 884 pages, with no failed jobs.
This includes sparse numbers and uncertain fragments: nonempty text is not complete or reliable OCR.
Four pale-blue worksheets (source-01, PDF pages 30, 32, 34 and 36) use a recorded blue-channel
render at 220 dpi; the default is grayscale at 150 dpi. The badly blurred photographs on
source-03 pages 22 and 119 still need better scans. Source-04 page 33 is primarily a labelled
illustration and should not be treated as a normal prose page. An uncertain extraction must
never become an approved teaching example.

The committed reference files contain metadata and learning concepts, not the raw scanned texts:

| File                                                                 | Purpose                                                                    |
| -------------------------------------------------------------------- | -------------------------------------------------------------------------- |
| [manifest.json](../content/source-index/manifest.json)               | Source identifiers, file hashes and page counts.                           |
| [pages.json](../content/source-index/pages.json)                     | Page-level extraction and quality information.                             |
| [concepts.json](../content/source-index/concepts.json)               | Vocabulary domains and grammar concepts identified for review.             |
| [colour-recovery.json](../content/source-index/colour-recovery.json) | Reproducible page-specific render settings for the four blue worksheets.   |
| [stage-map.json](../content/source-index/stage-map.json)             | Provisional distribution of concepts across the course stages.             |
| [lesson-links.json](../content/source-index/lesson-links.json)       | Source hashes, PDF page references and exact hashes of the authored packs. |

Page references use **PDF page numbers**, which may differ from printed page numbers. Hashes identify
the exact source and lesson version being reviewed; they do not establish language accuracy or rights.

Raw scans, page images and OCR outputs stay in private, ignored **`.local`** work files. They are not
published to GitHub, exposed in the learner interface or placed in a retrieval index for the tutor.
Public practice uses original authored text. Any later reproduction of source passages or recordings
requires a separate permissions check.

## Repeating the private extraction

Install the optional `scripts/source-requirements.txt` dependencies and Tesseract with Dutch
(`nld`) language data. Keep the supplied PDFs under `.local/source-pdfs/`, then run:

```bash
python scripts/index_teaching_sources.py \
  --pdf-dir .local/source-pdfs \
  --output-dir .local/source-import \
  --public-index content/source-index \
  --language nld --dpi 150 --workers 4 \
  --rotations-file content/source-index/scan-adjustments.json \
  --recovery-file content/source-index/colour-recovery.json
```

For a standalone Dutch language-data directory, add `--tessdata-dir /path/to/tessdata`.
Nonempty cached pages are reused only when source hash, language, render resolution, channel and
rotation match. Empty recognition also tries sparse text layout. Raw outputs remain private.

## Regenerating the pack

The first six authored contracts and the deterministic builder live in
[source_lessons.py](../scripts/content_build/source_lessons.py). The second units' authored contracts
are separated into [source_lessons_lower.py](../scripts/content_build/source_lessons_lower.py)
and [source_lessons_upper.py](../scripts/content_build/source_lessons_upper.py).
Run the builder after making a change for review:

```bash
python scripts/content_build/source_lessons.py
```

It writes the six stage files under `content/source-lessons/` and updates the lesson provenance links.
Generation is deterministic and idempotent: rerunning it with unchanged contracts should produce the
same files. The builder checks required translations, source-page bounds and existing vocabulary
references. Those structural checks do not replace native language review. The loader also rejects malformed packs, foreign-stage item IDs and incomplete translations before caching them.

## What still needs review

The new Dutch text, translations, grammar examples and provisional stage assignments remain
**unreviewed** until a competent Belgian Dutch reviewer checks the exact pack version. The source
books' reliability does not automatically validate a new sentence, task or translation authored from
their concepts.

The review should check naturalness, word order, register, answerability, internal consistency and
the amount of support appropriate to each stage. Listen to the rendered audio as well as checking
its script. Pre-A1 should stay short and concrete; bridge stages should reuse familiar language to
support a harder communication task, rather than introduce an unofficial extra CEFR level.

Use the [content review form](CONTENT_REVIEW_FORM.md) to record the reviewer, date and content hash.
Learner observations remain a separate record. Neither a passing software test nor a model's agreement
is native approval or evidence that the whole stage is calibrated for an official examination.

## Validation gates

The automated checks cover source-page and pack hashes, target-word references, task-fact
consistency, unchanged final tests, authenticated routes, protected answer fields, stage-bound IDs,
and cache updates/deletions. Builder idempotence is checked by comparing output hashes after a
second unchanged run. The coverage audit includes the effective merged banks, and generator
measurements account for the added vocabulary without lowering the existing acceptance gates.

API journeys check persisted reading and listening completion. Separate browser journeys exercise
the source units across the four skills and verify independent reading completion without changing
another unit or skill's progress. Visual snapshots use the original authored A1 bank as a fixed fixture,
so content expansion does not redefine the design baseline. CI additionally exercises PostgreSQL,
migrations, screenshots and production-image builds. Check the successful CI run for the exact
release commit before deploying; this document does not turn a planned or skipped check into a pass.
These are software gates, not native-language approval or calibrated level assessment.
