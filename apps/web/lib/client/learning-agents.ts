import type { LearningCopy } from "@/components/LanguageSupport";
import type { Skill } from "@/lib/types";

export interface ConversationChoice {
  id: string; stage_id: string; topic_id: string; title: LearningCopy; role: LearningCopy;
  active_session_id?: string | null;
}
export interface ConversationCatalog { items: ConversationChoice[]; learner_key: string }
export interface ConversationTurn {
  id: string; number: number; action: "respond" | "repeat" | "hint";
  learner_text: string; reply: LearningCopy; accepted: boolean; assisted: boolean; mode: "typed" | "spoken";
}
export interface ConversationSession {
  id: string; blueprint_id: string; stage_id: string; topic_id: string; title: LearningCopy;
  role: LearningCopy; setup: LearningCopy; opening: LearningCopy; mode: "typed" | "spoken";
  status: "active" | "completed" | "ended"; turn_count: number; max_turns: number;
  current_goal: LearningCopy | null; history: ConversationTurn[];
  goals: {goal: LearningCopy; met: boolean; assisted: boolean}[];
  summary: LearningCopy | null; review_status: string; recording_max_seconds: number; learner_key: string;
}
export interface ConversationTurnRequest {
  client_turn_id: string; expected_turn: number; action: "respond" | "repeat" | "hint";
  text?: string; audio_asset_id?: string;
}
export interface PracticePlan {
  stage_id: string; history_version: string; mode: "suggested" | "personalised" | "fallback";
  notice: LearningCopy; history_count: number; can_personalise: boolean;
  items: {id: string; stage_id: string; topic_id: string; skill: Skill; title: LearningCopy;
    category: LearningCopy; reason: LearningCopy; basis: string; evidence_count: number}[];
}
export const practiceStages = ["pre-a1", "a1", "pre-a2", "a2", "pre-b1", "b1", "pre-b2", "b2", "pre-c1", "c1", "pre-c2", "c2"];

/** Only generated stage/topic identifiers can become learner navigation targets. */
export function topicHref(stageId: string, skill: string, topicId: string): string | null {
  if (!practiceStages.includes(stageId) || !["reading", "listening", "speaking", "writing"].includes(skill) || !new RegExp(`^${stageId}-t\\d{3}$`).test(topicId)) return null;
  return `/learn/${stageId}?${new URLSearchParams({skill, topic: topicId})}`;
}
