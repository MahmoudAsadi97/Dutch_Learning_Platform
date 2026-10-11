/**
 * The word-by-word comparison of a typed answer with the one it was compared with, as the API's diff gives it
 * (compare.py): each part is a word that matched, one that is missing, one too many, or one typed otherwise.
 * Pure, so the unit tests load it without a bundler.
 */
import type { DiffOp } from "../../lib/client/exercises";

export type DiffPart =
  | { kind: "same"; text: string }
  | { kind: "missing"; expected: string }
  | { kind: "extra"; given: string }
  | { kind: "changed"; given: string; expected: string };

/** The parts to show, in order; neighbouring matched words are joined, so the sentence reads as one. */
export function diffParts(ops: readonly DiffOp[]): DiffPart[] {
  const parts: DiffPart[] = [];
  for (const op of ops) {
    const last = parts[parts.length - 1];
    if (op.op === "same") {
      const text = op.expected || op.given;
      if (last?.kind === "same") last.text = `${last.text} ${text}`;
      else parts.push({ kind: "same", text });
    } else if (op.op === "missing") parts.push({ kind: "missing", expected: op.expected });
    else if (op.op === "extra") parts.push({ kind: "extra", given: op.given });
    else parts.push({ kind: "changed", given: op.given, expected: op.expected });
  }
  return parts;
}

/** Whether the comparison has anything to point at (an answer typed exactly right has none). */
export function hasDifference(ops: readonly DiffOp[]): boolean {
  return ops.some((op) => op.op !== "same");
}
