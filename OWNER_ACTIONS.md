# Owner actions

Things only the owner can do. Each item is listed once; tick it when done.

## Now (before or at Gate 1)

1. [ ] **Put the private instruction files in place.** Create `instructions/` at the repository root
   (ignored by Git) and drop `PRODUCT_BRIEF.md`, `LEARNER_PROFILE.md` and the build prompt in it. They
   were not available in session 1, so the mission content, the language targets and acceptance check
   A01 are provisional (see `DECISIONS.md` D-01). Fill the desktop OS/browser field in the profile.
2. [x] **Run the foundation on the laptop.** Done 2026-09-18 in WSL 2 with the conda env `dlp`:
   preflight all ok, API tests 80 passed, browser tests 18 passed.
3. [x] **Microphone check with the real local providers.** Done 2026-09-18: `local-faster-whisper`
   transcript correct, `local-piper` playback labelled `synthetic-development`.
4. [ ] **Keep one real recording as a fixture.** Record a neutral sentence on the microphone page
   (for example *Ik wil mijn afspraak verzetten.*), note the request id shown in the result table, then
   run `cd apps/api && python -m dlp.cli export-recording <request id>`. That writes
   `tests/fixtures/dutch_sentence.wav` and `dutch_sentence.json`. Commit them only if you are happy for
   your voice to be in the repository; the recording from 2026-09-18 contains your name, so prefer a fresh neutral one.
5. [x] **Gate 1 exercise.** `test_slot_from_another_scenario_is_refused` in `apps/api/tests/test_actions.py`
   was written at the owner's request on 2026-09-18 rather than by the owner; the owner runs it
   (`python scripts/run.py test`) as part of the review. A hands-on exercise is offered again at Gate 2.
6. [ ] **Review and accept the Gate 1 decisions** in `DECISIONS.md` (D-01 to D-10), or say which to change.

## Later (Phase B, after M3)

7. [ ] Create the Azure resources following `docs/GO_LIVE.md` (written in M3), record the authorised
   allowance, SKUs and free/credit assumptions in `DECISIONS.md` before the first paid call.
8. [ ] Regenerate the fixed audio with the Azure `nl-BE` voice; run the full journey on the phone.
9. [ ] Arrange the language reviewer using the Gate 2 demo (what to show is written at Gate 2);
   record the outcome; only then remove the "unreviewed content" labels for approved items.
