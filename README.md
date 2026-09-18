# Dutch learning platform — release 0.1

One learner, one mission (*Een afspraak verzetten*, A2), four skills, Persian text help.
Phase A runs entirely on a laptop with local providers; Phase B connects Azure later
without rewriting application code.

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
python scripts/run.py services     # PostgreSQL + Azurite
python scripts/run.py migrate
python scripts/run.py fixture      # validates and loads content/missions/*/mission.json
python scripts/fetch_piper_voice.py
python scripts/run.py preflight    # what is configured and reachable; never prints secrets
python scripts/run.py dev          # API on 127.0.0.1:8000, web on http://localhost:3000
```

Then open <http://localhost:3000>: the mission page renders the reading step, the
microphone check page runs microphone → upload → ffmpeg → local transcription and synthetic playback.

Checks: `python scripts/run.py test` (API), `python scripts/run.py e2e` (browser tests with
fixture providers), `python scripts/run.py benchmark` (plumbing dry runs),
`python scripts/run.py acceptance` (check A01). `make <task>` wraps the same commands.

## Notes for WSL 2

- Docker Desktop must have **Settings → Resources → WSL integration** switched on for the distro you
  work in; otherwise `docker` does not exist inside WSL and `services` fails.
- The task runner strips other Python installations (for example a ROS 2 `python3.10` tree) from
  `PYTHONPATH` before it starts anything, so their pytest plugins cannot break the test run.
- Before the first `e2e`, run `sudo npx playwright install-deps chromium` once inside `apps/web`
  (headless Chromium needs a few system libraries).
- `dev` binds the web app on port 3000; open <http://localhost:3000> in the Windows browser.

## Documents

- `docs/ENGINEERING.md` — architecture, conventions, provider abstraction, trust boundaries, tests.
- `STATE.md` — milestone checkboxes and what is next.
- `VALIDATION_REPORT.md` — what was verified, how, and with which status.
- `DECISIONS.md` — decisions with their reasons.
- `OWNER_ACTIONS.md` — the short list of things only the owner can do.

All fixed Dutch content is provisional and labelled *unreviewed* until a language reviewer approves it.
