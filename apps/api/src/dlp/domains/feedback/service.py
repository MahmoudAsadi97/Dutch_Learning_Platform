"""Feedback grounded in evidence. The model may only comment on evidence records it was shown; every
point must cite at least one of them by handle, and points whose citations do not resolve are dropped
and recorded, never shown. Nothing here counts as an assessment: it is feedback on one step."""

from __future__ import annotations

import re
from typing import Any, Literal

from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from dlp.config import Settings
from dlp.domains.content.schemas import (
    CheckpointPayload,
    ListeningPayload,
    MissionDocument,
    ReadingPayload,
    SpeakingPayload,
    Step,
    WritingPayload,
)
from dlp.domains.content.service import get_mission, mission_document
from dlp.domains.feedback.models import FeedbackReport
from dlp.domains.practice.models import EvidenceRecord, PracticeSession
from dlp.domains.practice.service import PracticeError
from dlp.domains.usage import service as usage
from dlp.providers.base import ChatMessage, ProviderError
from dlp.providers.registry import Providers

FEEDBACK_VERSION = "feedback-v1"
TOKENS_ESTIMATE = 2500


class FeedbackModelPoint(BaseModel):
    kind: Literal["strength", "error", "suggestion"]
    text_nl: str = Field(min_length=1)
    text_fa: str = ""
    quote: str = ""
    correction: str = ""
    evidence: list[str] = Field(default_factory=list, description="handles such as E1, E2 of the evidence this point is about")


class FeedbackModelReply(BaseModel):
    summary_nl: str = Field(min_length=1)
    summary_fa: str = ""
    task_completed: bool = False
    points: list[FeedbackModelPoint] = Field(default_factory=list)


def _document(session: Session, practice: PracticeSession) -> MissionDocument:
    mission = get_mission(session, practice.mission_id)
    assert mission is not None
    return mission_document(mission)


def evidence_for_step(practice: PracticeSession, step_key: str) -> list[EvidenceRecord]:
    return sorted((e for e in practice.evidence if e.step_key == step_key), key=lambda e: e.created_at)


def check_expectations(document: MissionDocument, step: Step, records: list[EvidenceRecord]) -> str | None:
    """The mission says what must exist before a skill may be looked at; return the shortfall, if any."""
    expectation = next((x for x in document.evidence_expectations if x.skill == step.skill), None)
    if expectation is None:
        return None
    relevant = [r for r in records if r.kind in expectation.kinds]
    if len(relevant) < expectation.minimum_items:
        return (f"{step.skill} needs at least {expectation.minimum_items} evidence item(s) of kind "
                f"{', '.join(expectation.kinds)}; the step has {len(relevant)}")
    if expectation.requires_code_validated_action:
        accepted = [r for r in records if r.kind == "action_result" and (r.payload.get("result") or {}).get("accepted")]
        if not accepted:
            return f"{step.skill} needs at least one code-validated action; none was accepted yet"
    return None


def describe_evidence(record: EvidenceRecord) -> str:
    p = record.payload or {}
    if record.kind == "answer":
        verdict = "juist" if p.get("correct") else "fout"
        return f"antwoord op \"{p.get('prompt_nl', '')}\": \"{p.get('chosen_nl', '')}\" ({verdict}, poging {p.get('attempt', 1)})"
    if record.kind == "transcript":
        return f"gesproken (transcriptie): \"{p.get('text', '')}\""
    if record.kind == "typed_text":
        extra = f" ({p['word_count']} woorden" + (f", ontbreekt: {', '.join(p['missing'])}" if p.get("missing") else "") + ")" \
            if "word_count" in p else ""
        return f"getypt: \"{p.get('text', '')}\"{extra}"
    if record.kind == "action_result":
        result = p.get("result") or {}
        verdict = "aanvaard" if result.get("accepted") else "niet aanvaard"
        return f"actie {result.get('action', '?')}: {verdict} ({result.get('reason', '')})"
    if record.kind == "help_used":
        return f"hulp gebruikt: niveau {p.get('level')} ({p.get('kind')})"
    return f"{record.kind}: {str(p)[:200]}"


def _task_description(step: Step) -> str:
    payload = step.payload
    if isinstance(payload, ReadingPayload):
        return f"Leesopdracht: {step.instructions.nl} Tekst: \"{payload.text.nl}\""
    if isinstance(payload, ListeningPayload):
        return f"Luisteropdracht: {step.instructions.nl} Gesproken tekst: \"{payload.transcript.nl}\""
    if isinstance(payload, SpeakingPayload | CheckpointPayload):
        return f"Spreekopdracht (telefoongesprek): {payload.goal.nl} Vereiste stappen: {', '.join(payload.required_actions)}."
    if isinstance(payload, WritingPayload):
        return (f"Schrijfopdracht: {payload.prompt.nl} ({payload.min_words}-{payload.max_words} woorden; "
                f"moet bevatten: {', '.join(payload.must_include) or 'geen'})")
    return step.instructions.nl


def feedback_messages(step: Step, handles: list[tuple[str, EvidenceRecord]], task_completed: bool) -> list[ChatMessage]:
    lines = "\n".join(f"- {handle}: {describe_evidence(record)[:240]}" for handle, record in handles)
    system = (
        "Je bent een vriendelijke taalcoach Nederlands (Belgisch Standaardnederlands) voor een volwassen leerder op niveau A2 "
        "met Perzisch als moedertaal. Je geeft korte, concrete feedback op één oefening. Je mag ALLEEN spreken over de "
        "bewijsstukken hieronder en je verwijst bij elk punt naar de codes (E1, E2, ...) van de bewijsstukken waarover het gaat. "
        "Verzin niets wat niet in de bewijsstukken staat. Geen cijfer, geen niveau-oordeel.\n\n"
        f"{_task_description(step)}\n"
        f"Opdracht volbracht volgens de toepassing: {'ja' if task_completed else 'nee'}.\n\n"
        f"Bewijsstukken:\n{lines}\n\n"
        "Antwoord kort, als JSON met: summary_nl (twee korte zinnen), summary_fa (dezelfde samenvatting in het Perzisch), "
        "task_completed (true/false), points (maximaal drie), elk met kind (strength, error of suggestion), "
        "text_nl (één korte zin van hoogstens 15 woorden), text_fa (dezelfde zin in het Perzisch), quote (de woorden van de "
        "leerder waar het over gaat, letterlijk, of leeg), correction (de verbeterde vorm, of leeg) en evidence "
        "(lijst met codes zoals [\"E1\"]). Geen andere velden, geen tekst buiten de JSON."
    )
    return [ChatMessage("system", system), ChatMessage("user", "Geef nu de feedback als JSON.")]


def generate_feedback(session: Session, settings: Settings, providers: Providers, *, practice: PracticeSession,
                      step_key: str, request_id: str) -> FeedbackReport:
    existing = session.scalar(
        select(FeedbackReport).where(FeedbackReport.session_id == practice.id, FeedbackReport.request_id == request_id)
    )
    if existing is not None:
        return existing
    document = _document(session, practice)
    step = next((s for s in document.steps if s.key == step_key), None)
    if step is None:
        raise PracticeError("step not found", status_code=404)
    if step.variant != practice.variant:
        raise PracticeError(f"step {step_key} belongs to the {step.variant} variant", status_code=409)
    session.expire(practice, ["evidence"])
    records = evidence_for_step(practice, step_key)
    shortfall = check_expectations(document, step, records)
    if shortfall:
        raise PracticeError(f"not enough evidence for feedback yet: {shortfall}", status_code=409)
    progress = (practice.state.get("step_progress") or {}).get(step_key, {})
    task_completed = bool(progress.get("completed"))
    handles = [(f"E{i + 1}", record) for i, record in enumerate(records[-24:])]
    by_handle = {handle: record for handle, record in handles}

    calls_reservation = usage.reserve(session, settings, practice.learner_id, "model_calls", 1, f"{request_id}-fb")
    tokens_reservation = usage.reserve(session, settings, practice.learner_id, "tokens", TOKENS_ESTIMATE, f"{request_id}-fb")
    try:
        result = providers.chat.complete(
            feedback_messages(step, handles, task_completed), schema=FeedbackModelReply,
            max_output_tokens=settings.feedback_max_output_tokens, temperature=0.2,
            prompt_version=FEEDBACK_VERSION, request_id=request_id,
        )
    except ProviderError:
        usage.release(session, calls_reservation.id)
        usage.release(session, tokens_reservation.id)
        raise
    usage.commit(session, calls_reservation.id, 1.0)
    usage.commit(session, tokens_reservation.id, float(result.total_tokens))
    if isinstance(result.parsed, FeedbackModelReply):
        reply = result.parsed
    else:
        reply = FeedbackModelReply(summary_nl=result.text[:400] or "-")

    points: list[dict[str, Any]] = []
    dropped: list[dict[str, Any]] = []
    for point in reply.points:
        handles_cited = resolve_handles(point.evidence, by_handle)
        quote = point.quote.strip()
        if not handles_cited and quote:
            # No usable citation, but the quote may identify the evidence on its own.
            handles_cited = [h for h, record in handles if quote.lower() in describe_evidence(record).lower()]
        if not handles_cited:
            dropped.append({**point.model_dump(), "reason": "no valid evidence citation"})
            continue
        if quote and not any(quote.lower() in describe_evidence(by_handle[h]).lower() for h in handles_cited):
            dropped.append({**point.model_dump(), "reason": "quote not found in the cited evidence"})
            continue
        points.append({"kind": point.kind, "skill": step.skill, "text_nl": point.text_nl, "text_fa": point.text_fa,
                       "quote": quote, "correction": point.correction,
                       "evidence_ids": [str(by_handle[h].id) for h in handles_cited]})

    report = FeedbackReport(
        session_id=practice.id, learner_id=practice.learner_id, step_key=step_key, skill=step.skill, request_id=request_id,
        task_completed=task_completed,
        report={"summary_nl": reply.summary_nl, "summary_fa": reply.summary_fa, "points": points,
                "model_task_completed": reply.task_completed},
        evidence_ids=[str(r.id) for _, r in handles], dropped_points=dropped,
        model_provider=result.provider, model_name=result.model, prompt_version=result.prompt_version,
    )
    session.add(report)
    session.flush()
    _note_on_skill_record(session, practice, step, report)
    return report


def resolve_handles(cited: list[str], by_handle: dict[str, EvidenceRecord]) -> list[str]:
    """Accept the handle in the shapes a small model produces: "E1", "e1", "E1: ...", "[E1]", "1", "bewijs 1"."""
    found: list[str] = []
    for item in cited:
        text = str(item)
        for match in re.findall(r"[Ee]\s*(\d+)", text) or re.findall(r"\b(\d+)\b", text):
            handle = f"E{int(match)}"
            if handle in by_handle and handle not in found:
                found.append(handle)
    return found


def _note_on_skill_record(session: Session, practice: PracticeSession, step: Step, report: FeedbackReport) -> None:
    from dlp.domains.progress.models import SkillRecord

    record = session.scalar(
        select(SkillRecord).where(SkillRecord.learner_id == practice.learner_id,
                                  SkillRecord.mission_id == practice.mission_id, SkillRecord.skill == step.skill)
    )
    if record is None:
        return
    assessment = dict(record.latest_assessment or {})
    entry = dict(assessment.get(step.key, {}))
    entry["feedback_report_id"] = str(report.id)
    entry["feedback_points"] = len(report.report.get("points", []))
    assessment[step.key] = entry
    record.latest_assessment = assessment


def reports_for(session: Session, practice: PracticeSession) -> list[FeedbackReport]:
    return list(session.scalars(
        select(FeedbackReport).where(FeedbackReport.session_id == practice.id).order_by(FeedbackReport.created_at)
    ))


def report_view(report: FeedbackReport) -> dict[str, Any]:
    return {
        "id": str(report.id), "session_id": str(report.session_id), "step_key": report.step_key, "skill": report.skill,
        "request_id": report.request_id, "task_completed": report.task_completed,
        "summary_nl": report.report.get("summary_nl", ""), "summary_fa": report.report.get("summary_fa", ""),
        "points": report.report.get("points", []), "evidence_ids": report.evidence_ids,
        "dropped_points": len(report.dropped_points), "dropped": report.dropped_points,
        "model_provider": report.model_provider,
        "model_name": report.model_name, "prompt_version": report.prompt_version,
        "created_at": report.created_at.isoformat(),
    }

