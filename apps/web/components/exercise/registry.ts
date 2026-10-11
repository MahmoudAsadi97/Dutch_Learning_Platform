/**
 * The kinds this runner can show. A session is created with exactly these (the API plans nothing else), so a
 * kind is added here in the same change as its renderer: every kind the engine plans has one now (the
 * flashcard is for word review, 5.1). Pure, so the unit tests load it without a bundler.
 */
import type { CreateSession, GradedKind, Prompt } from "../../lib/client/exercises";
import type { Skill } from "../../lib/types";

const CHOICE_KINDS = ["choice", "cloze_choice", "odd_one_out", "listen_choose"] as const;
const TYPED_KINDS = ["cloze_typed", "typed_recall", "dictation"] as const;

export const RENDERED_KINDS = [
  ...CHOICE_KINDS,
  ...TYPED_KINDS,
  "match_pairs",
  "de_het",
  "sentence_builder",
  "sentence_order",
  "shadow",
] as const satisfies readonly GradedKind[];

export type RenderedKind = (typeof RENDERED_KINDS)[number];

/** The prompts the runner draws as options to choose from (the others are boards). */
export type ChoicePrompt = Extract<Prompt, { kind: (typeof CHOICE_KINDS)[number] }>;

export function isChoicePrompt(prompt: Prompt): prompt is ChoicePrompt {
  return (CHOICE_KINDS as readonly string[]).includes(prompt.kind);
}

/** The prompts answered by typing. */
export type TypedPrompt = Extract<Prompt, { kind: (typeof TYPED_KINDS)[number] }>;

export function isTypedPrompt(prompt: Prompt): prompt is TypedPrompt {
  return (TYPED_KINDS as readonly string[]).includes(prompt.kind);
}

/** A topic's or lesson's passage step: read or heard, then closed with done (never asked for in `kinds`). */
export type PassagePrompt = Extract<Prompt, { kind: "read_passage" | "listen_passage" }>;

export function isPassagePrompt(prompt: Prompt): prompt is PassagePrompt {
  return prompt.kind === "read_passage" || prompt.kind === "listen_passage";
}

/** The server adds the translation, or the transcript, once every question about the passage is answered. */
export function passageRevealed(prompt: PassagePrompt): boolean {
  return prompt.kind === "read_passage"
    ? Boolean(prompt.text.en || prompt.text.fa)
    : prompt.transcript !== null;
}

/** Where a listening passage is heard, part by part: the topic's own listening route, or the lesson's. */
export function passageAudioPath(session: { stage_id: string; topic_id?: string | null }): string {
  return session.topic_id
    ? `curriculum/${session.stage_id}/topics/${encodeURIComponent(session.topic_id)}/listening`
    : `curriculum/${session.stage_id}/listening`;
}

/** A practice topic and the skill a session on it practises. */
export interface TopicActivity {
  stageId: string;
  topicId: string;
  skill: Skill;
}

/**
 * The create request: a page's session asks for its kinds only (exactly as before topics existed); a topic's
 * session names the topic and skill, and `retry` only when it asks the missed questions again.
 */
export function sessionRequest(
  source: "stage_skill" | "while_you_wait" | "topic",
  activity: TopicActivity | null,
  retry: boolean,
  kinds: readonly GradedKind[],
): CreateSession {
  if (source !== "topic" || !activity) return { source, kinds };
  return {
    source: "topic",
    stage_id: activity.stageId,
    topic_id: activity.topicId,
    skill: activity.skill,
    kinds,
    ...(retry ? { retry: true } : {}),
  };
}

/** Kinds with a sound of their own: only these can be reported for a wrong or unclear sound. */
const SOUND_KINDS: ReadonlySet<string> = new Set(["listen_choose", "dictation", "shadow"]);

export function hasSound(kind: string): boolean {
  return SOUND_KINDS.has(kind);
}

/** Persian (۱) and Arabic (١) digits, as a Persian keyboard types them. */
const EASTERN_DIGITS = /^[۱-۹١-٩]$/;

/**
 * The option a number key (1 to 9) picks, or null. The digit typed counts first, in Latin, Persian or Arabic
 * figures; on a layout where the number row types letters without Shift (Belgian AZERTY: "é" for 2), the
 * physical key does. The number pad counts only when it types a digit (NumLock on).
 */
export function optionForKey(key: string, code: string, optionIds: readonly string[]): string | null {
  let digit: number | null = null;
  if (/^[1-9]$/.test(key)) digit = Number(key);
  else if (EASTERN_DIGITS.test(key)) digit = key.charCodeAt(0) - (key >= "۰" ? 0x06f0 : 0x0660);
  else {
    const physical = /^Digit([1-9])$/.exec(code);
    if (physical) digit = Number(physical[1]);
  }
  return digit === null ? null : (optionIds[digit - 1] ?? null);
}
