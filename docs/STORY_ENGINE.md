# The story engine

Every learner has one continuing serial, **De Lindestraat**: a street in the invented Flemish town of
Zilverdonk with a fixed cast (Sami the bicycle mechanic, mevrouw De Clercq, Ayşe the baker, Tom the
postman, Lotte, and Baas the dog). Episodes are written by the configured chat model, checked by code,
and queued ahead of the learner so the next one is usually ready when the app opens.

## Flow

```
GET /today ──▶ ensure a series exists ──▶ ensure one unread episode is queued/ready
                                               │
                                        job: story_episode
                                               │
                        writer prompt (bible + memory + known words + stage profile)
                                               │
                               chat.complete(schema=EpisodeDraft)
                                               │
                                    validator.validate_draft
                                      ok ──▶ status ready
                                      not ok ──▶ one rewrite with the findings
                                                   ok ──▶ ready · not ok ──▶ failed (quality)
```

* `domains/stories/bible.py` — the world, the cast, the rules, and one `StageProfile` per stage
  (paragraph and word bounds, longest and mean sentence, number of new words, required vocabulary
  coverage, grammar and tone guidance).
* `domains/stories/prompts.py` — the writer prompt (Belgian Standard Dutch rules, the brief as JSON,
  the memory of previous episodes, the learner's known words, candidate new words) and the on-demand
  translation prompt.
* `domains/stories/schemas.py` — `EpisodeDraft`: title, Dutch paragraphs, English paragraphs, glossary
  (term, English and Persian meaning, example sentence), two or three questions with an `evidence`
  sentence, a recap for the memory, and two choices for the next episode.
* `domains/stories/validator.py` — the deterministic gate (see below).
* `domains/stories/service.py` — queueing, the job handler, learner actions, views.
* `domains/stories/vocab.py` — the word bank and SM-2 scheduling.
* `domains/stories/today.py` — points per day, the streak, the daily goal.
* `api/routes_stories.py` — `/today`, `/stories…`, `/words…`.

## What the validator checks

| Check | Hard failure | Warning |
|---|---|---|
| Dutch text | function-word share < 0.22 or English markers > 4 % | — |
| Paragraphs | fewer than 2 or more than max + 2 | outside the stage range |
| Words | below 60 % of the minimum or above 150 % of the maximum | outside the stage range |
| Longest sentence | more than 6 words over the stage limit | over the limit |
| Mean sentence length | — | more than 2 words over the stage aim |
| `gij/ge` | used without a glossary label | — |
| Glossary terms | more than half are not in the text | some are not in the text |
| Questions | an `evidence` sentence that is not in the text | — |
| Vocabulary coverage | more than 15 points below the stage aim | below the stage aim |
| New words | — | more than the stage's number + 4 |

Coverage counts a token as known when it is a function word, a term from the stage's vocabulary banks
(this stage and every lower stage, with simple inflections and compounds), a word the learner saved,
a glossary term, or a cast name. A draft with a hard failure or two or more warnings is rewritten once
with the findings appended to the prompt; the better of the two drafts is kept, and only a draft
without hard failures becomes an episode.

## Memory and choices

The series keeps the last twelve recaps (`story_series.memory`) with the learner's choice for each.
The writer sees the last four. An episode's two choices are offered after the questions; the chosen
label becomes `previous_choice` of the next episode. While the last read episode still has an open
choice, no new episode is queued (for at most twelve hours), so the choice actually reaches the writer.

## Themes

The theme rotates through the stage's hundred practice topics (`content/practice/<stage>.json`),
avoiding the last twelve, so each episode links to a matching topic exercise. A learner can also ask for
a theme (`POST /stories/episodes` with `theme`); at most two unread episodes are written ahead.

## Cost and limits

An episode costs at most two model calls. Each attempt reserves one call and an estimated number of
tokens through the usage counters before the call and commits the measured usage after it; a transport
failure charges the estimate rather than refunding uncertain work. With the default limits
(200 calls and 200 k tokens per day) the engine cannot run away. In the cloud profile, generation
refuses to run unless `PAID_USAGE_ENABLED=true`.

## Trying it on the laptop

```
python scripts/run.py dev                      # Ollama must be running with LOCAL_CHAT_MODEL pulled
cd apps/api && python -m dlp.cli write-episode --stage a1 --theme "op de markt"
```

The command writes one episode for the development account with the configured providers and prints
the text, the new words and the validator's findings. A local 8B model takes one to three minutes per
episode on a laptop CPU; the job loop does the same work in the background for the app. The quality
of the Dutch is the model's; the engine guarantees shape, level and consistency, not correctness. Rate
episodes with the thumbs on the reader page — ratings are stored with the episode for later review.
