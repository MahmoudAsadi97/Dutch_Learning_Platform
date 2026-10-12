# Existing-bank coverage audit

Run on 12 October 2026 with `scripts/audit_learning_content.py`. This inspects committed content only;
no learner data or external service is used. Each stage contains 500 vocabulary entries, 100 stories
and 100 topics with four skills. All banks retain their unreviewed language status.

| Stage | Terms new relative to earlier banks | Reading passages reused from an earlier stage | Listening passages reused from an earlier stage |
| --- | ---: | ---: | ---: |
| Pre-A1 | 500 | 0 | 0 |
| A1 | 0 | 0 | 100 |
| pre-A2 | 0 | 0 | 100 |
| A2 | 416 | 0 | 0 |
| pre-B1 | 19 | 4 | 100 |
| B1 | 0 | 100 | 100 |
| pre-B2 | 440 | 0 | 0 |
| B2 | 0 | 0 | 0 |
| pre-C1 | 0 | 0 | 0 |
| C1 | 402 | 0 | 0 |
| pre-C2 | 245 | 100 | 0 |
| C2 | 0 | 100 | 0 |

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

The audit emits exact content hashes and per-topic review links into a local JSON file:

```bash
python scripts/audit_learning_content.py --json .local/content-audit.json
```
