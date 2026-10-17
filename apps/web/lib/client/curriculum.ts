import type { LearningCopy } from "@/components/LanguageSupport";
import { errorFor } from "@/lib/client/errors";
import type { Skill } from "@/lib/types";
import { uiCopy } from "@/lib/ui-copy";

export interface CurriculumQuestion {
  id: string;
  prompt: LearningCopy;
  options: LearningCopy[];
  answer_index?: number;
  explanation?: LearningCopy;
  model_sentence?: string | null;
}
export interface ProductiveTask {
  prompt: LearningCopy;
  criteria: LearningCopy[];
  sample?: LearningCopy;
  sample_is_excerpt?: boolean;
  min_words: number;
  max_words: number;
}
export interface StageSummary {
  id: string;
  title: LearningCopy;
  description: LearningCopy;
  cefr_reference: string;
  unlocked: boolean;
  passed: boolean;
  practice_completed: Skill[];
  test_available: boolean;
}
export interface CurriculumCatalog {
  learner_key: string;
  stages: StageSummary[];
  admin_bypass: boolean;
  policy: Record<string, unknown>;
}
export interface CurriculumStage extends StageSummary {
  learner_key: string;
  progress?: StageSummary;
  admin_bypass?: boolean;
  policy?: { recording_max_seconds?: number };
  grammar: {
    id: string;
    title: LearningCopy;
    explanation: LearningCopy;
    examples: LearningCopy[];
    practice: CurriculumQuestion[];
  }[];
  vocabulary: { id: string; term: string; meaning: LearningCopy; example: LearningCopy }[];
  lesson: {
    story: LearningCopy;
    reading_questions: CurriculumQuestion[];
    listening: LearningCopy;
    listening_questions: CurriculumQuestion[];
    audio_parts: number;
    speaking: ProductiveTask;
    writing: ProductiveTask;
  };
}
export interface SkillResult {
  passed: boolean;
  feedback: LearningCopy;
  correct?: number;
  total?: number;
  criteria?: { criterion: LearningCopy; met: boolean; feedback: LearningCopy }[];
}
export interface CurriculumAttempt {
  id: string;
  stage_id: string;
  status: string;
  admin_preview?: boolean;
  policy?: { recording_max_seconds?: number };
  submission?: {
    reading_answers: Record<string, number>;
    listening_answers: Record<string, number>;
    writing_text: string;
    speaking_asset_id: string;
  } | null;
  test: {
    reading: { text: LearningCopy; questions: CurriculumQuestion[] };
    listening: { questions: CurriculumQuestion[]; audio_parts: number };
    speaking: ProductiveTask;
    writing: ProductiveTask;
  };
  results: Record<Skill, SkillResult> | null;
}

export { skillNames, skillOrder, stageLabel } from "../domain/registry";
/**
 * The message for a failed curriculum call. Pass the error itself: the API's code decides first, the
 * status second (lib/client/errors.ts). A bare status still works for the few callers that only have one.
 * The final check words its 403 and 422 precisely. Only a submission keeps the learner's input on
 * screen, so only `input` may say it stays; loading and plain actions make no such claim.
 */
export function friendlyError(cause?: unknown, context: "input" | "action" | "load" = "input"): string {
  const failed = typeof cause === "number" ? { status: cause } : cause;
  return errorFor(
    failed,
    uiCopy.errors,
    { 403: uiCopy.errors.checkLocked, 422: uiCopy.errors.checkIncomplete },
    { keepsInput: context === "input" },
  ).nl;
}
