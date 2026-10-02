"use client";

import { apiJson, newRequestId } from "./api";
import type { EpisodeQuestion, GlossaryItem, WordItem } from "./stories";

export type VideoStatus = "queued" | "writing" | "rendering" | "ready" | "failed";
export interface VideoScene { nl: string; en: string; fa: string; keyword: string }
export interface VideoCue { start: number; end: number; text: string; scene: number }

export interface VideoSummary {
  id: string; stage_id: string; kind: string; kind_label: string; topic: string; topic_id: string; status: VideoStatus;
  error_code: string; title: string; word_count: number; duration_seconds: number; presenter: string; renderer: string;
  attempts: number; watched_at: string | null; rating: number; created_at: string; ready_at: string | null;
  content_status: string; warnings: string[]; failure_reasons: string[]; scene_count: number;
}
export interface Video extends VideoSummary {
  scenes: VideoScene[]; glossary: GlossaryItem[]; cues: VideoCue[]; questions: EpisodeQuestion[]; answered: boolean;
  provider: string; model: string; voice: string; media_url: string; subtitles_url: string;
}
export interface VideoLibrary {
  items: VideoSummary[]; levels: { id: string; label: string }[]; kinds: { id: string; label: string }[];
  default_stage: string; renderer: { name: string; label: string; voice: string }; min_seconds: number; max_seconds: number; max_pending: number;
}

export const videos = {
  library: (signal?: AbortSignal) => apiJson<VideoLibrary>("videos", { signal }),
  get: (id: string, signal?: AbortSignal) => apiJson<Video>(`videos/${id}`, { signal }),
  request: (stageId: string, topic: string, kind: string, requestId = newRequestId()) =>
    apiJson<VideoSummary>("videos", { method: "POST", body: { request_id: requestId, stage_id: stageId, topic, kind }, requestId }),
  watched: (id: string) => apiJson<Video>(`videos/${id}/watched`, { method: "POST" }),
  answer: (id: string, answers: Record<string, number>, requestId: string) =>
    apiJson<Video>(`videos/${id}/answers`, { method: "POST", body: { request_id: requestId, answers }, requestId }),
  rate: (id: string, rating: 1 | -1) => apiJson<Video>(`videos/${id}/rating`, { method: "POST", body: { rating } }),
  saveWord: (id: string, term: string) =>
    apiJson<{ item: WordItem; created: boolean }>(`videos/${id}/words`, { method: "POST", body: { term } }),
  retry: (id: string) => apiJson<VideoSummary>(`videos/${id}/retry`, { method: "POST" }),
};

export function videoHref(id: string) { return `/videos/${id}`; }

/** "1:05" for the duration badges. */
export function clock(seconds: number): string {
  const whole = Math.max(0, Math.round(seconds));
  return `${Math.floor(whole / 60)}:${String(whole % 60).padStart(2, "0")}`;
}

/** The scene the playhead is in, from the cues; -1 before the first cue. */
export function sceneAt(cues: VideoCue[], time: number): number {
  let current = -1;
  for (const cue of cues) {
    if (cue.start <= time + 0.05) current = cue.scene; else break;
  }
  return current;
}
