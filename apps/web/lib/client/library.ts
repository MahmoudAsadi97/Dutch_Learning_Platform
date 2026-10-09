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
}

export interface LibraryPage<T> {
  total: number;
  offset: number;
  limit: number;
  items: T[];
}

export const library = {
  /** The first words of a stage's library, the same list the library page opens with. */
  words: (stageId: string, limit: number, signal?: AbortSignal) =>
    apiJson<LibraryPage<LibraryWord>>(
      `library/${encodeURIComponent(stageId)}/vocabulary?${new URLSearchParams({ limit: String(limit) })}`,
      { signal },
    ),
};
