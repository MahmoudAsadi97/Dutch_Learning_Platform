import type { LearningCopy } from "@/components/LanguageSupport";
import type { Skill } from "@/lib/types";

export interface ReferenceSource {
  id: string;
  title: string;
  url: string;
}
export interface ExamProfile {
  id: string;
  title: string;
  family: string;
  levels: string[];
  source_ids: string[];
}
export interface LevelContract {
  id: string;
  reference_status: string;
  purpose: LearningCopy;
  skills: Record<Skill, { target: LearningCopy }>;
  source_details: ReferenceSource[];
  exam_profiles: ExamProfile[];
}
export interface ExamReferences {
  profiles: ExamProfile[];
  sources: ReferenceSource[];
}
