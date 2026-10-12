# Teaching source coverage and import workflow

Nine scanned PDFs were supplied, containing **884 PDF pages**. The two latest files add 201 pages. None has an embedded searchable text layer, and no companion recordings were supplied.

This is a source inventory and review queue. It is **not** a claim that every source word has been verified, licensed for redistribution, or incorporated into the live curriculum. A lesson can have correct software behaviour while its Dutch, translations, level suitability and feedback still need expert review.

| Source ID | File            | PDF pages |
| --------- | --------------- | --------: |
| source-01 | Dutch pdf 1.pdf |       120 |
| source-02 | Dutch pdf2.pdf  |        86 |
| source-03 | Dutch pdf3.pdf  |       121 |
| source-04 | Dutch pdf4.pdf  |       120 |
| source-05 | Dutch pdf 5.pdf |       120 |
| source-06 | Dutch pdf6.pdf  |       108 |
| source-07 | Dutch pdf7.pdf  |         8 |
| source-08 | Dutch pdf8.pdf  |       120 |
| source-09 | Dutch pdf 9.pdf |        81 |

Page numbers below are one-based PDF pages. A scanned page can contain two printed pages. Printed page numbers must not be substituted for PDF page references.

## What was inspected

The earlier source review recorded this thirty-nine-page visual selection: source-07 pages 1-8; source-04 pages 102-104; source-08 pages 1, 2, 20, 30, 43, 50, 70, 90 and 110; source-09 pages 1, 2, 12, 20, 30, 36, 37, 40, 53, 60, 63, 65, 70, 71, 73, 78, 79, 80 and 81. This complements the targeted review documented in [FOUR_SKILL_CONTENT.md](FOUR_SKILL_CONTENT.md), including the message-to-email pattern on source-06 PDF page 72. Source-09 page 37 was revisited for the new past-event unit. This is a record of selected checks, not a total of every visual check or a claim that all 884 pages were inspected.

| Visual anchors                             | Confirmed teaching patterns                                                                                                                                                                                                     |
| ------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| source-07 / 1-8                            | Time and ordinal numbers; spatial prepositions; main-clause inversion; questions; preferences; negation; modals; future and progressive expressions; conjunctions; imperative; because-clauses; articles; plurals; word classes |
| source-04 / 102-104                        | Curriculum connects situations with vocabulary, grammar, pronunciation and practical skills; family, food, clothing, transport, home and appointments                                                                           |
| source-08 / 1, 2, 20, 30                   | Introductions, spelling, greetings and formal/informal register; short vowels; negation                                                                                                                                         |
| source-08 / 50, 70, 90, 110                | Plural spelling; simultaneous events with `terwijl`; perfect tense with `hebben`/`zijn`; reflexive verbs and health vocabulary                                                                                                  |
| source-09 / 1, 2, 20, 30, 40, 60           | Social issues and chart reading; clothing; wishes and polite suggestions with `zou`; `hoeven` plus `te`; leisure and travel                                                                                                     |
| source-09 / 70, 78-81                      | Word order; irregular past and participle reference lists; relative clauses and grammatical terminology                                                                                                                         |
| source-09 / 12, 36, 37, 53, 63, 65, 71, 73 | Relative pronouns; regular past; `toen`; clausal reference; possession; posture verbs with `te`; impersonal pronouns; argument connectors; quantifiers                                                                          |

The social and administrative readings contain dated facts. Their historical statistics or descriptions of public benefits must not be copied into new lessons as current factual guidance. Original scenarios should use clearly fictional data or independently verified current facts. Source-09 page 81 is rotated and has an explicit scan correction in `scan-adjustments.json`.

## Machine extraction and private review data

`scripts/index_teaching_sources.py` renders every selected page and performs Dutch Tesseract OCR. Extraction is resumable by source hash, page, resolution, language, image channel, rotation and extractor version. `manifest.json` and `pages.json` contain the completed run's exact machine coverage and failure/empty-page counts. Missing text, low confidence and orientation problems remain review concerns even if an OCR process exits successfully.

The completed run on **12 October 2026** attempted all **884 pages**: **884 yielded nonempty text**, **0 were empty**, and **0 had process failures**. It produced **18,702 distinct surface-form candidates**. These are machine extractions, including sparse numeric labels, foreign-language glosses and uncertain fragments; they are not verified words, dictionary lemmas or a learning-coverage claim. **39 pages** have a mean optical word confidence below **55**.

Four pale-blue worksheets in source-01, PDF pages **30, 32, 34 and 36**, needed a blue-channel render at **220 dpi** instead of the default grayscale at **150 dpi**. Their recovery settings are recorded in [colour-recovery.json](../content/source-index/colour-recovery.json). The recovered text was checked against the page images, but not transcribed and verified word for word. Source-03 pages **22 and 119** remain badly blurred photographs: their sparse OCR is not a usable transcription, and clearer scans are still needed. Source-04 page **33** is primarily a body-part illustration with sparse labels, so it must not be counted as a normal prose page.

Private `QUALITY_REVIEW.json` records the low-confidence pages and visual findings. Private `EXTRACTION_RUN.json` records Tesseract **5.3.4**, the Dutch language-data hash, rendering settings and implementation commit. The cache checks the extractor version but does not fingerprint a replacement OCR engine or language-data file; use a fresh output directory if those dependencies change.

The script separates:

- **Private page records:** full unverified OCR, source hash, page number, confidence and machine grammar candidates. Default location: `.local/source-import/`, already ignored by git.
- **Private vocabulary candidates:** deduplicated surface tokens with all source-page references and confidence summaries. These are not dictionary lemmas; they include inflections, names, other languages, scanning errors, handwriting and deliberately incorrect examples. Every entry has `eligible_for_lessons: false` until separately reviewed.
- **Public metadata:** file hashes, page counts, per-page word counts, machine confidence and grammar-topic navigation tags. A strict serialization allowlist excludes OCR text, images and token lists.
- **Public concept inventory:** 40 visually supported grammar concepts and 93 illustrative vocabulary seed lemmas in nine domains. This is a small curriculum-authoring inventory, not the full source vocabulary.

Confidence values are Tesseract recognition estimates, not Dutch accuracy or pedagogical quality. Candidate vocabulary confidence is the mean of its source pages' word-confidence means, explicitly labelled as a **page-level proxy**, not confidence in that individual word. Even a high-confidence token can be a deliberate error, a proper name or handwritten answer. Automated topic matches are navigation aids and can have false positives.

Run locally after installing Python's `pymupdf`, Tesseract and its Dutch language data:

```bash
python -m pip install -r scripts/source-requirements.txt
python scripts/index_teaching_sources.py \
  --pdf-dir /path/to/private/scans \
  --language nld \
  --workers 4 \
  --dpi 150 \
  --rotations-file content/source-index/scan-adjustments.json \
  --recovery-file content/source-index/colour-recovery.json \
  --public-index content/source-index
```

For separately installed language files, add `--tessdata-dir /path/to/tessdata`. The script sets the TSV renderer directly and validates its header, so missing Tesseract config files cannot silently turn plain text into an empty successful extraction. A genuinely empty OCR result receives `ocr_empty_needs_review`, not a completed-text status. Page extraction errors are recorded without publishing captured source text. Re-running retries empty or failed pages and reuses unchanged successful pages.

Keep the source PDFs, page previews and private OCR outside tracked files. The script refuses a private output directory inside this repository unless it is under `.local/`. Do not upload the source scans or full OCR to a public repository. Content ownership and permission records remain a separate requirement; hiding a source's title does not grant redistribution rights.

## From a candidate to a teaching item

1. Check the scan, correct OCR and identify whether text is an explanation, correct example, task instruction, intentionally wrong example or handwriting.
2. Deduplicate surface forms into a lemma or useful phrase, preserving part of speech, article, inflection, meaning and context.
3. Have the Dutch form and usage checked for Belgian Standard Dutch. Avoid labelling a shared standard form as wrong merely because it is also common in the Netherlands.
4. Write a new example and English/Persian support text. Review translations separately, including directionality and register.
5. Map the item to a communication goal and stage. Do not infer CEFR level from chapter number or sentence length alone.
6. Include recognition, retrieval and productive use across reading, listening, speaking and writing; revisit the item later in a different situation.
7. Record exactly which published lesson teaches and checks it. Reviewed items can then move from the private import queue into the application dataset.

These distinctions prevent the common mistake of counting extracted tokens as taught vocabulary. No automatic source import changes a learner's mastery record or declares an item reviewed.

## Stage alignment and gaps

`content/source-index/stage-map.json` connects source concepts to the twelve stages `pre-a1`, `a1`, `pre-a2`, `a2`, `pre-b1`, `b1`, `pre-b2`, `b2`, `pre-c1`, `c1`, `pre-c2` and `c2`. Pre-stages are internal preparation stages. There is no CEFR A3 level.

Grammar is revisited in a spiral: an A1 introduction uses a short verb pattern; later stages use the same structure to explain, compare, negotiate and qualify meaning. The mapping distinguishes directly supported source concepts from original advanced extensions. A source's topic or grammar appendix does not establish a comprehensive B2-C2 curriculum, validated examination or certified CEFR outcome.

Remaining work before claiming comprehensive source coverage:

- Review and classify every relevant OCR candidate, including blurred and rotated scans, handwritten additions and overlaps.
- Map approved vocabulary and grammar to published lessons and final-test blueprints; the current concept inventory and starter lessons are not exhaustive.
- Review original advanced readings, translations and assessment criteria with a competent Belgian Dutch reviewer.
- Create original listening scripts and clearly labelled synthetic audio; no source recordings were imported.
- Build alternative assessment forms and check difficulty, answerability and scoring consistency with independent human evidence.

Story creation and future video production should use the approved lesson contract. A video remains an optional delivery format: the same learning goal, transcript, vocabulary, accessible text alternative and four-skill follow-up must remain available without it. Source illustrations, characters and text should not be copied into generated media without suitable rights.
