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

export interface OtherPayload {
  type: "listening" | "speaking" | "writing" | "checkpoint";
  help?: HelpRung[];
  [key: string]: unknown;
}

export interface Step {
  key: string;
  skill: Skill;
  title: LocalizedText;
  instructions: LocalizedText;
  variant: "base" | "transfer";
  payload: ReadingPayload | OtherPayload;
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

export interface PracticeSessionView {
  id: string;
  mission_id: string;
  variant: string;
  status: string;
  current_step_key: string;
  request_id: string;
  started_at: string;
}

export interface SkillRecordView {
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
