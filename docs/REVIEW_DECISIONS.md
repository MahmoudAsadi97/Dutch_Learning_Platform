# Learning quality and release decisions

Checked 12 October 2026 against remote main `92a6963`. This update resolves the review response and
supersedes conflicting priorities in the older roadmap. It does not record a live Azure release.

## Decisions

| Area | Decision | Evidence required |
| --- | --- | --- |
| Scope | Improve existing practice, content contracts and reliability before another platform/framework. | Focused diffs and regression checks. |
| Appointment mission | The learner cannot attend and changes their own appointment. The voicemail is a reminder, not a cancellation. | Consistent Dutch, English and Persian; versioned synthetic audio; valid slots enforced in code. |
| Level names | Keep all twelve stages open. Pre-A1 is a CEFR descriptor extension; later pre-stages are internal bridges. No A3. | Source-backed four-skill targets per stage; no invented official bridge certificates. |
| Content repetition | Shared vocabulary may support spiral practice. Reused text is review, not new level coverage. | Content hashes, review status, stage-specific task expectations and a duplication audit. |
| Belgian Dutch | Accept shared standard variants; label regional/register differences from authoritative references. | Native language review. No automatic Netherlands-only blacklist from spelling alone. |
| Assessment | Four separate skill records and provisional readiness checks. Exam profiles retain their actual formats. | Original practice tasks, withheld keys, assistance recorded; no recognised certificate or predicted official pass. |
| Learning upgrades | Prioritise delayed new-context retrieval, misunderstanding repair and listen-first interpretation/revision. | First attempt preserved; assisted repair does not establish independent retention; comparison with simpler practice. |
| Writing | Keep grounded corrections, invite revision, and record coach/sample exposure before independent claims. | Original draft plus later independent writing; no override-based mastery. |
| Paid work | Account for every attempted call, conserve uncertain usage and persist spending outside business rollbacks. | Failure, timeout, replay and rollback tests. No paid-usage expansion before these pass. |
| Jobs | Check packaged database schema before claims; renew leases and fence stale completion. | PostgreSQL regression tests; drain active handlers for releases. |
| Model selection | Separate deployment replacement from agent runtime. Keep the current region until a reviewed benchmark justifies a change. | Dutch quality, cost/latency, quota and current retirement checks; target cutover before 2027-01-31. |
| Agents | Keep bounded tutoring and conversation tools; manual single-call study guide. | Measurable gain over deterministic selection and recorded turns. No additional framework now. |
| UI | Preserve the current token system, improve mobile feedback and disclose learning targets on demand. | Keyboard, RTL, 320/390px journeys and pinned screenshot checks. |
| Demo | Interactive fixtures, clearly labelled and separate from production. | Deterministic scenario checks; no simulated live provider success. |

## Commit and release rule

The owner has authorised staged commits and pushes for this work. Commit messages describe the change;
use the owner's GitHub identity and no co-author trailers. Do not use a pasted credential. Keep each
stage reviewable and validate the exact pushed revision. A GitHub commit is not an Azure deployment.

Before Azure release: record previous image digests and migration head, rehearse upgrades on populated
data, drain active jobs, pass exact-commit CI, and check sign-in and microphone on the real phone.
The current cloud workspace has no authenticated Azure session, so these checks remain live owner actions.

## Content and evidence limits

The source-backed targets are provisional instructional mappings. They do not validate every existing
word, story or task. A bank of 500 words and 100 topics is a coverage count, not level calibration.
Native review must identify the reviewer and date and bind the decision to the content hash. Nobody
has been appointed as that reviewer in the material supplied for this upgrade.

Research supports the selected learning approaches in specific settings. The platform still needs
learner trials on unseen tasks after a delay. Do not claim guaranteed speed, accent correction or
that these ideas have never appeared elsewhere.
