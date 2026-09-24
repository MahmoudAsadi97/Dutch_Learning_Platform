# Teaching source coverage and import workflow

The owner supplied nine scanned PDFs containing **884 PDF pages**. The two latest files add 201 pages. None has an embedded searchable text layer, and no companion recordings were supplied.

This is a source inventory and review queue. It is **not** a claim that every source word has been verified, licensed for redistribution, or incorporated into the live curriculum. A lesson can have correct software behaviour while its Dutch, translations, level suitability and feedback still need expert review.

| Source ID | Owner filename | PDF pages |
|---|---|---:|
| source-01 | Dutch pdf 1.pdf | 120 |
| source-02 | Dutch pdf2.pdf | 86 |
| source-03 | Dutch pdf3.pdf | 121 |
| source-04 | Dutch pdf4.pdf | 120 |
| source-05 | Dutch pdf 5.pdf | 120 |
| source-06 | Dutch pdf6.pdf | 108 |
| source-07 | Dutch pdf7.pdf | 8 |
| source-08 | Dutch pdf8.pdf | 120 |
| source-09 | Dutch pdf 9.pdf | 81 |

Page numbers below are one-based PDF pages. A scanned page can contain two printed pages. Printed page numbers must not be substituted for PDF page references.

## What was inspected

Thirty-nine pages were visually inspected in this expansion: source-07 pages 1-8; source-04 pages 102-104; source-08 pages 1, 2, 20, 30, 43, 50, 70, 90 and 110; source-09 pages 1, 2, 12, 20, 30, 36, 37, 40, 53, 60, 63, 65, 70, 71, 73, 78, 79, 80 and 81. This complements the targeted review documented in `FOUR_SKILL_CONTENT.md`. It does not mean all 884 pages were visually checked.

| Visual anchors | Confirmed teaching patterns |
|---|---|
| source-07 / 1-8 | Time and ordinal numbers; spatial prepositions; main-clause inversion; questions; preferences; negation; modals; future and progressive expressions; conjunctions; imperative; because-clauses; articles; plurals; word classes |
| source-04 / 102-104 | Curriculum connects situations with vocabulary, grammar, pronunciation and practical skills; family, food, clothing, transport, home and appointments |
| source-08 / 1, 2, 20, 30 | Introductions, spelling, greetings and formal/informal register; short vowels; negation |
| source-08 / 50, 70, 90, 110 | Plural spelling; simultaneous events with `terwijl`; perfect tense with `hebben`/`zijn`; reflexive verbs and health vocabulary |
| source-09 / 1, 2, 20, 30, 40, 60 | Social issues and chart reading; clothing; wishes and polite suggestions with `zou`; `hoeven` plus `te`; leisure and travel |
| source-09 / 70, 78-81 | Word order; irregular past and participle reference lists; relative clauses and grammatical terminology |
| source-09 / 12, 36, 37, 53, 63, 65, 71, 73 | Relative pronouns; regular past; `toen`; clausal reference; possession; posture verbs with `te`; impersonal pronouns; argument connectors; quantifiers |

The social and administrative readings contain dated facts. Their historical statistics or descriptions of public benefits must not be copied into new lessons as current factual guidance. Original scenarios should use clearly fictional data or independently verified current facts. Source-09 page 81 is rotated and has an explicit scan correction in `scan-adjustments.json`.

## Machine extraction and private review data

`scripts/index_teaching_sources.py` renders every selected page and performs Dutch Tesseract OCR. Extraction is resumable by source hash, page, resolution, language, rotation and extractor version. `manifest.json` and `pages.json` contain the completed run's exact machine coverage and failure/empty-page counts. Missing text, low confidence and orientation problems remain review concerns even if an OCR process exits successfully.

The recorded run attempted all **884 pages**: **877 yielded text**, **7 yielded no recognised words**, and **0 had process failures**. It recognised **203,972 word tokens** and produced **22,138 distinct surface-token candidates**. These numbers include OCR noise and are not a vocabulary-size or learning-coverage claim. Fifty-four pages have a mean OCR word confidence below 50. The empty pages are source-01 pages 30, 32, 34 and 36; source-03 pages 22 and 119; source-04 page 33. They require visual diagnosis and, where appropriate, a clearer scan or another OCR pass. Both new PDFs yielded text on every page.

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
  --workers 4 \
  --dpi 110 \
  --rotations-file content/source-index/scan-adjustments.json \
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
