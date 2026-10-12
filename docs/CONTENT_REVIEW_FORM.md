# Small language-review pilot

Start with the appointment-change mission and one original A2 topic. Keep language review and learner
observations as separate records. Source-linked learning goals are not proof that the current text is correct.

1. Run `python scripts/audit_learning_content.py --json .local/content-audit.json`.
2. Identify the exact mission version or topic ID and its SHA-256, plus the alignment release.
3. A fluent Belgian Standard Dutch/NT2 reviewer checks naturalness, accuracy, register, task difficulty,
   accepted standard variants and whether the task contains everything needed to answer it.
4. Check Dutch, support translations and the script before synthesising audio. Synthetic audio is still
   labelled; the reviewer checks its intelligibility separately. Do not claim a pronunciation score.
5. Record reviewer identity, date, scope, findings and decision. A changed hash invalidates the old approval.
6. Observe a learner on the revised task, then a later unfamiliar variant. Record support and task outcome;
   keep these observations separate from the reviewer's language judgement.

Do not approve all twelve banks in one blanket statement. Word counts, a model's agreement and passing
software tests do not replace this review. No reviewer has been assigned in the current project evidence.

Suggested record (pending until an actual reviewer completes it):

```json
{
  "item_id": "appointment-change",
  "content_sha256": null,
  "alignment_version": "2026.10.12.1",
  "reviewer": null,
  "reviewed_at": null,
  "scope": ["language", "level", "answerability"],
  "decision": "pending",
  "findings": []
}
```
