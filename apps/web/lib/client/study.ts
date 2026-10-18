import type { Skill } from "../domain/registry";

export interface StudyCopy {
  nl: string;
  en?: string;
}
export type StudyStep = "prepare" | "practise" | "check";
export interface StudyWord {
  id: string;
  term: string;
  meaning: StudyCopy;
  example: StudyCopy;
  part_of_speech?: string | null;
  forms?: { label: StudyCopy; text: StudyCopy }[];
  contexts?: { id: string; setting: StudyCopy; sentence: StudyCopy; production_prompt?: StudyCopy }[];
}
export interface StudyTopic {
  id: string;
  title: StudyCopy;
  group: string;
  activity_count: number;
  available: boolean;
  availability_note?: StudyCopy | null;
}
export interface StudyCatalog {
  stage_id: string;
  skill: Skill;
  groups: { id: string; title: StudyCopy }[];
  topics: StudyTopic[];
  total_topics: number;
  available_topics: number;
}
export interface StudyQuestion {
  id: string;
  kind: "choice" | "gap" | "short";
  prompt: StudyCopy;
  options: StudyCopy[];
}
export interface StudyPart {
  id: string;
  title: StudyCopy;
  instructions: StudyCopy;
  prompt: StudyCopy;
  sample: StudyCopy | null;
  text: StudyCopy[];
  questions: StudyQuestion[];
  min_words: number;
  max_words: number;
  practice_questions?: { id: string; prompt: StudyCopy; sample: StudyCopy | null }[];
}
export interface StudyLesson {
  stage_id: string;
  topic_id: string;
  skill: Skill;
  title: StudyCopy;
  review_status: string;
  topic_title?: StudyCopy;
  context?: { title: StudyCopy; text: StudyCopy[] };
  preparation: {
    words: StudyWord[];
    grammar: { title: StudyCopy; explanation: StudyCopy; examples: StudyCopy[] }[];
  };
  activities: { id: string; title: StudyCopy }[];
  activity_id: string;
  parts: StudyPart[];
  policy: { ephemeral: boolean; pronunciation_assessed: boolean; recording_max_seconds?: number };
}
export interface StudyFeedback {
  status: "evaluated" | "fixture_unreviewed" | "needs_review";
  score: number | null;
  dimensions: {
    task: number | null;
    grammar: number | null;
    vocabulary: number | null;
    organisation: number | null;
    pronunciation: null;
  };
  summary: StudyCopy;
  corrections: { original: string; replacement: string; category: string; explanation: StudyCopy }[];
  checks: {
    id: string;
    correct: boolean | null;
    review_required?: boolean;
    answer: StudyCopy;
    explanation: StudyCopy;
  }[];
  pronunciation_note: StudyCopy;
  ephemeral: true;
}

/** A copied learning link carries its own context; a profile preference never overrides it. */
export function studyHref(
  stage: string,
  skill: Skill = "reading",
  options: {
    topic?: string;
    activity?: string;
    part?: string;
    step?: StudyStep;
    view?: string;
  } = {},
) {
  const query = new URLSearchParams({ skill });
  for (const [key, value] of Object.entries(options)) if (value) query.set(key, value);
  return `/learn/${encodeURIComponent(stage)}?${query}`;
}

export function studyStep(value?: string): StudyStep {
  return value === "practise" || value === "check" ? value : "prepare";
}

export const studySkillCopy = {
  reading: {
    title: { nl: "Lezen", en: "Reading" },
    action: { nl: "Verhalen en teksten", en: "Stories and texts" },
    icon: "book",
  },
  listening: {
    title: { nl: "Luisteren", en: "Listening" },
    action: { nl: "Luister en vind het antwoord", en: "Listen and find the answer" },
    icon: "headphones",
  },
  speaking: {
    title: { nl: "Spreken", en: "Speaking" },
    action: { nl: "Van korte antwoorden naar een gesprek", en: "From short answers to conversation" },
    icon: "mic",
  },
  writing: {
    title: { nl: "Schrijven", en: "Writing" },
    action: { nl: "Van een zin naar je eigen verhaal", en: "From a sentence to your own message" },
    icon: "pen",
  },
} as const;
