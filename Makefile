# Thin wrapper around scripts/run.py for people who prefer make (WSL, macOS, Linux).
PY ?= python3

.PHONY: setup services migrate fixture preflight api web dev test e2e benchmark acceptance lint

setup:      ; $(PY) scripts/run.py setup
services:   ; $(PY) scripts/run.py services
migrate:    ; $(PY) scripts/run.py migrate
fixture:    ; $(PY) scripts/run.py fixture
preflight:  ; $(PY) scripts/run.py preflight
api:        ; $(PY) scripts/run.py api
web:        ; $(PY) scripts/run.py web
dev:        ; $(PY) scripts/run.py dev
test:       ; $(PY) scripts/run.py test
e2e:        ; $(PY) scripts/run.py e2e
benchmark:  ; $(PY) scripts/run.py benchmark
acceptance: ; $(PY) scripts/run.py acceptance
lint:
	cd apps/api && .venv/bin/ruff check src tests
	cd apps/web && npm run lint && npm run typecheck
