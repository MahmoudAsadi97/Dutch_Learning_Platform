import type { Ref } from "react";

import type { Answer, Feedback, Prompt } from "../../lib/client/exercises";

/**
 * What a board renderer (match pairs, de/het, tiles, ordering) gets from the runner. A board is answered
 * whole: the renderer keeps its parts and reports the answer only once every part is in place (null before),
 * and the runner sends it on "Controleer". The renderer is keyed per item and attempt, so a new question
 * starts empty.
 */
export interface BoardProps<K extends Prompt["kind"]> {
  prompt: Extract<Prompt, { kind: K }>;
  /** The verdict of the answer just given; the board then shows each part's result and is read-only. */
  feedback: Feedback | null;
  onDraft: (answer: Answer | null) => void;
  headingRef?: Ref<HTMLHeadingElement>;
}
