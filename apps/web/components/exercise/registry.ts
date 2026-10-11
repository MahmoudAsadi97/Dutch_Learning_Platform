/**
 * The kinds this runner can show. A session is created with exactly these (the API plans nothing else), so a
 * kind is added here in the same change as its renderer (step 3.7b adds typing, listening and speaking). Pure, so the unit tests load it without a bundler.
 */
import type { Kind, Prompt } from "../../lib/client/exercises";

const CHOICE_KINDS = ["choice", "cloze_choice", "odd_one_out"] as const;

export const RENDERED_KINDS = [
  ...CHOICE_KINDS,
  "match_pairs",
  "de_het",
  "sentence_builder",
  "sentence_order",
] as const satisfies readonly Exclude<Kind, "intro">[];

export type RenderedKind = (typeof RENDERED_KINDS)[number];

/** The prompts the runner draws as options to choose from (the others are boards). */
export type ChoicePrompt = Extract<Prompt, { kind: (typeof CHOICE_KINDS)[number] }>;

export function isChoicePrompt(prompt: Prompt): prompt is ChoicePrompt {
  return (CHOICE_KINDS as readonly string[]).includes(prompt.kind);
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
