"""Mission document schemas: contract, scenarios, evidence expectations.

A mission file under `content/missions/<id>/mission.json` must validate against
`MissionDocument` before it is stored. Every fixed Dutch text is a `LocalizedText`
that carries its own review status, so the UI can label unreviewed content and the
reviewer can approve items one by one later.
"""

from __future__ import annotations

import re
from datetime import date, datetime, time
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

# Dotted paths (see `MissionDocument.iter_localized`) that belong to the fixed Dutch pack.
PACK_PATH = re.compile(
    r"^(steps\[\d+\]\.payload\.(text|transcript|goal|prompt|questions\[\d+\]\.(prompt|options\[\d+\]))"
    r"|scenarios\[\d+\]\.(fixed_lines\[\d+\]\.text|reason_options\[\d+\]|available_slots\[\d+\]\.note))$"
)

Skill = Literal["reading", "listening", "speaking", "writing"]
StepType = Literal["reading", "listening", "speaking", "writing", "checkpoint"]
VariantId = Literal["base", "transfer"]
ReviewStatus = Literal["unreviewed", "reviewed", "rejected"]
Modality = Literal["speech", "typed", "none"]
Register = Literal["formal", "informal"]

SKILLS: tuple[Skill, ...] = ("reading", "listening", "speaking", "writing")
UNREVIEWED_LABEL_NL = "Niet-nagekeken inhoud"
UNREVIEWED_LABEL_FA = "محتوای بازبینی‌نشده"


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class LocalizedText(StrictModel):
    """A fixed text in Dutch with an optional Persian rendering and its review state."""

    nl: str = Field(min_length=1)
    fa: str = ""
    review_status: ReviewStatus = "unreviewed"
    reviewer_note: str = ""

    @property
    def label(self) -> str | None:
        return UNREVIEWED_LABEL_NL if self.review_status != "reviewed" else None


class LanguageTarget(StrictModel):
    """A provisional can-do statement the mission aims at."""

    id: str = Field(pattern=r"^[a-z0-9_-]+$")
    cefr: str = Field(pattern=r"^(A1|A2|B1|B2|C1|C2)$")
    skill: Skill
    can_do: LocalizedText


class VocabularyItem(StrictModel):
    nl: str
    fa: str
    note_nl: str = ""


class HelpRung(StrictModel):
    """One rung of the Persian text-help ladder, from lightest to heaviest help."""

    level: int = Field(ge=1, le=3)
    kind: Literal["hint_nl", "gloss_fa", "translation_fa"]
    text: str = Field(min_length=1)
    direction: Literal["ltr", "rtl"]

    @model_validator(mode="after")
    def _direction_matches_language(self) -> HelpRung:
        expected = "ltr" if self.kind == "hint_nl" else "rtl"
        if self.direction != expected:
            raise ValueError(f"help rung {self.level} ({self.kind}) must be {expected}")
        return self


class Question(StrictModel):
    id: str = Field(pattern=r"^[a-z0-9_-]+$")
    prompt: LocalizedText
    options: list[LocalizedText] = Field(min_length=2, max_length=5)
    answer_index: int = Field(ge=0)
    help: list[HelpRung] = Field(default_factory=list)

    @model_validator(mode="after")
    def _answer_in_range(self) -> Question:
        if self.answer_index >= len(self.options):
            raise ValueError(f"question {self.id}: answer_index out of range")
        return self


class ReadingPayload(StrictModel):
    type: Literal["reading"] = "reading"
    text: LocalizedText
    vocabulary: list[VocabularyItem] = Field(default_factory=list)
    questions: list[Question] = Field(min_length=1)
    help: list[HelpRung] = Field(min_length=1)


class ListeningPayload(StrictModel):
    type: Literal["listening"] = "listening"
    audio_key: str = Field(pattern=r"^[a-z0-9_./-]+$")
    transcript: LocalizedText
    questions: list[Question] = Field(min_length=1)
    help: list[HelpRung] = Field(min_length=1)


class SpeakingPayload(StrictModel):
    type: Literal["speaking"] = "speaking"
    scenario_id: str
    goal: LocalizedText
    required_actions: list[str] = Field(min_length=1)
    max_turns: int = Field(ge=2, le=30)
    modality: Literal["push_to_talk"] = "push_to_talk"
    typed_fallback_allowed: bool = True
    help: list[HelpRung] = Field(min_length=1)


class WritingPayload(StrictModel):
    type: Literal["writing"] = "writing"
    prompt: LocalizedText
    min_words: int = Field(ge=5)
    max_words: int = Field(le=400)
    must_include: list[str] = Field(default_factory=list)
    help: list[HelpRung] = Field(min_length=1)

    @model_validator(mode="after")
    def _bounds(self) -> WritingPayload:
        if self.max_words <= self.min_words:
            raise ValueError("max_words must exceed min_words")
        return self


class CheckpointRestrictions(StrictModel):
    help_ladder: bool = False
    retry: bool = False
    typed_fallback: bool = False
    tools: list[str] = Field(default_factory=list)


class CheckpointPayload(StrictModel):
    type: Literal["checkpoint"] = "checkpoint"
    scenario_id: str
    goal: LocalizedText
    required_actions: list[str] = Field(min_length=1)
    max_turns: int = Field(ge=2, le=30)
    independent: Literal[True] = True
    restrictions: CheckpointRestrictions = Field(default_factory=CheckpointRestrictions)


StepPayload = Annotated[
    ReadingPayload | ListeningPayload | SpeakingPayload | WritingPayload | CheckpointPayload,
    Field(discriminator="type"),
]


class Step(StrictModel):
    key: str = Field(pattern=r"^[a-z0-9_-]+$")
    skill: Skill
    title: LocalizedText
    instructions: LocalizedText
    variant: VariantId = "base"
    payload: StepPayload

    @model_validator(mode="after")
    def _skill_matches_payload(self) -> Step:
        expected: dict[str, Skill] = {
            "reading": "reading",
            "listening": "listening",
            "speaking": "speaking",
            "writing": "writing",
            "checkpoint": "speaking",
        }
        if expected[self.payload.type] != self.skill:
            raise ValueError(f"step {self.key}: skill {self.skill} does not match payload {self.payload.type}")
        return self


class Character(StrictModel):
    name: str
    role: LocalizedText
    register_style: Register
    voice_hint: str = ""


class Slot(StrictModel):
    id: str = Field(pattern=r"^[a-z0-9_-]+$")
    day: date
    start: time
    end: time
    note: LocalizedText | None = None

    @model_validator(mode="after")
    def _ordered(self) -> Slot:
        if self.end <= self.start:
            raise ValueError(f"slot {self.id}: end must be after start")
        return self


class Appointment(StrictModel):
    what: LocalizedText
    with_whom: LocalizedText
    location: LocalizedText
    day: date
    start: time


class FixedLine(StrictModel):
    key: str = Field(pattern=r"^[a-z0-9_-]+$")
    when: Literal["opening", "ask_reason", "offer_slots", "confirm", "closing", "repeat", "clarify"]
    text: LocalizedText


class Scenario(StrictModel):
    """The situation the character and the learner are in. Slots and rules are authoritative."""

    id: str = Field(pattern=r"^[a-z0-9_-]+$")
    variant: VariantId
    reference_date: date
    setting: LocalizedText
    learner_role: LocalizedText
    character: Character
    appointment: Appointment
    reason_options: list[LocalizedText] = Field(min_length=1)
    available_slots: list[Slot] = Field(min_length=2)
    allowed_actions: list[str] = Field(min_length=1)
    fixed_lines: list[FixedLine] = Field(min_length=3)
    success_criteria: list[LocalizedText] = Field(min_length=1)

    @model_validator(mode="after")
    def _slots_after_reference(self) -> Scenario:
        seen: set[str] = set()
        for slot in self.available_slots:
            if slot.id in seen:
                raise ValueError(f"duplicate slot id {slot.id}")
            seen.add(slot.id)
            if slot.day < self.reference_date:
                raise ValueError(f"slot {slot.id} lies before the scenario reference date")
        if self.appointment.day < self.reference_date:
            raise ValueError("the current appointment lies before the scenario reference date")
        return self


class EvidenceExpectation(StrictModel):
    """What must exist in the database before a skill record for this mission may be assessed."""

    skill: Skill
    kinds: list[str] = Field(min_length=1)
    minimum_items: int = Field(ge=1)
    requires_code_validated_action: bool = False
    note: str = ""


class HelpPolicy(StrictModel):
    language: Literal["fa"] = "fa"
    direction: Literal["rtl"] = "rtl"
    max_level: int = Field(ge=1, le=3, default=3)
    unavailable_in_checkpoint: bool = True


class ContentPack(StrictModel):
    word_limit: int = Field(default=300, ge=50, le=300)
    description: str = ""


class Completion(StrictModel):
    required_step_keys: list[str] = Field(min_length=1)
    checkpoint_step_key: str


class MissionDocument(StrictModel):
    schema_version: Literal[1] = 1
    id: str = Field(pattern=r"^[a-z0-9-]+$")
    version: int = Field(ge=1)
    cefr_target: str = Field(pattern=r"^(A1|A2|B1|B2|C1|C2)$")
    title: LocalizedText
    description: LocalizedText
    language_targets: list[LanguageTarget] = Field(min_length=1)
    steps: list[Step] = Field(min_length=4)
    scenarios: list[Scenario] = Field(min_length=2)
    evidence_expectations: list[EvidenceExpectation] = Field(min_length=4)
    help_policy: HelpPolicy = Field(default_factory=HelpPolicy)
    content_pack: ContentPack = Field(default_factory=ContentPack)
    completion: Completion

    @model_validator(mode="after")
    def _cross_references(self) -> MissionDocument:
        step_keys = [step.key for step in self.steps]
        if len(step_keys) != len(set(step_keys)):
            raise ValueError("step keys must be unique")
        scenario_ids = {scenario.id for scenario in self.scenarios}
        variants = {scenario.variant for scenario in self.scenarios}
        if variants != {"base", "transfer"}:
            raise ValueError("a mission needs exactly one base and one transfer scenario")
        for step in self.steps:
            payload = step.payload
            if isinstance(payload, SpeakingPayload | CheckpointPayload) and payload.scenario_id not in scenario_ids:
                raise ValueError(f"step {step.key} references unknown scenario {payload.scenario_id}")
        for key in self.completion.required_step_keys:
            if key not in step_keys:
                raise ValueError(f"completion references unknown step {key}")
        if self.completion.checkpoint_step_key not in step_keys:
            raise ValueError("completion.checkpoint_step_key is not a step")
        checkpoint = next(step for step in self.steps if step.key == self.completion.checkpoint_step_key)
        if checkpoint.payload.type != "checkpoint":
            raise ValueError("completion.checkpoint_step_key must point at a checkpoint step")
        covered = {step.skill for step in self.steps}
        if covered != set(SKILLS):
            raise ValueError(f"steps must cover all four skills, got {sorted(covered)}")
        expected_skills = {item.skill for item in self.evidence_expectations}
        if expected_skills != set(SKILLS):
            raise ValueError("evidence_expectations must cover all four skills")
        for scenario in self.scenarios:
            for step in self.steps:
                if isinstance(step.payload, SpeakingPayload | CheckpointPayload) and step.payload.scenario_id == scenario.id:
                    for action in step.payload.required_actions:
                        if action not in scenario.allowed_actions:
                            raise ValueError(f"step {step.key} requires action {action} not allowed by {scenario.id}")
        return self

    def scenario(self, scenario_id: str) -> Scenario:
        return next(scenario for scenario in self.scenarios if scenario.id == scenario_id)

    def iter_localized(self) -> list[tuple[str, LocalizedText]]:
        """Every fixed text with a dotted path, used for labelling and word counts."""
        found: list[tuple[str, LocalizedText]] = []

        def walk(value: object, path: str) -> None:
            if isinstance(value, LocalizedText):
                found.append((path, value))
            elif isinstance(value, BaseModel):
                for name in type(value).model_fields:
                    walk(getattr(value, name), f"{path}.{name}" if path else name)
            elif isinstance(value, list):
                for index, item in enumerate(value):
                    walk(item, f"{path}[{index}]")

        walk(self, "")
        return found

    def pack_texts(self) -> list[tuple[str, LocalizedText]]:
        """The fixed Dutch pack: texts the learner reads or hears as lesson content."""
        return [(path, text) for path, text in self.iter_localized() if PACK_PATH.match(path)]

    def interface_texts(self) -> list[tuple[str, LocalizedText]]:
        """Titles, instructions, roles, settings: shown bilingually as interface guidance."""
        return [(path, text) for path, text in self.iter_localized() if not PACK_PATH.match(path)]

    def fixed_dutch_word_count(self) -> int:
        """Dutch words in the fixed pack (the `content_pack.word_limit` applies to this number)."""
        return sum(len(text.nl.split()) for _, text in self.pack_texts())

    def interface_word_count(self) -> int:
        return sum(len(text.nl.split()) for _, text in self.interface_texts())


class ReviewSummary(BaseModel):
    total_texts: int
    unreviewed: int
    reviewed: int
    rejected: int
    label_nl: str = UNREVIEWED_LABEL_NL
    label_fa: str = UNREVIEWED_LABEL_FA


def review_summary(document: MissionDocument) -> ReviewSummary:
    texts = [text for _, text in document.iter_localized()]
    return ReviewSummary(
        total_texts=len(texts),
        unreviewed=sum(1 for text in texts if text.review_status == "unreviewed"),
        reviewed=sum(1 for text in texts if text.review_status == "reviewed"),
        rejected=sum(1 for text in texts if text.review_status == "rejected"),
    )


class EvidenceEnvelope(BaseModel):
    """Runtime shape of an evidence record as exposed by the API and the export."""

    id: str
    session_id: str
    turn_id: str | None
    step_key: str
    skill: Skill
    kind: str
    modality: Modality
    payload: dict
    source: str
    created_at: datetime
