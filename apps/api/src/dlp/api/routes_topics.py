"""Authenticated four-skill topic practice, using the same providers and allowance as core lessons."""
from typing import Literal

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from dlp.api.deps import RequestContext, context_dep, providers_dep, settings_dep
from dlp.api.routes_curriculum import PracticeBody, _audio, _run
from dlp.config import Settings
from dlp.db.session import get_session
from dlp.domains.curriculum import topics
from dlp.domains.curriculum.schemas import Skill
from dlp.providers.registry import Providers

router = APIRouter(prefix="/curriculum/{stage_id}/topics", tags=["curriculum"])


@router.get("")
def topic_list(stage_id: str, skill: Skill, q: str = Query(default="", max_length=120),
               category: str = Query(default="", max_length=160),
               status: Literal["all", "not_started", "completed"] = "all",
               offset: int = Query(default=0, ge=0, le=100000), limit: int = Query(default=12, ge=1, le=24),
               ctx: RequestContext = Depends(context_dep), session: Session = Depends(get_session)):
    return _run(lambda: topics.topic_page(session, ctx.learner.id, topics.topics_for(stage_id), skill=skill,
                                          query=q, category=category, status=status, offset=offset, limit=limit))


@router.get("/{topic_id}")
def topic_get(stage_id: str, topic_id: str, skill: Skill, ctx: RequestContext = Depends(context_dep),
              settings: Settings = Depends(settings_dep), session: Session = Depends(get_session)):
    def operation():
        bank = topics.topics_for(stage_id)
        topic = topics.topic_for(bank, topic_id)
        return topics.topic_detail(session, ctx.learner.id, bank, topic, skill=skill,
                                   recording_max_seconds=settings.max_audio_seconds)
    return _run(operation)


@router.post("/{topic_id}/practice")
def topic_practice(stage_id: str, topic_id: str, body: PracticeBody,
                   ctx: RequestContext = Depends(context_dep), settings: Settings = Depends(settings_dep),
                   providers: Providers = Depends(providers_dep), session: Session = Depends(get_session)):
    def operation():
        bank = topics.topics_for(stage_id)
        topic = topics.topic_for(bank, topic_id)
        return topics.save_topic_practice(
            session, settings, providers, learner_id=ctx.learner.id, bank=bank, topic=topic,
            skill=body.skill, answers=body.answers, text=body.text, asset_id=body.audio_asset_id, request_id=ctx.request_id,
            observation_request_id=body.request_id,
        )
    return _run(operation, provider_detail=(
        "Practice feedback is temporarily unavailable. Your response was not completed; retry."
    ))


@router.post("/{topic_id}/listening")
def topic_listening(stage_id: str, topic_id: str, part: int = Query(default=0, ge=0, le=100),
                    ctx: RequestContext = Depends(context_dep), settings: Settings = Depends(settings_dep),
                    providers: Providers = Depends(providers_dep), session: Session = Depends(get_session)):
    def operation():
        topic = topics.topic_for(topics.topics_for(stage_id), topic_id)
        return _audio(topic.listening.text.nl, part, ctx, settings, providers, session)
    return _run(operation)
