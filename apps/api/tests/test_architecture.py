"""Import boundaries, as a ratchet.

The intended layering is domains -> ports (providers/base.py) and providers -> nothing in the domains. The
code does not fully respect that yet; the pairs below are the known exceptions. Each test compares the
current import graph with its allowlist exactly, so a new violation fails and a removed one must be taken
off the list in the same change (the lists may only shrink).
"""

from __future__ import annotations

import ast
from pathlib import Path

SRC = Path(__file__).resolve().parents[1] / "src" / "dlp"

# domain module -> adapter or composition-root module it imports (anything under dlp.providers except base)
DOMAINS_IMPORTING_ADAPTERS = frozenset(
    {
        ("domains.coaching.service", "dlp.providers.chat_openai_compatible"),
        ("domains.coaching.service", "dlp.providers.registry"),
        ("domains.content_review.service", "dlp.providers.chat_openai_compatible"),
        ("domains.content_review.service", "dlp.providers.registry"),
        ("domains.curriculum.service", "dlp.providers.registry"),
        ("domains.curriculum.topics", "dlp.providers.registry"),
        ("domains.curriculum.writing", "dlp.providers.registry"),
        ("domains.feedback.service", "dlp.providers.registry"),
        ("domains.practice.turns", "dlp.providers.registry"),
        ("domains.stories.service", "dlp.providers.chat_openai_compatible"),
        ("domains.stories.service", "dlp.providers.registry"),
        ("domains.topic_conversations.service", "dlp.providers.registry"),
        ("domains.topic_conversations.workflow", "dlp.providers.chat_openai_compatible"),
        ("domains.videos.service", "dlp.providers.chat_openai_compatible"),
        ("domains.videos.service", "dlp.providers.registry"),
    }
)

# provider module -> domain module it imports
PROVIDERS_IMPORTING_DOMAINS = frozenset({("providers.video_local", "dlp.domains.speech.audio")})

# vendor SDKs and agent frameworks that application code (domains, api) must not import directly;
# the two workflow modules keep LangGraph until the pipelines become plain functions
VENDOR_PREFIXES = ("azure", "openai", "langgraph", "langchain", "agent_framework")
APPLICATION_IMPORTING_VENDORS = frozenset(
    {
        ("domains.practice.workflow", "langgraph"),
        ("domains.topic_conversations.workflow", "langgraph"),
    }
)


def _module_name(path: Path) -> str:
    return ".".join(path.relative_to(SRC).with_suffix("").parts).removesuffix(".__init__")


def _imports(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    found: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            found.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
            found.add(node.module)
    return found


def _pairs(folder: str, matches) -> set[tuple[str, str]]:
    pairs: set[tuple[str, str]] = set()
    for path in sorted((SRC / folder).rglob("*.py")):
        module = _module_name(path)
        pairs.update((module, imported) for imported in _imports(path) if matches(imported))
    return pairs


def _assert_exact(found: set[tuple[str, str]], allowed: frozenset[tuple[str, str]], what: str) -> None:
    new = sorted(found - allowed)
    assert not new, f"new {what} (fix the import or, if unavoidable, discuss before extending the list): {new}"
    stale = sorted(allowed - found)
    assert not stale, f"{what} no longer present; remove from the allowlist: {stale}"


def test_domains_do_not_import_adapters():
    found = _pairs("domains", lambda name: name.startswith("dlp.providers") and name != "dlp.providers.base")
    _assert_exact(found, DOMAINS_IMPORTING_ADAPTERS, "domain modules importing adapters")


def test_providers_do_not_import_domains():
    found = _pairs("providers", lambda name: name.startswith(("dlp.domains", "dlp.api")))
    _assert_exact(found, PROVIDERS_IMPORTING_DOMAINS, "provider modules importing domains")


def test_application_code_does_not_import_vendor_sdks():
    def vendor(name: str) -> bool:
        return name.split(".")[0] in VENDOR_PREFIXES

    found = {(module, imported.split(".")[0]) for module, imported in _pairs("domains", vendor) | _pairs("api", vendor)}
    _assert_exact(found, APPLICATION_IMPORTING_VENDORS, "application modules importing vendor SDKs")
