"""Explicit release job. Never run schema changes from the web server's startup command."""
from __future__ import annotations

import argparse
import os
from pathlib import Path

import psycopg
from alembic import command
from alembic.config import Config
from psycopg import sql
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session

from dlp.domains.content.service import load_all_missions

API_DIR = Path(__file__).resolve().parents[2]
LOCK_ID = 742031902


def migrate(admin_url: str, app_password: str) -> None:
    if not admin_url or len(app_password) < 24:
        raise ValueError("Migration database URL and an application password of at least 24 characters are required")
    if make_url(admin_url).get_backend_name() != "postgresql":
        raise ValueError("Migration job requires PostgreSQL")
    engine = create_engine(admin_url, hide_parameters=True, connect_args={"connect_timeout": 10})
    try:
        with engine.connect() as lock:
            if not lock.execute(text("select pg_try_advisory_lock(:key)"), {"key": LOCK_ID}).scalar_one():
                raise RuntimeError("Another release is migrating this database")
            try:
                os.environ["ALEMBIC_DATABASE_URL"] = admin_url
                config = Config(str(API_DIR / "alembic.ini"))
                config.set_main_option("script_location", str(API_DIR / "migrations"))
                command.upgrade(config, "head")
                # Only the original, versioned lesson pack is loaded. Review status is not changed here.
                with Session(engine) as session:
                    load_all_missions(session)
                    session.commit()
                url = make_url(admin_url).set(drivername="postgresql")
                with psycopg.connect(url.render_as_string(hide_password=False)) as connection:
                    with connection.cursor() as cursor:
                        cursor.execute("SELECT 1 FROM pg_roles WHERE rolname = 'dlp_app'")
                        if cursor.fetchone() is None:
                            cursor.execute("CREATE ROLE dlp_app LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE")
                        cursor.execute(sql.SQL("ALTER ROLE dlp_app PASSWORD {}").format(sql.Literal(app_password)))
                        cursor.execute("GRANT USAGE ON SCHEMA public TO dlp_app")
                        cursor.execute("GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO dlp_app")
                        cursor.execute("GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO dlp_app")
                        cursor.execute("REVOKE INSERT, UPDATE, DELETE ON alembic_version FROM dlp_app")
                        cursor.execute("REVOKE CREATE ON SCHEMA public FROM PUBLIC")
                        cursor.execute(sql.SQL("GRANT CONNECT ON DATABASE {} TO dlp_app").format(
                            sql.Identifier(url.database or "dlp")))
            finally:
                lock.execute(text("select pg_advisory_unlock(:key)"), {"key": LOCK_ID})
    finally:
        engine.dispose()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["migrate"])
    parser.parse_args()
    try:
        migrate(os.environ.get("MIGRATION_DATABASE_URL", ""), os.environ.get("DATABASE_APP_PASSWORD", ""))
    except Exception as exc:
        # A database exception may include the URL/password. Do not send it to Container Apps logs.
        print(f"Release migration failed ({type(exc).__name__}); inspect the protected release job configuration.")
        return 1
    print("Release migration and content load completed; runtime role has DML access only.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
