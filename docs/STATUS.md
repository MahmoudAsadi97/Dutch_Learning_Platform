# Status and roadmap

Updated 2 October 2026.

## What works today

| Area | State |
|---|---|
| Daily plan (`/`): streak, daily goal, today's episode, due words | implemented; browser and API tests |
| Story serial (`/verhalen`): generated episodes, questions, choices, glossary, Persian on request, read-aloud | implemented; first live episodes written by `gpt-4.1-mini` in Azure on 2 October; stage profiles and the rewrite feedback tuned from them |
| Word bank with spaced repetition (`/woorden`) | implemented; a live review cycle checked in Azure (2 October) |
| Twelve-stage learning path (`/leerpad`, `/learn/<stage>`): words, grammar, reading, listening, speaking, writing, final check | implemented; verified on the laptop with the real local providers (22 September) |
| Topic practice: 100 situations × 4 skills × 12 stages | implemented; static content, unreviewed |
| Guided conversations, practice coach, admin editing queue | implemented; fixture-tested |
| Role-play missions (`/missions`): appointment, lunch, return, course message | implemented; the appointment mission verified end to end on the laptop; a live lunch turn in Azure exposed the "direct order" rule, fixed as D-21 |
| Speech: push-to-talk recording → ffmpeg → faster-whisper; Piper playback | verified on the laptop |
| Azure: Container Apps, Azure OpenAI, Speech `nl-BE`, Blob, Bicep, release script | deployed to `dlp-production` (West Europe) on 2 October; synthesis (`nl-BE-DenaNeural`) and a recognition round trip, episodes and a mission turn checked signed in |

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
* The GitHub deploy workflow (`deploy.yml`) has no `production` environment yet; releases run from the
  owner's laptop with `scripts/deploy_current.sh`.

## Next steps, in order

1. Read the live serial daily for two weeks; rate episodes; keep tuning the stage profiles and the
   writer prompt from the failure reasons stored on `story_episodes.checks` (visible on a failed card
   under "Wat er niet klopte").
2. Phone run on the live site (GO_LIVE §6): microphone, read-aloud, playback, layout at 390 px.
3. Arrange a Belgian Dutch reviewer for the fixed A1–A2 pack and a sample of generated episodes
   (`docs/DEMO.md` is the walkthrough to show them).
4. Run `scripts/setup_github_deploy.sh` once so a release is one click from GitHub (`deploy.yml`).
5. Only then: more content, more missions.

## Live checklist

Done: resource group, budget alert, Azure OpenAI deployment, Speech, Storage, PostgreSQL, Container Apps
from `infra/main.bicep`; built-in authentication with the owner's account; `PAID_USAGE_ENABLED=true`;
`scripts/verify_live.py` (anonymous scope) green; signed-in checks of episodes, grading, saving, choice,
points and streak, word review, synthesis and recognition, a mission turn.
Remaining: the phone run; `verify_live.py --mode authenticated` with a session cookie; the recovery
drill (PostgreSQL point-in-time restore to a separate server).
