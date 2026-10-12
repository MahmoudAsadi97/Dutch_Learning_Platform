# Existing-bank coverage audit

Run on 12 October 2026 with `scripts/audit_learning_content.py`. This inspects committed content only;
no learner data or external service is used. The audit includes the additive source lesson packs
loaded by the application. Every stage retains at least 500 vocabulary entries, 100 stories
and 100 topics with four skills. All banks retain their unreviewed language status.

| Stage | Vocabulary | Stories | Topics per skill | Terms new relative to earlier banks | Earlier reading passages | Earlier listening passages |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| pre-a1 | 501 | 101 | 101 | 501 | 0 | 0 |
| a1 | 502 | 101 | 101 | 2 | 0 | 100 |
| pre-a2 | 500 | 101 | 101 | 0 | 0 | 100 |
| a2 | 503 | 101 | 101 | 416 | 0 | 0 |
| pre-b1 | 500 | 101 | 101 | 19 | 4 | 100 |
| b1 | 503 | 101 | 101 | 0 | 100 | 100 |
| pre-b2 | 500 | 100 | 100 | 440 | 0 | 0 |
| b2 | 500 | 100 | 100 | 0 | 0 | 0 |
| pre-c1 | 500 | 100 | 100 | 0 | 0 | 0 |
| c1 | 500 | 100 | 100 | 402 | 0 | 0 |
| pre-c2 | 500 | 100 | 100 | 245 | 100 | 0 |
| c2 | 500 | 100 | 100 | 0 | 100 | 0 |

“New” means exact normalised Dutch term novelty, not new senses, mastery or estimated difficulty.
“Reused” means exact passage equality after whitespace normalisation across earlier stage banks.
The audit does not assess semantic near-duplicates, translation quality, valid questions or CEFR level.

## Decision

Retain shared words as spiral practice, but identify exact repeated passages as review. They cannot be
presented as independently calibrated new level material. Stage-specific goals now describe the
required communicative demand; they do not retroactively validate these passages.

Prioritise original, reviewed beginner listening and the A2→B1 transfer slice before writing thousands
more nominal topics. The advanced duplicate reading banks also require new tasks and review. A native
review pilot remains required. Every changed bank must rerun answerability, source-hash and final-check
isolation tests. Do not automatically paraphrase a bank and call it approved.

The six source units add original passages but do not erase repeated older material.
See [SOURCE_LESSONS.md](SOURCE_LESSONS.md) for the additions and their review status.

The audit emits exact base-bank and supplement hashes and per-topic review links into a local JSON file:

```bash
python scripts/audit_learning_content.py --json .local/content-audit.json
```
