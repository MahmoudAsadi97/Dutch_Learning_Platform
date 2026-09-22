#!/usr/bin/env python3
"""Cross-platform task runner (Windows, WSL, macOS, Linux). Usage: python scripts/run.py <task>

  setup       create the API virtualenv, install Python and Node dependencies
  services    start PostgreSQL and Azurite with Docker Compose
  migrate     apply database migrations
  fixture     validate and load the mission content
  preflight   report configured providers (no secrets)
  api         run the API on 127.0.0.1:8000
  web         run the web app on localhost:3000 (development server)
  dev         one command after a reboot: services, migrations, content, Ollama, then api + web
  test        run the API test suite
  e2e         build the web app, start api + web with fixture providers, run the browser tests
  benchmark   run the language-benchmark plumbing dry runs
  acceptance  run acceptance check A01

Reads `.env` at the repository root and passes it to every child process.
"""

from __future__ import annotations

import os
import platform
import shutil
import signal
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
API = ROOT / "apps" / "api"
WEB = ROOT / "apps" / "web"
WINDOWS = platform.system() == "Windows"


def using_active_environment() -> bool:
    """True when the runner is started from an activated conda env (other than base) or virtualenv.

    Then that interpreter runs the project and no `.venv` is created. `DLP_USE_ACTIVE_PYTHON=1` forces it.
    """
    if os.environ.get("DLP_USE_ACTIVE_PYTHON") == "1":
        return True
    conda_env = os.environ.get("CONDA_DEFAULT_ENV", "")
    if conda_env and conda_env != "base" and os.environ.get("CONDA_PREFIX"):
        return True
    return bool(os.environ.get("VIRTUAL_ENV"))


def venv_python() -> Path:
    if using_active_environment():
        return Path(sys.executable)
    return API / ".venv" / ("Scripts/python.exe" if WINDOWS else "bin/python")


def _sanitised_pythonpath(value: str) -> str:
    """Drop PYTHONPATH entries that belong to another Python (for example a ROS 2 installation's
    python3.10 site-packages): they leak incompatible pytest plugins and packages into this environment."""
    import re

    current = f"python{sys.version_info.major}.{sys.version_info.minor}"
    kept: list[str] = []
    for entry in value.split(os.pathsep):
        if not entry:
            continue
        versions = set(re.findall(r"python3\.\d+", entry.lower()))
        if "/opt/ros/" in entry or (versions and current not in versions):
            continue
        kept.append(entry)
    return os.pathsep.join(kept)


def load_env() -> dict[str, str]:
    env = dict(os.environ)
    if env.get("PYTHONPATH"):
        env["PYTHONPATH"] = _sanitised_pythonpath(env["PYTHONPATH"])
        if not env["PYTHONPATH"]:
            del env["PYTHONPATH"]
    dotenv = ROOT / ".env"
    if dotenv.exists():
        for line in dotenv.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            value = value.split(" #", 1)[0].strip().strip('"').strip("'")
            env.setdefault(key.strip(), value)
    env.setdefault("API_INTERNAL_URL", "http://127.0.0.1:8000")
    return env


def sh(command: list[str], *, cwd: Path = ROOT, env: dict[str, str] | None = None, check: bool = True) -> int:
    print("+", " ".join(command), f"(in {cwd.relative_to(ROOT) if cwd != ROOT else '.'})")
    result = subprocess.run(command, cwd=cwd, env=env or load_env(), shell=False)
    if check and result.returncode != 0:
        sys.exit(result.returncode)
    return result.returncode


def npm() -> str:
    return "npm.cmd" if WINDOWS else "npm"


def npx() -> str:
    return "npx.cmd" if WINDOWS else "npx"


def task_setup() -> None:
    if using_active_environment():
        print(f"using the active environment: {sys.executable}")
    elif not venv_python().exists():
        sh([sys.executable, "-m", "venv", str(API / ".venv")])
    python = str(venv_python())
    sh([python, "-m", "pip", "install", "--upgrade", "pip"], cwd=API)
    sh([python, "-m", "pip", "install", "-e", ".[dev]"], cwd=API)
    if os.environ.get("SPEECH_LOCAL", "1") == "1":
        # Real local speech (faster-whisper, Piper) is optional: the API runs with fixture providers without it.
        if sh([python, "-m", "pip", "install", "-e", ".[speech-local]"], cwd=API, check=False) != 0:
            print("warning: the local speech packages did not install; preflight will report them as missing")
    sh([npm(), "install", "--no-audit", "--no-fund"], cwd=WEB)
    if sh([npx(), "playwright", "install", "chromium"], cwd=WEB, check=False) != 0:
        print("warning: the Playwright browser did not install; `e2e` needs it, everything else works without it")
    if not (ROOT / ".env").exists():
        shutil.copy(ROOT / ".env.example", ROOT / ".env")
        print("created .env from .env.example; edit DEV_OWNER_EMAIL, OWNER_ALLOWLIST and ASSERTION_SIGNING_KEY")
    print("setup finished; next: services, migrate, fixture, preflight")


def task_services() -> None:
    sh(["docker", "compose", "up", "-d"])


def _database_port(env: dict[str, str]) -> tuple[str, int]:
    from urllib.parse import urlparse

    parsed = urlparse(env.get("DATABASE_URL", ""))
    return parsed.hostname or "127.0.0.1", parsed.port or 5432


def _ensure_services(env: dict[str, str] | None = None) -> None:
    """Start the Docker services when nothing listens on the database port (after a reboot, typically)."""
    env = env or load_env()
    host, port = _database_port(env)
    if host not in ("127.0.0.1", "localhost") or not _port_free(port):
        return
    if shutil.which("docker") is None:
        raise SystemExit(f"no database on {host}:{port} and Docker is not on the PATH; start PostgreSQL and Azurite first")
    print(f"no database on {host}:{port}; starting the Docker services")
    if sh(["docker", "compose", "up", "-d"], check=False) != 0:
        raise SystemExit("docker compose failed; is Docker Desktop running (with WSL integration on)?")
    deadline = time.monotonic() + 90
    while time.monotonic() < deadline:
        if not _port_free(port):
            time.sleep(2)  # the server accepts connections a moment after the port opens
            return
        time.sleep(1)
    raise SystemExit(f"the database did not come up on {host}:{port} within 90 s; check `docker compose logs postgres`")


def task_migrate() -> None:
    _ensure_services()
    sh([str(venv_python()), "-m", "alembic", "upgrade", "head"], cwd=API)


def task_fixture() -> None:
    _ensure_services()
    sh([str(venv_python()), "-m", "dlp.cli", "load-fixture"], cwd=API)


def task_preflight() -> None:
    _ensure_services()
    sh([str(venv_python()), "-m", "dlp.cli", "preflight"], cwd=API)


def task_acceptance() -> None:
    _ensure_services()
    sh([str(venv_python()), "-m", "dlp.cli", "acceptance", "--check", "all"], cwd=API)


def task_test() -> None:
    _ensure_services()
    sh([str(venv_python()), "-m", "pytest", "-q"], cwd=API)


def task_benchmark() -> None:
    sh([str(venv_python()), str(ROOT / "benchmarks" / "language" / "harness.py"), "--provider", "expected"])
    sh([str(venv_python()), str(ROOT / "benchmarks" / "language" / "harness.py"), "--provider", "wrong"])


def api_command(env: dict[str, str]) -> list[str]:
    return [str(venv_python()), "-m", "uvicorn", "dlp.main:app", "--host", env.get("API_HOST", "127.0.0.1"),
            "--port", env.get("API_PORT", "8000")]


def task_api() -> None:
    env = load_env()
    sh(api_command(env), cwd=API, env=env)


def task_web() -> None:
    env = load_env()
    sh([npm(), "run", "dev"], cwd=WEB, env=env)


def _port_free(port: int) -> bool:
    import socket

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
        return probe.connect_ex(("127.0.0.1", port)) != 0


def _require_free_ports(*ports: int) -> None:
    busy = [port for port in ports if not _port_free(port)]
    if busy:
        raise SystemExit(f"port(s) {busy} already in use; stop the other api/web process first")


def _spawn(command: list[str], cwd: Path, env: dict[str, str]) -> subprocess.Popen:
    """Start a child in its own process group so that `_stop` can end it together with its children."""
    kwargs = {}
    if WINDOWS:
        kwargs["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP  # type: ignore[attr-defined]
    else:
        kwargs["start_new_session"] = True
    return subprocess.Popen(command, cwd=cwd, env=env, **kwargs)


def _stop(process: subprocess.Popen, name: str = "process") -> None:
    """Terminate a child and its process group; escalate to SIGKILL on timeout or a second Ctrl+C."""
    if process.poll() is not None:
        return
    print(f"stopping {name}…")
    try:
        if WINDOWS:
            subprocess.run(["taskkill", "/PID", str(process.pid), "/T", "/F"], capture_output=True, check=False)
        else:
            os.killpg(process.pid, signal.SIGTERM)
        process.wait(timeout=15)
    except (Exception, KeyboardInterrupt):  # noqa: BLE001 - whatever happens, the child must die
        try:
            if not WINDOWS:
                os.killpg(process.pid, signal.SIGKILL)
        except Exception:  # noqa: BLE001
            pass
        process.kill()
        try:
            process.wait(timeout=5)
        except Exception:  # noqa: BLE001
            pass


def _wait_http(url: str, timeout: float = 60.0) -> None:
    import urllib.error
    import urllib.request

    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=2) as response:  # noqa: S310 - local URL
                if response.status < 500:
                    return
        except (urllib.error.URLError, ConnectionError, TimeoutError, OSError):
            time.sleep(0.5)
    raise SystemExit(f"timed out waiting for {url}")


def _ollama_reachable(base_url: str) -> bool:
    import urllib.error
    import urllib.request

    try:
        with urllib.request.urlopen(base_url.rstrip("/") + "/models", timeout=2) as response:  # noqa: S310 - local URL
            return response.status < 500
    except (urllib.error.URLError, ConnectionError, TimeoutError, OSError):
        return False


def _ensure_ollama(env: dict[str, str]) -> subprocess.Popen | None:
    """Start `ollama serve` when the chat provider is local and nothing answers at its endpoint.
    Returns the child when this runner started it (it is stopped with the rest), None otherwise."""
    if env.get("CHAT_PROVIDER", "local") != "local":
        return None
    base_url = env.get("LOCAL_CHAT_BASE_URL", "http://localhost:11434/v1")
    if _ollama_reachable(base_url):
        return None
    if shutil.which("ollama") is None:
        print(f"warning: nothing answers at {base_url} and `ollama` is not on the PATH; the conversation needs it")
        return None
    log_dir = ROOT / ".local"
    log_dir.mkdir(exist_ok=True)
    log = open(log_dir / "ollama.log", "ab")  # noqa: SIM115 - handed to the child process
    print(f"nothing answers at {base_url}; starting `ollama serve` (log: .local/ollama.log)")
    group: dict = {"creationflags": subprocess.CREATE_NEW_PROCESS_GROUP} if WINDOWS else {"start_new_session": True}  # type: ignore[attr-defined]
    child = subprocess.Popen(["ollama", "serve"], cwd=ROOT, env=env, stdout=log, stderr=subprocess.STDOUT, **group)
    deadline = time.monotonic() + 45
    while time.monotonic() < deadline and child.poll() is None:
        if _ollama_reachable(base_url):
            return child
        time.sleep(1)
    print("warning: ollama did not answer within 45 s; the conversation will report the model as unavailable")
    return child


def task_dev() -> None:
    """Everything a laptop needs after a reboot, in order, then the two servers."""
    env = load_env()
    _require_free_ports(int(env.get("API_PORT", "8000")), int(env.get("WEB_PORT", "3000")))
    _ensure_services(env)
    sh([str(venv_python()), "-m", "alembic", "upgrade", "head"], cwd=API, env=env)
    sh([str(venv_python()), "-m", "dlp.cli", "load-fixture"], cwd=API, env=env)
    ollama = _ensure_ollama(env)
    api = _spawn(api_command(env), API, env)
    web = _spawn([npm(), "run", "dev"], WEB, env)
    print("api on http://127.0.0.1:8000, web on http://localhost:3000 — Ctrl+C stops both")
    try:
        while api.poll() is None and web.poll() is None:
            time.sleep(1)
    except KeyboardInterrupt:
        print()
    finally:
        _stop(web, "web")
        _stop(api, "api")
        if ollama is not None:
            _stop(ollama, "ollama")


E2E_OWNER_EMAIL = "owner@example.com"


def require_test_database(url: str) -> None:
    """E2E resets learner history: never run it against the development or production database."""
    from urllib.parse import unquote, urlparse

    name = unquote(urlparse(url).path.lstrip("/"))
    if not name.endswith("_test"):
        raise SystemExit("E2E refuses to reset learner data: TEST_DATABASE_URL must name a database ending in _test")


def task_e2e() -> None:
    """Browser tests run against the test database with fixture providers and a fixed fixture identity,
    so the developer's own `.env` (owner email, local models, dev database) never influences them."""
    env = load_env()
    env.update({
        "APP_ENV": "development", "DEV_AUTH_ENABLED": "true",
        "DEV_OWNER_EMAIL": E2E_OWNER_EMAIL, "DEV_OWNER_NAME": "Owner", "OWNER_ALLOWLIST": E2E_OWNER_EMAIL,
        "E2E_OWNER_EMAIL": E2E_OWNER_EMAIL,
        "DATABASE_URL": env.get("TEST_DATABASE_URL", "postgresql+psycopg://dlp:dlp@localhost:5432/dlp_test"),
        "CHAT_PROVIDER": "fixture", "STT_PROVIDER": "fixture", "TTS_PROVIDER": "fixture", "BLOB_PROVIDER": "memory",
        "JOB_LOOP_ENABLED": "false",
    })
    require_test_database(env["DATABASE_URL"])
    _ensure_services(env)
    sh([str(venv_python()), "-m", "alembic", "upgrade", "head"], cwd=API, env=env)
    sh([str(venv_python()), "-m", "dlp.cli", "load-fixture"], cwd=API, env=env)
    # every run starts from an empty learner history, so the conversation tests are repeatable
    sh([str(venv_python()), "-m", "dlp.cli", "reset-learner-data"], cwd=API, env=env)
    _require_free_ports(int(env.get("API_PORT", "8000")), int(env.get("WEB_PORT", "3000")))
    sh([npm(), "run", "build"], cwd=WEB, env=env)
    api = _spawn(api_command(env), API, env)
    web = _spawn([npx(), "next", "start", "-p", env.get("WEB_PORT", "3000")], WEB, env)
    try:
        _wait_http("http://127.0.0.1:8000/health")
        _wait_http(f"http://localhost:{env.get('WEB_PORT', '3000')}/")
        code = sh([npx(), "playwright", "test"], cwd=WEB, env=env, check=False)
    finally:
        _stop(web, "web")
        _stop(api, "api")
    sys.exit(code)


TASKS = {name[5:]: func for name, func in globals().items() if name.startswith("task_")}


def main() -> None:
    if len(sys.argv) != 2 or sys.argv[1] not in TASKS:
        print(__doc__)
        sys.exit(2)
    TASKS[sys.argv[1]]()


if __name__ == "__main__":
    main()
