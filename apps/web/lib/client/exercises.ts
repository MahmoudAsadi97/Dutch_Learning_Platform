"use client";

/**
 * The exercise engine's client: sessions are generated and graded on the API, so the browser never holds an
 * answer before it is given. Types mirror `apps/api/src/dlp/domains/exercises/schemas.py`. Every answer keeps
 * its request id across a retry (the runner mints one per item and attempt), so a lost response is replayed,
 * never counted twice.
 */
import type { Skill } from "../types";
import { ApiError, apiFetch, apiJson, newRequestId } from "./api";

export interface Text {
  nl?: string | null;
  en?: string | null;
  fa?: string | null;
}
export interface Option extends Text {
  id: string;
}
export interface SupportOption extends Option {
  definition?: string | null;
}
export interface Hint {
  first: string;
  /** The letters of each word of the answer. */
  letters: readonly number[];
}
export interface IntroWord {
  term: string;
  meaning: Text;
  example: Text;
}
/** A word of a practice topic, shown beside its passage. */
export interface PassageWord {
  term: string;
  meaning: Text;
}

export type Prompt =
  | {
      kind: "choice";
      direction: "meaning" | "term" | "definition" | "question";
      stem: Text;
      options: Option[];
    }
  | { kind: "cloze_choice"; sentence: string; cue: Text | null; options: Option[] }
  | { kind: "odd_one_out"; topic: Text; options: Option[] }
  | { kind: "intro"; words: IntroWord[] }
  | { kind: "cloze_typed"; sentence: string; cue: Text | null; hint: Hint }
  | { kind: "typed_recall"; cue: Text; hint: Hint }
  | { kind: "flashcard"; term: string }
  | { kind: "match_pairs"; left: Option[]; right: Option[] }
  | { kind: "de_het"; bins: ("de" | "het")[]; options: Option[] }
  | { kind: "sentence_builder"; tiles: Option[]; end: string; cue: Text | null }
  | { kind: "sentence_order"; sentences: Option[] }
  | { kind: "listen_choose"; options: Option[] }
  | { kind: "dictation"; word_count: number }
  | { kind: "shadow"; sentence: string }
  /** A topic's or lesson's text, Dutch only until every question is answered, then with its translation. */
  | { kind: "read_passage"; text: Text; vocabulary: PassageWord[] }
  /** Heard from the topic's or lesson's own listening route, part by part; the transcript once answered. */
  | { kind: "listen_passage"; parts: number; transcript: Text | null; vocabulary: PassageWord[] };
export type Kind = Prompt["kind"];
/** Steps with nothing to answer: closed with done, never graded. The engine plans them; a client never asks. */
export type UngradedKind = "intro" | "read_passage" | "listen_passage";
export type GradedKind = Exclude<Kind, UngradedKind>;

/** "almost" and "not_heard" are shown in a neutral colour, never red; "accepted" is the learner's overrule. */
export type Outcome =
  "correct" | "almost" | "incorrect" | "skipped" | "done" | "accepted" | "heard" | "not_heard";

export interface WordCard {
  library_id: string;
  term: string;
  meaning: Text;
  example: Text;
}
export interface DiffOp {
  op: "same" | "missing" | "extra" | "changed";
  expected: string;
  given: string;
}
export interface PartResult {
  given: string;
  correct: string;
  ok: boolean;
}
export interface Feedback {
  outcome: Outcome;
  correct?: string | null;
  given?: string | null;
  support?: SupportOption[];
  explanation?: Text | null;
  word?: WordCard | null;
  sentence?: string | null;
  odd_topic?: Text | null;
  typed?: string | null;
  expected?: string | null;
  notes?: string[];
  diff?: DiffOp[];
  pairs?: Record<string, PartResult> | null;
  bins?: Record<string, PartResult> | null;
  cards?: Record<string, WordCard> | null;
  order?: string[] | null;
  given_order?: string[] | null;
  first_difference?: number | null;
  texts?: string[] | null;
  translation?: Record<string, string[]> | null;
  known?: boolean | null;
  transcript?: string | null;
  target_words?: number | null;
  matched_words?: number | null;
  missed?: string[] | null;
  overridable?: boolean;
}
export interface Progress {
  closed: number;
  total: number;
  queued: number;
}
export interface ItemView {
  id: string;
  position: number;
  kind: Kind;
  skill: string;
  state: "open" | "closed";
  attempts_left: number;
  prompt: Prompt;
  feedback: Feedback | null;
  hint_used?: boolean;
}
/** A missed word the learner may save; the example and library id go with it into the word bank. */
export interface Suggestion {
  key: string;
  term: string;
  meaning_en: string;
  meaning_fa: string;
  example?: string;
  library_id?: string;
}
/** What a topic or lesson session did for its activity: only the first answers count, by the course's rule. */
export interface Completion {
  scope: "topic" | "lesson";
  skill: Skill;
  topic_id: string | null;
  counted: boolean;
  /** Why it did not count: a retry, a question never tried, changed content, or a warm-up before a task. */
  reason: "retry" | "unfinished" | "content_changed" | "open_task" | "assisted" | null;
  passed: boolean | null;
  correct: number | null;
  total: number | null;
  required: number | null;
  /** The topic (or the lesson's stage skill) is completed, by this session or before. */
  completed: boolean;
  /** Questions missed the first time here, which a retry session asks again. */
  to_retry: number;
}
export interface Summary {
  items_total: number;
  answered: number;
  first_try_correct: number;
  fixed_on_retry: number;
  skipped: number;
  overridden: number;
  points_earned: number;
  session_bonus: number;
  by_kind: Record<string, { total: number; first_try_correct: number }>;
  missed: { ref: string; term: string | null; expected: string | null }[];
  suggestions: Suggestion[];
  completion?: Completion | null;
}
export interface SessionView {
  id: string;
  source: string;
  stage_id: string;
  focus: string;
  library_topic: string | null;
  topic_id?: string | null;
  skill?: Skill | null;
  retry?: boolean;
  status: "active" | "finished" | "abandoned";
  content_status: "unreviewed";
  resumed: boolean;
  items: ItemView[];
  next_item_id: string | null;
  progress: Progress;
  summary: Summary | null;
}
export interface AnswerResult {
  item_id: string;
  attempt: number;
  outcome: Outcome;
  closed: boolean;
  requeue: boolean;
  attempts_left: number;
  feedback: Feedback;
  points: number;
  progress: Progress;
  next_item_id: string | null;
  goal_reached?: boolean | null;
}
export interface FinishResult {
  id: string;
  status: "finished";
  summary: Summary;
  points: number;
  goal_reached?: boolean | null;
}

/** An answer in the shape its kind takes; a board (pairs, bins, order) is sent whole. */
export type Answer =
  | { option: string }
  | { done: true }
  | { text: string }
  | { known: boolean }
  | { pairs: Record<string, string> }
  | { bins: Record<string, "de" | "het"> }
  | { order: string[] };

export interface CreateSession {
  source?: "stage_skill" | "while_you_wait" | "topic";
  stage_id?: string;
  library_topic?: string;
  size?: number;
  fresh?: boolean;
  /** Only the kinds this client can show (always with choice). */
  kinds?: readonly GradedKind[];
  /** A practice topic and the skill practised (source "topic"). */
  topic_id?: string;
  skill?: Skill;
  /** Only the questions the last session on this topic missed the first time. */
  retry?: boolean;
}

/** Why the learner reports an exercise ("Meld een probleem"). */
export type ReportReason = "answer_wrong" | "unclear" | "sound" | "other";

const item = (sessionId: string, itemId: string, action: string) =>
  `exercises/sessions/${sessionId}/items/${itemId}/${action}`;

export const exercises = {
  create: (body: CreateSession, requestId = newRequestId()) =>
    apiJson<SessionView>("exercises/sessions", {
      method: "POST",
      body: { focus: "words", ...body, request_id: requestId },
      requestId,
    }),
  get: (sessionId: string, signal?: AbortSignal) =>
    apiJson<SessionView>(`exercises/sessions/${sessionId}`, { signal }),
  assistance: (sessionId: string, itemId: string, signal?: AbortSignal) =>
    apiJson<ItemView>(item(sessionId, itemId, "assistance"), { method: "POST", signal }),
  answer: (sessionId: string, itemId: string, answer: Answer, requestId: string, hintUsed = false) =>
    apiJson<AnswerResult>(item(sessionId, itemId, "answer"), {
      method: "POST",
      body: { request_id: requestId, answer, hint_used: hintUsed },
      requestId,
    }),
  skip: (
    sessionId: string,
    itemId: string,
    requestId: string,
    reason: "unknown" | "no_microphone" | "no_audio" = "unknown",
  ) =>
    apiJson<AnswerResult>(item(sessionId, itemId, "skip"), {
      method: "POST",
      body: { request_id: requestId, reason },
      requestId,
    }),
  override: (sessionId: string, itemId: string, requestId: string) =>
    apiJson<AnswerResult>(item(sessionId, itemId, "override"), {
      method: "POST",
      body: { request_id: requestId },
      requestId,
    }),
  /** The item's sound (a word or sentence of the course), served from the speech cache; a development
   * environment's test tone says so. */
  audio: async (
    sessionId: string,
    itemId: string,
    signal?: AbortSignal,
  ): Promise<{ blob: Blob; developmentTone: boolean }> => {
    const response = await apiFetch(item(sessionId, itemId, "audio"), { method: "POST", signal });
    if (!response.ok) {
      // keep the status and code, so a used-up allowance or an outage reads as such
      const body = (await response.json().catch(() => null)) as { detail?: unknown; code?: unknown } | null;
      throw new ApiError(
        response.status,
        String(body?.detail ?? response.statusText),
        response.headers.get("x-request-id") ?? "",
        typeof body?.code === "string" ? body.code : "",
      );
    }
    return {
      blob: await response.blob(),
      developmentTone: response.headers.get("x-audio-voice") === "fixture-tone",
    };
  },
  /** A shadowing attempt: heard or not heard, never a score; the recording is not kept. */
  record: (sessionId: string, itemId: string, requestId: string, blob: Blob, fileName: string) => {
    const form = new FormData();
    form.append("request_id", requestId);
    form.append("audio", blob, fileName);
    return apiJson<AnswerResult>(item(sessionId, itemId, "recording"), {
      method: "POST",
      formData: form,
      requestId,
    });
  },
  /** "Meld een probleem": kept with the item for the content review; it changes nothing in the session. */
  report: (sessionId: string, itemId: string, requestId: string, reason: ReportReason, note: string) =>
    apiJson<{ item_id: string; reason: ReportReason }>(item(sessionId, itemId, "report"), {
      method: "POST",
      body: { request_id: requestId, reason, note: note.trim() || null },
      requestId,
    }),
  finish: (sessionId: string, requestId: string, early = false) =>
    apiJson<FinishResult>(`exercises/sessions/${sessionId}/finish`, {
      method: "POST",
      body: { request_id: requestId, early },
      requestId,
    }),
};
