"""Test configuration: fixture providers, the test database with migrations applied, an authenticated client."""

from __future__ import annotations

import os
import subprocess
import sys
from collections.abc import Iterator
from pathlib import Path

API_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = API_DIR.parents[1]
FIXTURES = Path(__file__).resolve().parent / "fixtures"

TEST_DATABASE_URL = os.environ.get("TEST_DATABASE_URL", "postgresql+psycopg://dlp:dlp@localhost:5432/dlp_test")

# Settings are read once; pin the test configuration before dlp is imported.
os.environ.update(
    {
        "APP_ENV": "test",
        "DEV_AUTH_ENABLED": "true",
        "DEV_OWNER_EMAIL": "owner@example.com",
        "DEV_OWNER_NAME": "Test Owner",
        "OWNER_ALLOWLIST": "owner@example.com,second@example.com",
        "ASSERTION_SIGNING_KEY": "test-signing-key-with-more-than-thirty-two-characters",
        "DATABASE_URL": TEST_DATABASE_URL,
        "CHAT_PROVIDER": "fixture",
        "STT_PROVIDER": "fixture",
        "TTS_PROVIDER": "fixture",
        "BLOB_PROVIDER": "memory",
        "JOB_LOOP_ENABLED": "false",
        "USAGE_DAILY_AUDIO_SECONDS": "120",
        "USAGE_TOTAL_AUDIO_SECONDS": "1000",
        "USAGE_DAILY_MODEL_CALLS": "20",
        "USAGE_TOTAL_MODEL_CALLS": "100",
        "USAGE_DAILY_TOKENS": "5000",
        "USAGE_TOTAL_TOKENS": "50000",
        "MAX_AUDIO_SECONDS": "12",
    }
)

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import text  # noqa: E402

from dlp.config import get_settings  # noqa: E402
from dlp.db.session import get_engine, session_scope  # noqa: E402
from dlp.domains.content.service import load_all_missions  # noqa: E402
from dlp.domains.identity.assertions import issue_assertion  # noqa: E402
from dlp.providers.registry import reset_providers  # noqa: E402

TABLES_TO_CLEAR = [
    "topic_practice",
    "curriculum_attempts",
    "curriculum_practice",
    "feedback_reports",
    "usage_reservations",
    "usage_counters",
    "evidence_records",
    "practice_turns",
    "practice_sessions",
    "skill_records",
    "audio_assets",
    "jobs",
    "pricing_entries",
    "learners",
]


def _database_available() -> bool:
    try:
        with get_engine().connect() as connection:
            connection.execute(text("select 1"))
        return True
    except Exception:  # noqa: BLE001
        return False


@pytest.fixture(scope="session")
def database() -> Iterator[None]:
    from sqlalchemy.engine import make_url

    if not (make_url(TEST_DATABASE_URL).database or "").endswith("_test"):
        pytest.fail("refusing destructive test cleanup: TEST_DATABASE_URL must name a database ending in _test")
    if not _database_available():
        if os.environ.get("REQUIRE_TEST_DATABASE", "").lower() == "true":
            pytest.fail("required test database is not reachable; integration checks must not silently skip")
        pytest.skip("test database not reachable (configure TEST_DATABASE_URL)")
    env = {**os.environ, "ALEMBIC_DATABASE_URL": TEST_DATABASE_URL}
    subprocess.run([sys.executable, "-m", "alembic", "upgrade", "head"], cwd=API_DIR, env=env, check=True,
                   capture_output=True)
    with session_scope() as session:
        load_all_missions(session)
    yield


@pytest.fixture(autouse=True)
def clean_tables(request: pytest.FixtureRequest) -> Iterator[None]:
    """Clear learner-generated data before each database test; missions stay loaded."""
    if "database" in request.fixturenames:
        with get_engine().begin() as connection:
            connection.execute(text("TRUNCATE " + ", ".join(TABLES_TO_CLEAR) + " CASCADE"))
    reset_providers()
    yield


@pytest.fixture
def settings():
    return get_settings()


@pytest.fixture
def client(database) -> Iterator[TestClient]:
    from dlp.main import app

    with TestClient(app) as test_client:
        yield test_client


def auth_headers(request_id: str = "test-request-0001", *, email: str = "owner@example.com",
                 identity_provider: str = "fixture", csrf: bool = True) -> dict[str, str]:
    token = issue_assertion(get_settings(), subject=f"{identity_provider}:{email}", email=email, name="Test Owner",
                            identity_provider=identity_provider, request_id=request_id)
    headers = {"Authorization": f"Bearer {token}", "X-Request-Id": request_id}
    if csrf:
        headers["X-Requested-With"] = "fetch"
    return headers


@pytest.fixture
def headers() -> dict[str, str]:
    return auth_headers()
