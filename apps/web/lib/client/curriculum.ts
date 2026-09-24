import type { LearningCopy } from "@/components/LanguageSupport";
import type { Skill } from "@/lib/types";

export interface CurriculumQuestion { id: string; prompt: LearningCopy; options: LearningCopy[]; answer_index?: number; explanation?: LearningCopy }
export interface ProductiveTask { prompt: LearningCopy; criteria: LearningCopy[]; sample?: LearningCopy; sample_is_excerpt?: boolean; min_words: number; max_words: number }
export interface StageSummary {
  id: string; title: LearningCopy; description: LearningCopy; cefr_reference: string;
  unlocked: boolean; passed: boolean; practice_completed: Skill[]; test_available: boolean;
}
export interface CurriculumCatalog { learner_key: string; stages: StageSummary[]; admin_bypass: boolean; policy: Record<string, unknown> }
export interface CurriculumStage extends StageSummary {
  learner_key: string;
  progress?: StageSummary; admin_bypass?: boolean; policy?: {recording_max_seconds?: number};
  grammar: { id: string; title: LearningCopy; explanation: LearningCopy; examples: LearningCopy[]; practice: CurriculumQuestion[] }[];
  vocabulary: { id: string; term: string; meaning: LearningCopy; example: LearningCopy }[];
  lesson: {
    story: LearningCopy; reading_questions: CurriculumQuestion[]; listening: LearningCopy;
    listening_questions: CurriculumQuestion[]; audio_parts: number; speaking: ProductiveTask; writing: ProductiveTask;
  };
}
export interface SkillResult { passed: boolean; feedback: LearningCopy; correct?: number; total?: number; criteria?: { criterion: LearningCopy; met: boolean; feedback: LearningCopy }[] }
export interface CurriculumAttempt {
  id: string; stage_id: string; status: string; admin_preview?: boolean; policy?: {recording_max_seconds?: number};
  submission?: {reading_answers: Record<string, number>; listening_answers: Record<string, number>; writing_text: string; speaking_asset_id: string} | null;
  test: {
    reading: { text: LearningCopy; questions: CurriculumQuestion[] };
    listening: { questions: CurriculumQuestion[]; audio_parts: number };
    speaking: ProductiveTask; writing: ProductiveTask;
  };
  results: Record<Skill, SkillResult> | null;
}

export const skillNames: Record<Skill, string> = { reading: "Lezen", listening: "Luisteren", speaking: "Spreken", writing: "Schrijven" };
export const skillOrder: Skill[] = ["reading", "listening", "speaking", "writing"];
export function stageLabel(id: string) { return id.replace(/^pre-/, "pre-").replace(/([abc])([12])$/, (_, letter: string, number: string) => `${letter.toUpperCase()}${number}`); }
export function friendlyError(status?: number): string {
  if (status === 401) return "Je sessie is verlopen. Meld je opnieuw aan en probeer verder te gaan.";
  if (status === 403) return "Rond eerst het vorige niveau af. Je voortgang wordt op de server gecontroleerd.";
  if (status === 429) return "Je oefenlimiet is bereikt. Je werk blijft bewaard; probeer later opnieuw.";
  if (status === 422) return "Controleer of je alle onderdelen hebt ingevuld en een nieuwe opname hebt gemaakt.";
  return "Dit lukte even niet. Je invoer blijft staan. Probeer het opnieuw.";
}
