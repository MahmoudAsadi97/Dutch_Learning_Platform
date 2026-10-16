"""Bounded, sense-specific language references for optional writing guidance.

Only the curated local reference is read. Matching chooses relevant guidance;
it never declares learner text correct, rewrites it or makes network calls.
"""

from __future__ import annotations

import json
import logging
import os
import re
import unicodedata
from copy import deepcopy
from datetime import date
from functools import lru_cache
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

logger = logging.getLogger(__name__)

MAX_REFERENCE_BYTES = 100_000
MAX_GUIDANCE_CHARACTERS = 4_000
MAX_GUIDANCE_ENTRIES = 6
STATUSES = {
    "shared_standard", "standard_belgium", "uncertain_standard_status_belgium", "nonstandard_in_this_sense",
}
SOURCE_HOSTS = {"taaladvies.net", "www.vlaanderen.be", "onzetaal.nl"}


class UsageReferenceError(ValueError):
    """The optional curated reference cannot be safely interpreted."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise UsageReferenceError(message)


def _text(value: Any, maximum: int = 800) -> bool:
    return isinstance(value, str) and bool(value.strip()) and len(value) <= maximum


def _iso_date(value: Any) -> bool:
    try:
        return isinstance(value, str) and date.fromisoformat(value).isoformat() == value
    except ValueError:
        return False


def validate_reference(data: Any) -> None:
    """Reject unknown authority/status values rather than guessing their meaning."""
    _require(isinstance(data, dict) and type(data.get("schema_version")) is int
             and data["schema_version"] == 1, "unsupported usage-reference schema")
    _require(data.get("review_status") == "source_checked_scope_limited", "unsupported reference review status")
    _require(_text(data.get("version"), 80) and _iso_date(data.get("checked_at")), "missing reference version")
    policy = data.get("policy")
    _require(isinstance(policy, dict) and policy.get("automatic_blacklist") is False
             and policy.get("meaning_required") is True
             and policy.get("register_is_separate_from_standard_status") is True
             and policy.get("retain_acceptable_variants") is True, "unsafe usage-reference policy")
    sources = data.get("sources")
    _require(isinstance(sources, list) and 1 <= len(sources) <= 40, "invalid reference sources")
    source_ids: set[str] = set()
    for source in sources:
        _require(isinstance(source, dict), "invalid source object")
        source_id = source.get("id")
        _require(_text(source_id, 80) and source_id not in source_ids, "invalid or duplicate source ID")
        source_ids.add(source_id)
        _require(_text(source.get("url"), 600), "missing source URL")
        try:
            parsed = urlsplit(source["url"])
        except ValueError as exc:
            raise UsageReferenceError("invalid usage-reference URL") from exc
        _require(parsed.scheme == "https" and parsed.hostname in SOURCE_HOSTS
                 and not parsed.username and not parsed.password, "unapproved usage-reference authority")
        _require(source.get("checked_at") == data["checked_at"], "inconsistent reference date")
    entries = data.get("entries")
    _require(isinstance(entries, list) and 1 <= len(entries) <= 100, "invalid usage-reference entries")
    entry_ids: set[str] = set()
    for entry in entries:
        _require(isinstance(entry, dict), "invalid usage-reference entry")
        entry_id = entry.get("id")
        _require(_text(entry_id, 80) and entry_id not in entry_ids, "invalid or duplicate entry ID")
        entry_ids.add(entry_id)
        status = entry.get("status")
        _require(isinstance(status, str) and status in STATUSES, "unknown usage-reference status")
        for key in ("forms", "contexts", "source_ids"):
            values = entry.get(key)
            _require(isinstance(values, list) and 1 <= len(values) <= 16
                     and all(_text(value, 160) for value in values), f"invalid entry {key}")
        _require(set(entry["source_ids"]) <= source_ids, "unknown entry source")
        meanings = entry.get("sense")
        _require(isinstance(meanings, dict) and set(meanings) == {"nl", "en", "fa"}
                 and all(_text(value, 240) for value in meanings.values()), "invalid entry meanings")
        _require(_text(entry.get("guidance")) and _text(entry.get("register"), 80), "missing usage guidance")
        alternatives = entry.get("shared_standard_alternatives")
        _require(isinstance(alternatives, list) and len(alternatives) <= 16
                 and all(_text(value, 160) for value in alternatives), "invalid entry alternatives")


@lru_cache(maxsize=8)
def _read_reference(path: str, modified: int, size: int) -> dict:
    del modified, size  # File metadata is part of the cache key.
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise UsageReferenceError("usage reference is unreadable") from exc
    validate_reference(data)
    return data


def load_reference(content_dir: Path | None = None) -> dict:
    directory = content_dir or Path(os.environ.get("DLP_CONTENT_DIR") or Path(__file__).resolve().parents[6] / "content")
    path = directory / "alignment" / "usage-reference.json"
    try:
        stamp = path.stat()
    except OSError as exc:
        raise UsageReferenceError("usage reference is unavailable") from exc
    _require(stamp.st_size <= MAX_REFERENCE_BYTES, "usage reference exceeds its size limit")
    return deepcopy(_read_reference(str(path.resolve()), stamp.st_mtime_ns, stamp.st_size))


@lru_cache(maxsize=256)
def _form_pattern(form: str) -> re.Pattern:
    normalized = unicodedata.normalize("NFC", form).casefold()
    return re.compile(r"(?<!\w)" + r"\s+".join(re.escape(part) for part in normalized.split()) + r"(?!\w)")


def reference_guidance(text: str, *, content_dir: Path | None = None,
                       max_entries: int = MAX_GUIDANCE_ENTRIES) -> str:
    """Select whole-term references, retaining all senses of an ambiguous match.

    An invalid optional reference is logged and omitted; ordinary grounded
    writing feedback remains available under its existing cautious prompt.
    No untrusted learner substring is interpolated into a system message.
    """
    if not text or max_entries < 1:
        return ""
    try:
        reference = load_reference(content_dir)
    except UsageReferenceError:
        logger.warning("Optional writing usage reference unavailable or invalid; contextual guidance omitted.")
        return ""
    normalized = unicodedata.normalize("NFC", text[:12000]).casefold()
    groups: dict[tuple[int, int], list[dict]] = {}
    for entry in reference["entries"]:
        matches = [_form_pattern(form).search(normalized) for form in entry["forms"]]
        match = min((item for item in matches if item), key=lambda item: item.start(), default=None)
        if match:
            # Both meanings of e.g. tas must travel together. Never select the
            # bag entry alone merely because a small prompt limit was reached.
            groups.setdefault((match.start(), match.end()), []).append(entry)
    if not groups:
        return ""
    header = (
        "\nLocal source-checked usage guidance (scope limited; not proof that the draft is correct). "
        "Choose the meaning from the learner's sentence before applying an entry. A word match alone is not a verdict. "
        "Preserve acceptable Belgian variants and explain register separately. Never replace every occurrence of a form. "
        "For ambiguous forms, compare all supplied senses. These references are guidance, not mandatory edits.\n"
    )
    chosen: list[dict] = []
    ids: set[str] = set()
    for _, entries in sorted(groups.items()):
        fresh = [entry for entry in entries if entry["id"] not in ids]
        if len(chosen) + len(fresh) > min(max_entries, MAX_GUIDANCE_ENTRIES):
            continue
        records = [{"forms": entry["forms"], "meaning": entry["sense"]["en"], "status": entry["status"],
                    "register": entry["register"], "contexts": entry["contexts"],
                    "alternatives": entry["shared_standard_alternatives"], "guidance": entry["guidance"]}
                   for entry in fresh]
        candidate = header + json.dumps(chosen + records, ensure_ascii=False)
        if len(candidate) > MAX_GUIDANCE_CHARACTERS:
            continue
        chosen.extend(records)
        ids.update(entry["id"] for entry in fresh)
    return header + json.dumps(chosen, ensure_ascii=False) if chosen else ""
