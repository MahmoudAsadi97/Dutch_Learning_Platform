# Status and roadmap

Updated 2 October 2026.

## What works today

| Area | State |
|---|---|
| Daily plan (`/`): streak, daily goal, today's episode, due words | implemented; browser and API tests |
| Story serial (`/verhalen`): generated episodes, questions, choices, glossary, Persian on request, read-aloud | implemented; verified with fixture providers in CI; real-model runs happen on the laptop |
| Word bank with spaced repetition (`/woorden`) | implemented; API tests |
| Twelve-stage learning path (`/leerpad`, `/learn/<stage>`): words, grammar, reading, listening, speaking, writing, final check | implemented; verified on the laptop with the real local providers (22 September) |
| Topic practice: 100 situations × 4 skills × 12 stages | implemented; static content, unreviewed |
| Guided conversations, practice coach, admin editing queue | implemented; fixture-tested |
| Role-play missions (`/missions`): appointment, lunch, return, course message | implemented; the appointment mission verified end to end on the laptop |
| Speech: push-to-talk recording → ffmpeg → faster-whisper; Piper playback | verified on the laptop |
| Azure adapters (chat, speech, blob), Bicep, release workflow | written and unit-tested against fixtures; nothing deployed |

Statuses in detail: `docs/VERIFICATION.md`.

## Known limits

* All fixed Dutch (curriculum, topics, libraries, missions) and every generated episode is unreviewed
  by a teacher; the interface says so.
* The static story libraries are templated and reuse texts across neighbouring stages; the generated
  serial is the path forward, the libraries remain as reference material.
* The local 8B model's Dutch and Persian are serviceable, not native; Belgian forms are enforced by the
  prompt and the validator only as far as word lists go.
* No pronunciation scoring exists anywhere, by design.
* Phone acceptance (real device, HTTPS) has not been done.

## Next steps, in order

1. Run the serial on the laptop for two weeks with `llama3.1:8b`; rate episodes; tune the stage
   profiles and the prompt from the failure reasons stored on `story_episodes.checks`.
2. Arrange a Belgian Dutch reviewer for the fixed A1–A2 pack and a sample of generated episodes
   (`docs/DEMO.md` is the walkthrough to show them).
3. Compare a stronger local model for the writer (`LOCAL_CHAT_MODEL_STRONG`) against the 8B model on
   the same themes.
4. Azure: create the resources described in `docs/GO_LIVE.md`, record the allowance, run
   `scripts/verify_live.py`, regenerate the fixed audio with the `nl-BE` voice, test on the phone.
5. Only then: more content, more missions.

## Before going live (owner checklist)

* Azure subscription, resource group and budget alert; two chat deployments; Speech `F0` or `S0`;
  storage account; PostgreSQL Flexible Server; Container Apps via `infra/main.bicep`.
* Built-in authentication registered with the real account; `OWNER_ALLOWLIST` set to it.
* `PAID_USAGE_ENABLED=true` set deliberately after the allowance is recorded in `docs/DECISIONS.md`.
* `scripts/verify_live.py` green; the fixed audio regenerated; the phone run done.
