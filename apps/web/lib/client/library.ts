"use client";

import type { LearningCopy } from "@/components/LanguageSupport";
import { apiJson } from "./api";

/** One word from a stage's library, with its meaning and an example sentence. */
export interface LibraryWord {
  id: string;
  term: string;
  topic: LearningCopy;
  meaning: LearningCopy;
  example: LearningCopy;
  part_of_speech?: "noun" | "verb" | "adjective" | "adverb" | "expression" | "other";
  article?: string;
  plural?: string;
  productive_core?: boolean;
  core_order?: number | null;
  forms?: { label: LearningCopy; text: LearningCopy }[];
  contexts?: {
    id: string;
    setting: LearningCopy;
    sentence: LearningCopy;
    production_prompt: LearningCopy;
    structure: string;
  }[];
}

export interface LibraryPage<T> {
  total: number;
  offset: number;
  limit: number;
  items: T[];
}

export const library = {
  /** A short, mixed starter round from the same productive core the library opens with. */
  words: (stageId: string, limit: number, signal?: AbortSignal) =>
    apiJson<LibraryPage<LibraryWord>>(
      `library/${encodeURIComponent(stageId)}/vocabulary?${new URLSearchParams({ limit: String(limit), core_only: "true" })}`,
      { signal },
    ),
};
