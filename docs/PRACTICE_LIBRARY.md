# Open practice library

Every admitted learner can open all twelve stages. The order remains a suggestion; final checks
still produce four separate results and require the four practice skills within that stage. Opening
advanced material, reviewing cards or marking a story read never creates a passing assessment record.

## Using the library

- **Words:** choose a topic or search in Dutch, English or Persian. Browse 20 cards per page. Reveal a
  meaning, replay the word and example sentence, then practise five cards through recall and retry.
- **Story Time:** browse short original stories by topic. Each has at least two paragraphs, sentence
  replay, optional support-language translations, linked vocabulary and a comprehension question.
  Retell the event in your own words after reading. Read marks stay in the current browser/account.
- **Alphabet:** pre-A1 offers 26 Dutch letter names, common letter combinations and listen-and-choose
  practice. A letter name is distinguished from its sound in a word.
- **Writing:** request spelling and grammar feedback after composing a draft. Review the original
  fragment, proposed correction and explanation. Choose whether to use the revised version; it is
  not substituted automatically, and nothing is submitted as a final-test answer.

The bank is a menu of practice, not a demand to memorise 500 words before learning to speak. Use a
small topic set, recall it on a later day and apply it in the four-skill tasks and role-play missions.

## Content and limits

The twelve banks each contain at least 500 distinct terms or useful expressions and 100 stories.
Neighbouring stages deliberately spiral some vocabulary and use graded retellings of the same
situations. These are per-stage counts, not 6,000 independent lexical roots or 1,200 unrelated plots.
The collection is original teaching material, not copied anecdote-book text and not a validated
frequency ranking of the most common Dutch words.

Every word has a Dutch explanation, English/Persian meaning and an example with support translations.
Stories connect to the words and cover varied everyday, professional and public-life contexts.
Some beginner anecdotes are only a few sentences, presented in two short paragraphs; advanced
materials are short reading practice, not substitutes for long-form advanced coursework.

All language and voice examples remain **unreviewed** pending qualified language review. Automated
checks validate structure, duplicates, counts and links. They do not establish naturalness, translation
accuracy or CEFR calibration. Synthetic speech is not a native human recording or a pronunciation grade.

## Operation

No new Azure resources are needed. Phrase playback uses the existing Speech adapter; writing review
uses the configured model and existing allowance checks. Audio is requested on a click, reused in a
bounded in-memory cache, and stopped when another clip starts. Production service quotas and existing
paid-usage controls apply. Browser microphone behaviour and actual Belgian voice quality still require
checks on the target phone.

Content lives in `content/library/<stage>.json`. Editorial source/build files are under
`scripts/content_build/`. Release validation refuses missing or structurally invalid banks before
migration. No scans, raw OCR, credentials or learner drafts belong in those content files.

## Rebuilding the authored banks

From the repository root, run:

```bash
python scripts/content_build/build_beginner_library.py
python scripts/content_build/intermediate_build.py
python scripts/content_build/upper_build.py
python scripts/content_build/advanced_library.py
```

These deterministic builders use only the checked-in original editorial sources. They do not call
models or translation services. The release holds 500 cards and 100 stories in each of 12 banks.
The early stages use brief anecdotal scenes; advanced banks use longer thematic incidents. The
advanced source pool has 750 terms and 150 stories, with 250 terms and 50 stories shared by each
pair of its three stage selections. Shared material is intentional review, not new unique content.

Edit a source, rebuild its bank, inspect the Dutch and both support translations, and rerun the
library checks. A successful build checks completeness and relationships, not language approval.
