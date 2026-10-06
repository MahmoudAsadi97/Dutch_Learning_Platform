"""scripts/check_model_lifecycle.py classifies a pinned deployment from the catalogue's lifecycle data; the
preflight item does the same from AZURE_CHAT_RETIRES_ON without a network call."""

from __future__ import annotations

import importlib.util
import sys
from datetime import date
from pathlib import Path

from dlp.providers.preflight import _retirement_item

SCRIPTS = Path(__file__).resolve().parents[3] / "scripts"


def _lifecycle():
    spec = importlib.util.spec_from_file_location("check_model_lifecycle", SCRIPTS / "check_model_lifecycle.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules["check_model_lifecycle"] = module
    spec.loader.exec_module(module)
    return module


def test_classify_warns_within_ninety_days_and_fails_after_retirement():
    lifecycle = _lifecycle()
    today = date(2026, 10, 6)
    assert lifecycle.classify(lifecycle="GenerallyAvailable", retires_on=date(2027, 4, 14), today=today, days=90)[0] == "ok"
    assert lifecycle.classify(lifecycle="GenerallyAvailable", retires_on=date(2026, 12, 20), today=today, days=90)[0] == "warning"
    assert lifecycle.classify(lifecycle="Deprecating", retires_on=date(2027, 9, 21), today=today, days=90)[0] == "warning"
    assert lifecycle.classify(lifecycle="Deprecated", retires_on=None, today=today, days=90)[0] == "retired"
    assert lifecycle.classify(lifecycle="GenerallyAvailable", retires_on=date(2026, 10, 5), today=today, days=90)[0] == "retired"
    assert lifecycle.classify(lifecycle="", retires_on=None, today=today, days=90) == ("ok", "no retirement date published")


def test_parse_date_accepts_iso_timestamps_and_ignores_junk():
    lifecycle = _lifecycle()
    assert lifecycle.parse_date("2027-04-14T00:00:00Z") == date(2027, 4, 14)
    assert lifecycle.parse_date("2027-04-14") == date(2027, 4, 14)
    assert lifecycle.parse_date("soon") is None and lifecycle.parse_date("") is None


def test_preflight_retirement_item_without_network():
    today = date(2026, 10, 6)
    assert _retirement_item("", today).status == "not_configured"
    assert _retirement_item("2027-04-14", today).status == "ok"
    assert _retirement_item("2026-12-01", today).status == "warning"
    assert _retirement_item("2026-10-01", today).status == "retired"
    assert _retirement_item("next year", today).status == "warning"
