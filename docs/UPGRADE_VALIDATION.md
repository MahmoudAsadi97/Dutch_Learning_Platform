# Learning-quality upgrade validation

Baseline: `92a6963`, 12 October 2026. Staged work: pull request #9.

## Scope actually implemented

- Owner-author commits; refreshed history references and one commit/release rule.
- Consistent appointment reminder, support text and versioned audio key.
- Shrinking/wrapping exercise grids; a 390px normal-motion animation regression.
- Pinned screenshot renderer in its own CI job; original thresholds retained.
- Database-head guard, job heartbeat and fenced completion/retry.
- Independent Azure usage reservation/settlement; one Azure chat dispatch per request; conservative
  uncertain charges and replay safeguards, including paid video narration.
- A guarded, populated 0007→head migration rehearsal in an isolated test schema.
- Twelve sourced stage contracts and eleven exam-readiness blueprints, with explicit bridge/C2 limits.
- On-demand per-skill target panel, exam explorer and its authenticated API routes.
- Content coverage/duplication audit, review form, research memo and ordered README with animation.
- Separate hosted interactive demo, with its reproducible source in `demo/`.

## Local checks

| Check | Result |
| --- | --- |
| Focused API/provider/content/schema/migration-safety tests | 101 passed; 8 PostgreSQL-dependent checks skipped |
| Stage alignment plus architecture checks | 19 passed |
| Web pure-module tests | 115 passed |
| Web component tests | 76 passed |
| Web source and test TypeScript | Passed |
| Web ESLint | Passed after correcting effect state handling |
| API Ruff | Passed with a fresh test environment |
| Next.js production build | Passed; includes `/examens` |
| Demo JS syntax and interaction checks | 12 passed |
| Demo native hosting result | Publication succeeded; owner-private |

These are scoped checks, not a full local PostgreSQL/browser run. Local dependency installation was
refreshed so type/component results use the current lockfile. No preview server or browser was available
for the demo workspace; its visual and physical-phone behaviour still needs user inspection.

## Remote checks

The early staged run passed the pinned screenshots and both production image builds, but stopped at
format/import lint. Those failures were corrected; the final pushed revision must pass all CI jobs before
merging or releasing. Inspect [PR #9](https://github.com/MahmoudAsadi97/Dutch_Learning_Platform/pull/9) and
[CI](https://github.com/MahmoudAsadi97/Dutch_Learning_Platform/actions/workflows/ci.yml) for the exact run.
Do not treat a successful earlier revision as evidence for a changed one.

Independent code review caught two uncertain-usage refund paths. Both were corrected and covered by
regressions. Review of the source is distinct from PostgreSQL execution of those tests.

## Still required before Azure activation

1. Passing exact-commit push-event CI, including populated migration and failure-accounting tests.
2. Current production migration head and previous image digests recorded; active calls/jobs/renders drained.
3. Authenticated live model, synthesis and microphone journey on the owner's actual phone and laptop.
4. Named native reviewer for the small content pilot; no existing bank is promoted to reviewed by this change.
5. Retention/deletion checks and broader evidence rules before a second learner is invited.

No authenticated Azure session was available in the upgrade workspace. Nothing here verifies a live
deployment, invoice, phone recording or recognised examination result. The demo is deliberately a fixture
showcase. Research-informed directions such as delayed new-context retrieval are demonstrated there;
they are not claimed as a completed production learning-efficacy study.
