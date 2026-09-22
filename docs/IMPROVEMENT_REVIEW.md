# Reliability and learner experience review — 22 September 2026

## Scope

Keep release 0.1 focused on one learner and one appointment mission. Preserve the local-first providers,
four separate skill records, provisional content labels and manual Azure deployment. No paid services
or cloud infrastructure are provisioned by this maintenance update.

## Findings and changes

| Finding | Change | Regression coverage |
|---|---|---|
| GitHub browser tests failed before reaching the browser: the job created `dlp`, the runner used `dlp_test`. | Align the service and explicit test URL; required database tests fail rather than silently skip in CI. | Full database/API and Playwright workflow. |
| Hints were revealed before evidence was saved; failures were silently ignored. | Await the evidence write, keep the hint hidden on failure, offer retry, validate the requested rung server-side. | Browser failure/retry and API validation tests. |
| Reading translation and listening transcript toggles were not recorded. | Save first exposure as assistance before display; reopening the same support does not create extra events. | API support/checkpoint tests and browser journey. |
| Clearing a draft was ignored; concurrent saves could restore an older version. | Serialize saves, save empty drafts, drain pending saves before submission and lesson-step navigation, show save failures and retry. | Client unit tests plus browser clear/reload, delayed save and failed navigation tests. |
| Simultaneous requests could read the same old session JSON or open two sessions. | Lock session state during mutations, serialize session creation per learner, reject conflicting reuse of a session-start request ID. | Real PostgreSQL concurrent transactions. |
| Concurrent first-visit requests could race to create the learner. | Insert on conflict without failing, then load the winning learner record. | Concurrent identity test. |
| A rejected past-slot proposal changed the offered slots/actions before returning failure. | Perform validation before mutating appointment state. | Side-effect-free rejection test. |
| Development test cleanup could be pointed at the normal learner database. | Refuse destructive API/E2E test setup unless the database name ends in `_test`. | Pure runner safety tests and fixture guard. |
| Deployment input was interpolated directly into a shell script. | Pass the tag through an environment variable and validate its image-tag format. | Workflow review; no deployment executed. |
| Home prioritised diagnostics over the learning task. | Add a mission entry panel and four real skill cards, retaining diagnostics and usage below. | Responsive browser journey and production build. |

An acknowledged help event records exposure, not independent ability. Practice still contains bilingual
instructions and vocabulary scaffolding; the checkpoint remains the only explicitly independent mode.
No linguistic review status or certification claim has been upgraded.

## Validation

See the dated entry in `VALIDATION_REPORT.md` for actual results. Tests with fixture providers verify
software behaviour, not Belgian Dutch quality, pronunciation accuracy, or learning effectiveness.
Desktop Chromium at phone width is not a physical-phone Safari or microphone test.

## Next improvements, in order

1. Finish the actual-device speaking/checkpoint run and independent Belgian Dutch content review.
2. Benchmark the real local models on the existing labelled cases; distinguish provisional labels from
   reviewed labels before selecting or advertising a model's language quality.
3. Add version-aware cross-tab draft conflict handling. This update serializes saves in one editing
   view and serializes server state mutations, but two independent editing tabs still use last-writer-wins.
4. Add attempt deletion with verified blob cleanup/retention and a restore exercise before production.
5. Confirm cloud allowance and real Azure authentication, speech and storage through the go-live runbook.
6. Only then expand content or introduce another mission. Teacher workspaces and formal level assessments
   remain separate product work; this update does not attempt them.

Technical references: [PostgreSQL row locking](https://www.postgresql.org/docs/current/explicit-locking.html#LOCKING-ROWS)
and [GitHub workflow script-injection guidance](https://docs.github.com/en/actions/concepts/security/script-injections).
