# Gate 2 demo — what to show the language reviewer

The reviewer is a Dutch speaker (ideally Flemish) who judges the *language*, not the software.
Twenty minutes, on the owner's laptop, real local providers (`python scripts/run.py dev`, Ollama running).

## Before the demo

1. Start a fresh base session: on the mission page there is no "abandon" button yet, so either use a
   fresh database (`python -m dlp.cli reset-learner-data --force` against the dev database, only if
   nothing needs keeping) or simply continue the existing session — every step can be redone.
2. Have `docs/ENGINEERING.md` §6.1 open in case the reviewer asks how replies are produced.

## The walk (in this order)

| Step | Show | Ask the reviewer |
|---|---|---|
| 1 Lezen | The reminder text, the *Niet-nagekeken inhoud* label, the Persian toggle, the three help rungs, the two questions | Is the Dutch natural Belgian Standard Dutch at A2? Any word an A2 learner in Flanders would not meet? |
| 2 Luisteren | Play the clip (label `synthetic-development`), reveal the transcript, answer the question | Is the voicemail plausible? Would they accept the synthetic voice as a placeholder until the Azure `nl-BE` voice replaces it? |
| 3 Spreken | Hold the button, say a reason, choose a slot, confirm. Point at the labels: *vaste zin* vs *antwoord van het model*, the seconds, the appointment panel | Are the receptionist's fixed lines right (register, *u*, Flemish phrasing)? Are the model's free replies acceptable? Did the transcript read the learner correctly? |
| 4 Schrijven | Type a short message, show the autosave time, submit, show the word count and required words | Is the prompt clear? Are 25–80 words reasonable for A2? |
| Feedback | On each step, *Vraag feedback*. Show a point with its evidence ids and, if present, the dropped-point count | Is the feedback correct Dutch and correct *about* the learner's Dutch? Is the Persian rendering usable? |
| 5 Controle | Explain only (one attempt): speech only, no help, no typed input, one session; the owner may keep the attempt for later | Is the hairdresser scenario a fair transfer of the dentist one? |

## What the reviewer decides

- Which fixed texts may go from `unreviewed` to `reviewed` (per text; the owner records this in the
  mission file's `review_status` and reloads with `python scripts/run.py fixture`).
- Whether the fixed lines of the two scenarios need rewording (they are content, not code).
- Whether the model's free replies and feedback are good enough to keep, or should be reduced to
  fixed lines until a better local model is chosen (benchmark harness: `python scripts/run.py benchmark`).

## What not to claim

Nothing in the demo is a proficiency assessment; skill records show `practised`/`checkpoint_passed`
and the evidence behind them, never a level. Feedback is model output with citations, not a teacher's
judgement. Anything with the yellow label has not been checked by a human.
