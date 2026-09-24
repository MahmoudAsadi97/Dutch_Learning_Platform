# Taalstudio — Dutch learning platform

A guided Belgian Standard Dutch learning path with original stories, vocabulary, grammar drills,
and separate reading, listening, speaking and writing practice.

The path follows **pre-A1 → A1 → pre-A2 → A2 → pre-B1 → B1 → pre-B2 → B2 → pre-C1 → C1 → pre-C2 → C2**.
Preparation stages are internal bridges; there is no A3. Each stage has a distinct four-part final
course check. **Every stage is open to every admitted learner**; choose the right starting point.
Practise all four skills within a stage before its final check. Passing remains a separate four-skill
record, not a condition for opening the next stage. Tester previews never manufacture student passes.

The top bar switches Dutch–English, Dutch–Persian and Dutch–Persian–English support at any time.
Dutch remains the target language. A restrained navy/blue interface puts the current learning step,
useful feedback and the next action first. Each stage also has a searchable vocabulary-card bank and **Story Time**, with explicit word/sentence
replay, short recall rounds and comprehension checks. Pre-A1 includes Dutch letter names and common
letter combinations. Writing help shows inspectable corrections and explanations without overwriting
the draft. Each of the four skill tabs opens a searchable topic browser: **100 situations per skill
per stage**, with independent answers, feedback and practice progress. The original introductory
lesson remains available through **Startles**. Four additional everyday role-play missions remain under
`/missions`: appointments, lunch, returning a purchase and course messages.

**Coverage is a growing authored course, not a completed or externally validated A1–C2 syllabus.**
The supplied scans are indexed separately, with uncertain OCR kept out of lessons. Every original
unit remains labelled as awaiting language review. Internal course checks do not award recognised
CEFR certificates or pronunciation scores. See [topic-based skill practice](docs/TOPIC_PRACTICE.md), [the extended practice library](docs/PRACTICE_LIBRARY.md), [curriculum coverage](docs/CURRICULUM.md) and
[source coverage](docs/SOURCE_COVERAGE.md) for what is included and what still needs review.

The existing Azure architecture is retained: a public authenticated Next.js web app, internal FastAPI
API, PostgreSQL, Blob Storage and managed model/speech services. No additional paid service is required
for this learning-path release. [GO_LIVE](docs/GO_LIVE.md) covers the migration and deployment gate;
[VALIDATION_REPORT](VALIDATION_REPORT.md) separates tested code from verified live behavior.

| Part | Technology | Where |
|---|---|---|
| Web app (only public entry) | Next.js / React / TypeScript | `apps/web` |
| API (never public) | FastAPI / Pydantic / SQLAlchemy / Alembic | `apps/api` |
| Database | PostgreSQL 16 | Docker Compose |
| Blob storage | Azurite (Phase A), Azure Blob Storage (Phase B) | Docker Compose |
| Chat model | Ollama (Phase A), Azure AI Foundry (Phase B) | `apps/api/src/dlp/providers` |
| Speech | faster-whisper + Piper (Phase A), Azure Speech nl-BE (Phase B) | `apps/api/src/dlp/providers` |
| Content | 12-stage path, topic-based skill practice, word/story libraries and four scenario missions | `content/curriculum`, `content/practice`, `content/library`, `content/missions` |
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

Then open <http://localhost:3000> for the learning path; `/missions` opens additional role-play practice.
The mission page renders the reading step and the speaking step (hold the button, speak, release; the receptionist answers through the local chat model and
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
