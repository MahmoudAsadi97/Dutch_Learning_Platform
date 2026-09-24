"""Release lifecycle checks against a disposable PostgreSQL database, never a learner database."""
from __future__ import annotations

from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url

from dlp.api.routes_health import ready
from dlp.release import migrate


def test_release_job_is_repeatable_and_runtime_cannot_migrate(database, settings):
    password = "release-test-password-32-characters"
    migrate(settings.database_url, password)
    migrate(settings.database_url, password)
    app_url = make_url(settings.database_url).set(username="dlp_app", password=password)
    app = create_engine(app_url)
    try:
        with app.connect() as connection:
            assert connection.execute(text("select count(*) from missions")).scalar_one() >= 1
            assert connection.execute(text("select has_table_privilege('learners', 'INSERT')")).scalar_one()
            for privilege in ("SELECT", "INSERT", "UPDATE", "DELETE"):
                assert connection.execute(
                    text("select has_table_privilege('topic_practice', :privilege)"), {"privilege": privilege},
                ).scalar_one()
            assert not connection.execute(text("select has_table_privilege('alembic_version', 'UPDATE')")).scalar_one()
            assert not connection.execute(text("select has_schema_privilege('public', 'CREATE')")).scalar_one()
    finally:
        app.dispose()


def test_readiness_checks_migration_head(database):
    assert ready().status_code == 200


def test_readiness_fails_closed_without_leaking_connection_error(monkeypatch):
    def failed():
        raise RuntimeError("private database credential")
    monkeypatch.setattr("dlp.api.routes_health.get_engine", failed)
    response = ready()
    assert response.status_code == 503
    assert b"private" not in response.body


def test_job_requires_explicit_credentials():
    import pytest
    with pytest.raises(ValueError, match="required"):
        migrate("", "")


def test_release_refuses_invalid_libraries_before_opening_database(monkeypatch):
    import pytest

    from dlp import release

    sequence = []
    monkeypatch.setattr(release, "curriculum", lambda: sequence.append("curriculum"))
    def invalid_library():
        sequence.append("libraries")
        raise ValueError("library coverage is incomplete")
    monkeypatch.setattr(release, "validate_all_libraries", invalid_library)
    monkeypatch.setattr(release, "create_engine", lambda *args, **kwargs: sequence.append("database"))
    with pytest.raises(ValueError, match="coverage is incomplete"):
        release.migrate("postgresql+psycopg://dlp:dlp@localhost/dlp_test", "x" * 32)
    assert sequence == ["curriculum", "libraries"]
