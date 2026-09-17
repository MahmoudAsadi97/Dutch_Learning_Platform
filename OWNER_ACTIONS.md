# Owner actions

Things only the owner can do. Each item is listed once; tick it when done.

## Now (before or at Gate 1)

1. [ ] **Put the private instruction files in place.** Create `instructions/` at the repository root
   (ignored by Git) and drop `PRODUCT_BRIEF.md`, `LEARNER_PROFILE.md` and the build prompt in it. They
   were not available in session 1, so the mission content, the language targets and acceptance check
   A01 are provisional (see `DECISIONS.md` D-01). Fill the desktop OS/browser field in the profile.
2. [ ] **Run the foundation on the laptop.** `python scripts/run.py setup`, edit `.env`
   (`DEV_OWNER_EMAIL`, `OWNER_ALLOWLIST`, a random 32+ character `ASSERTION_SIGNING_KEY`,
   `LOCAL_CHAT_MODEL` = a model that `ollama list` shows), then `services`, `migrate`, `fixture`,
   `python scripts/fetch_piper_voice.py`, `preflight`, `test`, `e2e`, `dev`.
3. [ ] **Microphone check with the real local providers.** Open <http://localhost:3000/speech-check>
   in the desktop browser named in the profile, hold the button, say a Dutch sentence, confirm the
   transcript comes from `local-faster-whisper`, and play the synthetic sample (`local-piper`). The first
   transcription downloads the whisper model (about 500 MB for `small`). Report the result; the
   statuses in `VALIDATION_REPORT.md` then move from `verified_workspace` to `verified_local`.
4. [ ] **Keep one real recording as a fixture.** After item 3, copy the canonical WAV of one sentence
   (the API stores it under `recordings/…` in Azurite; the request id is shown on the page) to
   `apps/api/tests/fixtures/dutch_sentence.wav` with a `dutch_sentence.json` sidecar holding the
   transcript. Until then the tests use a generated tone.
5. [ ] **Gate 1 exercise (write one test yourself).** In `apps/api/tests/test_actions.py` add a test
   that a learner cannot accept the slot `mon-1700` in the `dentist-base` scenario (it belongs to the
   hairdresser scenario). Skeleton: load the scenario like the other tests, build `ProposedAction(action="accept_slot", slot_id="mon-1700")`,
   call `apply_action`, and assert `accepted is False` and that the reason mentions "not an available slot".
   Run `python scripts/run.py test`. Commit it under your own identity.
6. [ ] **Review and accept the Gate 1 decisions** in `DECISIONS.md` (D-01 to D-10), or say which to change.

## Later (Phase B, after M3)

7. [ ] Create the Azure resources following `docs/GO_LIVE.md` (written in M3), record the authorised
   allowance, SKUs and free/credit assumptions in `DECISIONS.md` before the first paid call.
8. [ ] Regenerate the fixed audio with the Azure `nl-BE` voice; run the full journey on the phone.
9. [ ] Arrange the language reviewer using the Gate 2 demo (what to show is written at Gate 2);
   record the outcome; only then remove the "unreviewed content" labels for approved items.
