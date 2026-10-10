"use client";

import { apiJson, newRequestId } from "./api";
import type { LibraryWord } from "./library";

export interface StoryParagraph {
  nl: string;
  en: string;
  fa?: string;
}
export interface GlossaryItem {
  term: string;
  meaning_en: string;
  meaning_fa: string;
  example: string;
}
export interface EpisodeQuestion {
  index: number;
  prompt: string;
  options: string[];
  answer_index?: number;
  evidence?: string;
  chosen?: number | null;
  correct?: boolean;
}
export interface EpisodeChoice {
  id: "a" | "b";
  label: string;
}
export type EpisodeStatus = "queued" | "generating" | "ready" | "failed";

export interface EpisodeSummary {
  id: string;
  number: number;
  stage_id: string;
  status: EpisodeStatus;
  error_code: string;
  title: string;
  theme: string;
  theme_source: string;
  topic_id: string;
  mood: string;
  word_count: number;
  read_at: string | null;
  rating: number;
  chosen_choice: string;
  created_at: string;
  content_status: string;
  attempts: number;
  warnings: string[];
  failure_reasons: string[];
}
export interface Episode extends EpisodeSummary {
  paragraphs: StoryParagraph[];
  glossary: GlossaryItem[];
  choices: EpisodeChoice[];
  questions: EpisodeQuestion[];
  answered: boolean;
  previous_choice: string;
  read_aloud: Record<string, { matched_words: number; target_words: number; attempts: number }>;
  provider: string;
  model: string;
}
export interface SeriesView {
  id: string;
  title: string;
  stage_id: string;
  episode_count: number;
  town: string;
  cast: { name: string; role: string }[];
  memory: { number: number; title: string; recap: string; choice: string }[];
}
export interface WordItem {
  id: string;
  term: string;
  meaning_en: string;
  meaning_fa: string;
  example: string;
  source_kind: string;
  source_id: string;
  ease: number;
  interval_days: number;
  repetitions: number;
  lapses: number;
  due_at: string;
  due: boolean;
  learned: boolean;
  last_grade: number | null;
  created_at: string;
}
export interface WordStats {
  total: number;
  due_count: number;
  learned_count: number;
  new_count: number;
}
export interface TodayPlan {
  date: string;
  streak: { current: number; best: number; today_active: boolean; today_points: number; active_days: number };
  goal: { target: number; points: number; met: boolean };
  series: SeriesView;
  episode: Episode | null;
  failed: EpisodeSummary | null;
  awaiting_choice: EpisodeSummary | null;
  words: WordStats & { preview: WordItem[] };
  next_step: "read" | "choose" | "review" | "wait" | "explore";
  recent_days: { day: string; points: number; goal_met: boolean }[];
  levels: { id: string; label: string }[];
  videos?: {
    ready: { id: string; title: string; topic: string; kind_label: string; duration_seconds: number } | null;
    pending: number;
  };
}
export type Grade = "again" | "hard" | "good" | "easy";

export { stageLabels } from "../domain/registry";

export const stories = {
  today: (signal?: AbortSignal) => apiJson<TodayPlan>("today", { signal }),
  library: (signal?: AbortSignal) =>
    apiJson<{ series: SeriesView; items: EpisodeSummary[] }>("stories", { signal }),
  episode: (id: string, signal?: AbortSignal) => apiJson<Episode>(`stories/episodes/${id}`, { signal }),
  request: (theme: string, requestId = newRequestId()) =>
    apiJson<EpisodeSummary>("stories/episodes", {
      method: "POST",
      body: { request_id: requestId, theme },
      requestId,
    }),
  level: (stageId: string) =>
    apiJson<SeriesView>("stories/level", { method: "POST", body: { stage_id: stageId } }),
  read: (id: string) => apiJson<Episode>(`stories/episodes/${id}/read`, { method: "POST" }),
  answer: (id: string, answers: Record<string, number>, requestId: string) =>
    apiJson<Episode>(`stories/episodes/${id}/answers`, {
      method: "POST",
      body: { request_id: requestId, answers },
      requestId,
    }),
  choose: (id: string, choice: "a" | "b") =>
    apiJson<Episode>(`stories/episodes/${id}/choice`, { method: "POST", body: { choice } }),
  rate: (id: string, rating: 1 | -1) =>
    apiJson<Episode>(`stories/episodes/${id}/rating`, { method: "POST", body: { rating } }),
  retry: (id: string) => apiJson<EpisodeSummary>(`stories/episodes/${id}/retry`, { method: "POST" }),
  translate: (id: string, paragraphIndex: number, requestId = newRequestId()) =>
    apiJson<{ paragraph_index: number; fa: string; cached: boolean }>(`stories/episodes/${id}/translate`, {
      method: "POST",
      body: { request_id: requestId, paragraph_index: paragraphIndex },
      requestId,
    }),
  saveWord: (id: string, term: string) =>
    apiJson<{ item: WordItem; created: boolean }>(`stories/episodes/${id}/words`, {
      method: "POST",
      body: { term },
    }),
  readAloud: (id: string, paragraphIndex: number, blob: Blob, fileName: string, signal?: AbortSignal) => {
    const form = new FormData();
    form.append("paragraph_index", String(paragraphIndex));
    form.append("audio", blob, fileName);
    return apiJson<{
      paragraph_index: number;
      transcript: string;
      target_words: number;
      matched_words: number;
      missed: string[];
      extra: string[];
      points: number;
    }>(`stories/episodes/${id}/read-aloud`, { method: "POST", formData: form, signal });
  },
};

export const words = {
  due: (limit = 20, signal?: AbortSignal) =>
    apiJson<WordStats & { items: WordItem[] }>(`words?due=true&limit=${limit}`, { signal }),
  all: (signal?: AbortSignal) => apiJson<WordStats & { items: WordItem[] }>("words?limit=500", { signal }),
  save: (term: string, meaning_en = "", meaning_fa = "", example = "") =>
    apiJson<{ item: WordItem; created: boolean }>("words", {
      method: "POST",
      body: { term, meaning_en, meaning_fa, example, source_kind: "manual" },
    }),
  /** A word the practice summary suggested: a library word with its example when the suggestion knows it. */
  saveSuggestion: (item: {
    term: string;
    meaning_en: string;
    meaning_fa: string;
    example?: string;
    library_id?: string;
  }) =>
    apiJson<{ item: WordItem; created: boolean }>("words", {
      method: "POST",
      body: {
        term: item.term,
        meaning_en: item.meaning_en,
        meaning_fa: item.meaning_fa,
        example: item.example ?? "",
        ...(item.library_id
          ? { source_kind: "library", source_id: item.library_id }
          : { source_kind: "manual" }),
      },
    }),
  /** A word chosen from a stage library; the word list keeps where it came from. */
  saveLibrary: (item: LibraryWord) =>
    apiJson<{ item: WordItem; created: boolean }>("words", {
      method: "POST",
      body: {
        term: item.term,
        meaning_en: item.meaning.en ?? "",
        meaning_fa: item.meaning.fa ?? "",
        example: item.example.nl,
        source_kind: "library",
        source_id: item.id,
      },
    }),
  review: (id: string, grade: Grade, requestId = newRequestId()) =>
    apiJson<WordItem>(`words/${id}/review`, {
      method: "POST",
      body: { request_id: requestId, grade },
      requestId,
    }),
  remove: (id: string) => apiJson<null>(`words/${id}`, { method: "DELETE" }),
};

export function episodeHref(id: string) {
  return `/verhalen/${id}`;
}

/** A gentle, non-judging line for the Today page. */
export function greeting(hour = new Date().getHours()): string {
  if (hour < 12) return "Goeiemorgen";
  if (hour < 18) return "Goeiemiddag";
  return "Goeienavond";
}
