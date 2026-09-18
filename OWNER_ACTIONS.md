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
6. [x] **Review and accept the Gate 1 decisions.** Accepted implicitly on 2026-09-18 ("start M2"); recorded as D-12.

## Now (M2)

7. [ ] **Have the first real conversation.** Start Ollama first (a second WSL terminal: `ollama serve`;
   the preflight row *chat model* must say `ok`), then `git pull`, `python scripts/run.py dev`, open the mission,
   step 3 *Spreken: het telefoongesprek*, "Start het gesprek", hold the button and say why you cannot
   come (for example *Ik moet werken.*), then choose one of the offered moments and confirm. The
   receptionist's line comes from `llama3.1:8b`; her offer and confirmation lines are fixed
   sentences the model may not change. Please note: whether the transcript was right, whether the
   reply made sense, the time per turn (shown under each reply, with the model name), and anything odd.
   That report moves the turn loop from `verified_workspace` to `verified_local`.
8. [ ] **Try the checkpoint once** (step 5 *Controle: de kapper*, speech only, no help, one attempt),
   or leave it for Gate 2 if you prefer to keep your single attempt for the demo.

## Later (Phase B, after M3)

7. [ ] Create the Azure resources following `docs/GO_LIVE.md` (written in M3), record the authorised
   allowance, SKUs and free/credit assumptions in `DECISIONS.md` before the first paid call.
8. [ ] Regenerate the fixed audio with the Azure `nl-BE` voice; run the full journey on the phone.
9. [ ] Arrange the language reviewer using the Gate 2 demo (what to show is written at Gate 2);
   record the outcome; only then remove the "unreviewed content" labels for approved items.
