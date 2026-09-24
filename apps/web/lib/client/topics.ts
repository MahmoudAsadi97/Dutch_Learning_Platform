import type { LearningCopy } from "@/components/LanguageSupport";
import type { CurriculumQuestion, ProductiveTask, SkillResult } from "@/lib/client/curriculum";
import type { Skill } from "@/lib/types";

export interface TopicSummary {
  id: string; title: LearningCopy; category: LearningCopy; completed: boolean; attempted: boolean;
}
export interface TopicPage {
  stage_id: string; skill: Skill; total: number; total_topics: number; offset: number; limit: number;
  completed_count: number; categories: LearningCopy[]; items: TopicSummary[]; learner_key: string;
}
export interface TopicDetail {
  stage_id: string; skill: Skill; id: string; title: LearningCopy; category: LearningCopy;
  objectives: LearningCopy[]; language_focus: LearningCopy; review_status: string;
  context?: {reading: LearningCopy; listening: LearningCopy};
  vocabulary: {id: string; term: string; meaning: LearningCopy; example: LearningCopy}[];
  activity: (ProductiveTask & {text?: never; questions?: never; audio_parts?: never}) | {
    text: LearningCopy; questions: CurriculumQuestion[]; audio_parts?: number;
    prompt?: never; criteria?: never; sample?: never; sample_is_excerpt?: never; min_words?: never; max_words?: never;
  };
  progress: {completed: boolean; attempted: boolean}; policy: {recording_max_seconds: number};
}
export interface TopicFeedback {
  completed: boolean; passed?: boolean; correct?: number; total?: number; feedback: LearningCopy;
  criteria?: SkillResult["criteria"];
  explanations?: {id: string; correct: boolean; answer_index: number; explanation: LearningCopy}[];
}
