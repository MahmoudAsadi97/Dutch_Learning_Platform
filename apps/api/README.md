# API

FastAPI service for release 0.1. It is never exposed directly: the web app proxies
`/api` to it and every request carries a short-lived signed assertion.

```
python -m venv .venv && . .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -e ".[dev]"                            # add ,speech-local for faster-whisper and Piper
alembic upgrade head
python -m dlp.cli load-fixture
uvicorn dlp.main:app --host 127.0.0.1 --port 8000
pytest
```

See `docs/ENGINEERING.md` at the repository root for the architecture.
