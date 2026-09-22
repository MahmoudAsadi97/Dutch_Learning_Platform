/** Shapes returned by the API for the parts the web app renders in release 0.1. */

export type ReviewStatus = "unreviewed" | "reviewed" | "rejected";
export type Skill = "reading" | "listening" | "speaking" | "writing";

export interface LocalizedText {
  nl: string;
  fa: string;
  review_status: ReviewStatus;
  reviewer_note: string;
}

export interface HelpRung {
  level: 1 | 2 | 3;
  kind: "hint_nl" | "gloss_fa" | "translation_fa";
  text: string;
  direction: "ltr" | "rtl";
}

export interface VocabularyItem {
  nl: string;
  fa: string;
  note_nl: string;
}

export interface Question {
  id: string;
  prompt: LocalizedText;
  options: LocalizedText[];
  answer_index: number;
  help: HelpRung[];
}

export interface ReadingPayload {
  type: "reading";
  text: LocalizedText;
  vocabulary: VocabularyItem[];
  questions: Question[];
  help: HelpRung[];
}

export interface SpeakingPayload {
  type: "speaking";
  scenario_id: string;
  goal: LocalizedText;
  required_actions: string[];
  max_turns: number;
  modality: "push_to_talk";
  typed_fallback_allowed: boolean;
  help: HelpRung[];
}

export interface CheckpointPayload {
  type: "checkpoint";
  scenario_id: string;
  goal: LocalizedText;
  required_actions: string[];
  max_turns: number;
  independent: true;
  restrictions: { help_ladder: boolean; retry: boolean; typed_fallback: boolean; tools: string[] };
}

export interface ListeningPayload {
  type: "listening";
  audio_key: string;
  transcript: LocalizedText;
  questions: Question[];
  help: HelpRung[];
}

export interface WritingPayload {
  type: "writing";
  prompt: LocalizedText;
  min_words: number;
  max_words: number;
  must_include: string[];
  help: HelpRung[];
}

export type StepPayload = ReadingPayload | ListeningPayload | SpeakingPayload | CheckpointPayload | WritingPayload;

export interface Step {
  key: string;
  skill: Skill;
  title: LocalizedText;
  instructions: LocalizedText;
  variant: "base" | "transfer";
  payload: StepPayload;
}

export interface MissionResponse {
  id: string;
  version: number;
  cefr_target: string;
  title: LocalizedText;
  description: LocalizedText;
  review_status: string;
  content_hash: string;
  fixed_word_count: number;
  word_limit: number;
  review: { total_texts: number; unreviewed: number; reviewed: number; rejected: number };
  steps: { key: string; skill: Skill; type: string; variant: string; title: LocalizedText }[];
  document: { steps: Step[]; language_targets: { id: string; cefr: string; skill: Skill; can_do: LocalizedText }[] };
  labels: { unreviewed_nl: string; unreviewed_fa: string };
  request_id: string;
}

export interface AppointmentStateView {
  reason_stated?: boolean;
  offered_slot_ids?: string[];
  accepted_slot_id?: string;
  confirmed?: boolean;
  cancelled?: boolean;
  actions?: string[];
}

export interface StepProgress {
  completed?: boolean;
  turns?: number;
  modalities?: string[];
  answered?: Record<string, boolean>;
  attempts?: Record<string, number>;
  correct?: number;
  total?: number;
  help_levels?: number[];
  submissions?: number;
  word_count?: number;
  missing?: string[];
}

export interface PracticeSessionView {
  id: string;
  mission_id: string;
  variant: "base" | "transfer";
  status: "active" | "completed" | "ended" | "abandoned";
  current_step_key: string;
  request_id: string;
  appointment: AppointmentStateView;
  step_progress: Record<string, StepProgress>;
  started_at: string;
  updated_at: string;
  completed_at: string | null;
  turn_count: number;
  evidence_count: number;
}

export interface ConversationStepInfo {
  step_key: string;
  type: "speaking" | "checkpoint";
  opening_line: string;
  character: { name: string; role: LocalizedText; register: "formal" | "informal" };
  goal: LocalizedText;
  required_actions: string[];
  max_turns: number;
  typed_allowed: boolean;
  help_allowed: boolean;
  retry_allowed: boolean;
  slots: { id: string; day: string; start: string }[];
}

export interface TurnView {
  id: string;
  turn_index: number;
  step_key: string;
  request_id: string;
  modality: "speech" | "typed";
  learner_text: string;
  learner_audio_asset_id: string | null;
  character_text: string;
  character_audio_asset_id: string | null;
  proposed_action: { action: string; reason_text?: string; slot_id?: string; confidence?: number } | null;
  action_result: { accepted: boolean; action: string; reason: string; slot_id?: string } | null;
  phase: string | null;
  reply_source: "model" | "fixed_line" | null;
  understood_nl: string;
  model_calls: { step: string; prompt_version: string; provider: string; model: string; latency_ms: number }[];
  errors: string[];
  error: string | null;
  audio_error: string | null;
  status: "pending" | "completed" | "failed";
  created_at: string;
}

export interface EvidenceView {
  id: string;
  turn_id: string | null;
  step_key: string;
  skill: Skill;
  kind: string;
  modality: string;
  payload: Record<string, unknown>;
  source: string;
  created_at: string;
}

export interface DraftView {
  text: string;
  word_count: number;
  saved_at: string;
  submitted?: boolean;
}

export interface FeedbackPoint {
  kind: "strength" | "error" | "suggestion";
  skill: Skill;
  text_nl: string;
  text_fa: string;
  quote: string;
  correction: string;
  evidence_ids: string[];
}

export interface FeedbackReportView {
  id: string;
  session_id: string;
  step_key: string;
  skill: Skill;
  request_id: string;
  task_completed: boolean;
  summary_nl: string;
  summary_fa: string;
  points: FeedbackPoint[];
  evidence_ids: string[];
  dropped_points: number;
  dropped: { kind: string; text_nl: string; text_fa: string; quote: string; correction: string; evidence: string[]; reason: string }[];
  model_provider: string;
  model_name: string;
  prompt_version: string;
  created_at: string;
}

export interface SessionDetail {
  session: PracticeSessionView;
  conversation: ConversationStepInfo[];
  turns: TurnView[];
  evidence: EvidenceView[];
  drafts: Record<string, DraftView>;
  feedback: FeedbackReportView[];
  request_id: string;
}

export interface AnswerResponse {
  evidence: EvidenceView;
  correct: boolean;
  answer_index: number;
  step_completed: boolean;
  answered: Record<string, boolean>;
  session: PracticeSessionView;
  request_id: string;
}

export interface WritingResponse {
  evidence: EvidenceView;
  word_count: number;
  missing: string[];
  step_completed: boolean;
  session: PracticeSessionView;
  request_id: string;
}

export interface TurnResponse {
  turn: TurnView;
  deduplicated: boolean;
  step_completed: boolean;
  appointment: AppointmentStateView;
  reply_source: string;
  session: PracticeSessionView;
  request_id: string;
}

export interface SkillRecordView {
  updated_at: string;
  id: string;
  mission_id: string;
  skill: Skill;
  status: string;
  attempts: number;
  evidence_ids: string[];
}

export interface PreflightItem {
  component: string;
  mode: string;
  status: string;
  detail: string;
}
