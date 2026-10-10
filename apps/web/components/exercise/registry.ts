/**
 * The kinds this runner can show. A session is created with exactly these (the API plans nothing else), so a
 * kind is added here in the same change as its renderer (step 3.7 adds the boards, typing, listening and
 * speaking). Pure, so the unit tests load it without a bundler.
 */
import type { Kind, Prompt } from "../../lib/client/exercises";

export const RENDERED_KINDS = ["choice", "cloze_choice", "odd_one_out"] as const satisfies readonly Exclude<
  Kind,
  "intro"
>[];

export type RenderedKind = (typeof RENDERED_KINDS)[number];

/** The prompts the runner draws with options to choose from. */
export type ChoicePrompt = Extract<Prompt, { kind: RenderedKind }>;

export function isChoicePrompt(prompt: Prompt): prompt is ChoicePrompt {
  return (RENDERED_KINDS as readonly string[]).includes(prompt.kind);
}

/** The option a number key (1 to 4) picks, or null. */
export function optionForKey(key: string, optionIds: readonly string[]): string | null {
  if (!/^[1-9]$/.test(key)) return null;
  return optionIds[Number(key) - 1] ?? null;
}
