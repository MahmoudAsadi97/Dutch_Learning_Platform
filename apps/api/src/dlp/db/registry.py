"""Imports every ORM model so that `Base.metadata` is complete (used by Alembic)."""

from dlp.db.base import Base
from dlp.domains.coaching import models as coaching_models
from dlp.domains.content import models as content_models
from dlp.domains.content_review import models as content_review_models
from dlp.domains.curriculum import models as curriculum_models
from dlp.domains.feedback import models as feedback_models
from dlp.domains.identity import models as identity_models
from dlp.domains.jobs import models as jobs_models
from dlp.domains.practice import models as practice_models
from dlp.domains.progress import models as progress_models
from dlp.domains.speech import models as speech_models
from dlp.domains.topic_conversations import models as topic_conversation_models
from dlp.domains.usage import models as usage_models

__all__ = [
    "Base",
    "coaching_models",
    "content_models",
    "content_review_models",
    "curriculum_models",
    "feedback_models",
    "identity_models",
    "jobs_models",
    "practice_models",
    "progress_models",
    "speech_models",
    "topic_conversation_models",
    "usage_models",
]
