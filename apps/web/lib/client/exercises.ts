"use client";

/**
 * The exercise engine's client: sessions are generated and graded on the API, so the browser never holds an
 * answer before it is given. Types mirror `apps/api/src/dlp/domains/exercises/schemas.py`. Every answer keeps
 * its request id across a retry (the runner mints one per item and attempt), so a lost response is replayed,
 * never counted twice.
 */
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
  length: number;
}
export interface IntroWord {
  term: string;
  meaning: Text;
  example: Text;
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
  | { kind: "shadow"; sentence: string };
export type Kind = Prompt["kind"];

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
  suggestions: { key: string; term: string; meaning_en: string; meaning_fa: string }[];
}
export interface SessionView {
  id: string;
  source: string;
  stage_id: string;
  focus: string;
  library_topic: string | null;
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
  source?: "stage_skill" | "while_you_wait";
  stage_id?: string;
  library_topic?: string;
  size?: number;
  fresh?: boolean;
  /** Only the kinds this client can show (always with choice). */
  kinds?: readonly Exclude<Kind, "intro">[];
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
  /** The item's sound (a word or sentence of the course), served from the speech cache. */
  audio: async (sessionId: string, itemId: string, signal?: AbortSignal): Promise<Blob> => {
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
    return response.blob();
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
