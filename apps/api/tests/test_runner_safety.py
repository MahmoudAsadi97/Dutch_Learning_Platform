"""No services are started by these task-runner safety tests."""
import importlib.util
from pathlib import Path

import pytest

spec = importlib.util.spec_from_file_location("task_runner", Path(__file__).resolve().parents[3] / "scripts" / "run.py")
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)


@pytest.mark.parametrize("name", ["dlp", "production", "", "dlp_test/production"])
def test_e2e_refuses_non_test_databases(name):
    with pytest.raises(SystemExit, match="refuses to reset"):
        runner.require_test_database(f"postgresql+psycopg://user:password@localhost:5432/{name}")


def test_e2e_accepts_explicit_test_database():
    runner.require_test_database("postgresql+psycopg://user:password@localhost:5432/dlp_test")
