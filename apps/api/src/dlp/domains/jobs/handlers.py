"""The one place that makes every job handler known to the registry.

Handlers register themselves when their module is imported (`@registry.register(...)` in the stories,
videos and content-review services). The API imports those modules through its routers, but a one-shot
worker such as `python -m dlp.cli run-jobs` does not, so it used to miss the video handlers. Both call
`register_all()` before draining the queue.
"""

from __future__ import annotations

from dlp.domains.jobs.service import registry


def register_all() -> list[str]:
    """Import every module that registers a job handler; return the kinds the registry knows."""
    from dlp.domains.content_review import service as _content_review  # noqa: F401
    from dlp.domains.stories import service as _stories  # noqa: F401
    from dlp.domains.videos import service as _videos  # noqa: F401

    return registry.kinds()
