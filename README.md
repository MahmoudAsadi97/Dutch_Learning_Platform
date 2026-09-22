# Taalstudio — Dutch learning platform 0.2

One learner, one mission (*Een afspraak verzetten*, A2), four skills, Persian text help.
Phase A runs entirely on a laptop with local providers; Phase B connects Azure later
without rewriting application code.

The learner interface now has a focused dashboard, a five-step appointment mission, four separate
skill records, a speech studio and account/settings pages. Desktop navigation and a mobile bottom bar
share the same routes. Persian help is right-to-left; recordings and speech synthesis remain clearly
labelled. Progress comes from saved attempts, not invented scores, streaks or certificates.

For Azure setup, start with **[the release guide](docs/GO_LIVE.md)**. It lists every service, the
creation sequence, identity configuration and live acceptance checks. The release includes private
PostgreSQL, managed-identity providers, an isolated migration job, runtime health probes, dependency
locks, CI container builds and a manual OIDC deployment workflow. No Azure resources are created on push.
This is a release candidate for the scoped single-learner product, not a claim that the full future
A1–C2 curriculum or institutional product is complete.

| Part | Technology | Where |
|---|---|---|
| Web app (only public entry) | Next.js / React / TypeScript | `apps/web` |
| API (never public) | FastAPI / Pydantic / SQLAlchemy / Alembic | `apps/api` |
| Database | PostgreSQL 16 | Docker Compose |
| Blob storage | Azurite (Phase A), Azure Blob Storage (Phase B) | Docker Compose |
| Chat model | Ollama (Phase A), Azure AI Foundry (Phase B) | `apps/api/src/dlp/providers` |
| Speech | faster-whisper + Piper (Phase A), Azure Speech nl-BE (Phase B) | `apps/api/src/dlp/providers` |
| Content | one mission file with contract, scenarios and evidence expectations | `content/missions` |
| Benchmark | 40 language cases, provider-tagged results | `benchmarks/language` |

## Run it on the laptop

Prerequisites: Docker Desktop, Ollama with an instruction-tuned model installed, and either
conda (recommended, gives Python, Node and ffmpeg in one environment) or Python 3.11+, Node 22 LTS
and `ffmpeg` on the PATH.

With conda:

```
conda env create -f environment.yml
conda activate dlp
```

Then, in that environment (or with plain Python, which creates `apps/api/.venv` instead):

```
python scripts/run.py setup        # pip (API), npm (web), Playwright browser, creates .env from .env.example
# edit .env: DEV_OWNER_EMAIL, OWNER_ALLOWLIST, ASSERTION_SIGNING_KEY (32+ random characters), LOCAL_CHAT_MODEL
python scripts/run.py services     # PostgreSQL + Azurite (dev does this by itself when they are down)
python scripts/run.py migrate
python scripts/run.py fixture      # validates and loads content/missions/*/mission.json
python scripts/fetch_piper_voice.py
python scripts/run.py preflight    # what is configured and reachable; never prints secrets
python scripts/run.py dev          # API on 127.0.0.1:8000, web on http://localhost:3000
```

After a reboot, `python scripts/run.py dev` is the only command needed: it starts the Docker services
when the database is down, applies migrations, loads the content, starts `ollama serve` when nothing
answers at `LOCAL_CHAT_BASE_URL` (and stops it again with Ctrl+C), then runs the API and the web app.
The preflight row *chat model* says whether Ollama is reachable; without it a turn fails with a clear
message instead of a fake reply.
Speech recognition uses faster-whisper `small` by default; `LOCAL_STT_MODEL=medium` in `.env` is
clearly better on non-native Dutch at about three times the recognition time (roughly one second
per second of speech on a laptop CPU).

Then open <http://localhost:3000>: the mission page renders the reading step and the speaking
step (hold the button, speak, release; the receptionist answers through the local chat model and
Piper; typed input is accepted in the practice step and stored as typed evidence), the checkpoint
step (speech only, no help, one attempt), and the microphone check page runs
microphone → upload → ffmpeg → local transcription and synthetic playback.

Checks: `python scripts/run.py test` (API), `python scripts/run.py e2e` (browser tests with
fixture providers, a fixed fixture identity and the test database, independent of your `.env`), `python scripts/run.py benchmark` (plumbing dry runs),
`python scripts/run.py acceptance` (check A01). `make <task>` wraps the same commands.

## Notes for WSL 2

- Docker Desktop must have **Settings → Resources → WSL integration** switched on for the distro you
  work in; otherwise `docker` does not exist inside WSL and `services` fails.
- The task runner strips other Python installations (for example a ROS 2 `python3.10` tree) from
  `PYTHONPATH` before it starts anything, so their pytest plugins cannot break the test run.
- Before the first `e2e`, headless Chromium needs a few system libraries. Inside `apps/web` run
  `sudo env "PATH=$PATH" npx playwright install-deps chromium` once (plain `sudo npx` resets PATH
  and picks up an old system Node, which fails with a syntax error).
- `FFMPEG_MEMORY_LIMIT_MB` caps ffmpeg's virtual address space. The conda-forge ffmpeg build needs
  more than 1 GB of address space; the default is 2048. "audio conversion failed" with
  "failed to map segment" in the API log means the cap is too small.
- `dev` binds the web app on port 3000; open <http://localhost:3000> in the Windows browser.

## Going live

Azure resources have not been deployed by this update. [GO_LIVE](docs/GO_LIVE.md) covers allowance,
app registration, foundation, immutable images, the migration job, private deployment, sign-in and
publication. [VALIDATION_REPORT](VALIDATION_REPORT.md) distinguishes local/CI evidence from pending
live checks. Creation/configuration and real service, phone, language-review and recovery checks are
still required; a successful container build cannot establish those results.

## Documents

- `docs/ENGINEERING.md` — architecture, conventions, provider abstraction, trust boundaries, tests.
- `STATE.md` — milestone checkboxes and what is next.
- `VALIDATION_REPORT.md` — what was verified, how, and with which status.
- `DECISIONS.md` — decisions with their reasons.
- `OWNER_ACTIONS.md` — the short list of things only the owner can do.

All fixed Dutch content is provisional and labelled *unreviewed* until a language reviewer approves it.

## Reliability update — September 2026

The home page now shows four separate skill records alongside the mission entry point. Hints,
reading translations and listening transcripts are logged before display. Writing drafts save in order,
including erased text; moving between lesson steps waits for a successful save and offers retry if offline.
Session mutations are serialized to preserve concurrent progress updates.

Additional checks: `cd apps/web && npm run test:unit` (Node 22.6+). API and browser test databases must
end in `_test`: test cleanup intentionally refuses the normal learner database. CI requires the test
database instead of silently skipping its tests. See [the review](docs/IMPROVEMENT_REVIEW.md) for findings,
limitations and the next priorities. This update does not deploy Azure or certify language quality.
