/**
 * What a topic session's summary says about its activity and which way it offers on (roadmap 3.9). The server
 * decides what counted (`summary.completion`); this only chooses the words and the order of the buttons. Pure,
 * so the unit tests load it without a bundler.
 */
import type { Completion } from "../../lib/client/exercises";
import type { exerciseCopy } from "../../lib/copy/exercise";

type CopyKey = keyof typeof exerciseCopy;

export interface CompletionLine {
  key: CopyKey;
  values?: Record<string, number>;
}

/** The lines about the activity: what counted, or why not, and what that means for the topic. */
export function completionLines(completion: Completion | null | undefined): CompletionLine[] {
  if (!completion || completion.scope !== "topic") return [];
  const already: CompletionLine[] = completion.completed ? [{ key: "completionAlready" }] : [];
  switch (completion.reason) {
    case "open_task":
      return [{ key: "completionWarmUp" }];
    case "retry":
      return [
        { key: "completionRetry" },
        completion.completed ? { key: "completionAlready" } : { key: "completionWhole" },
      ];
    case "unfinished":
      return [{ key: "completionUnfinished" }, ...already];
    case "content_changed":
      return [{ key: "completionChanged" }, ...already];
  }
  if (completion.passed) return [{ key: "completionPassed" }];
  if (completion.completed) return [{ key: "completionKept" }];
  if (completion.required !== null && completion.total !== null && completion.required < completion.total)
    return [{ key: "completionRule", values: { required: completion.required, total: completion.total } }];
  return [{ key: "completionRuleAll" }];
}

/** Whether the activity line reads as done (a check) or open (neutral, never a miss colour). */
export function completionState(completion: Completion): "done" | "open" {
  return completion.reason !== "open_task" && completion.completed ? "done" : "open";
}

export interface SummaryAction {
  kind: "retry" | "again" | "exit";
  variant: "primary" | "secondary" | "ghost";
}

/** The summary's buttons in order: the way that helps most first. */
export function summaryActions(
  completion: Completion | null | undefined,
  canRetry: boolean,
): SummaryAction[] {
  if (!completion)
    return [
      { kind: "again", variant: "primary" },
      { kind: "exit", variant: "secondary" },
    ];
  if (completion.reason === "open_task")
    return [
      { kind: "exit", variant: "primary" },
      { kind: "again", variant: "secondary" },
    ];
  if (canRetry && completion.to_retry > 0)
    return [
      { kind: "retry", variant: "primary" },
      { kind: "again", variant: "secondary" },
      { kind: "exit", variant: "ghost" },
    ];
  if (completion.completed)
    return [
      { kind: "exit", variant: "primary" },
      { kind: "again", variant: "secondary" },
    ];
  return [
    { kind: "again", variant: "primary" },
    { kind: "exit", variant: "secondary" },
  ];
}

/** "Nog een oefening" for a page's session; a topic's says what starting again means there. */
export function againLabel(completion: Completion | null | undefined): CopyKey {
  if (!completion) return "again";
  if (completion.reason === "open_task") return "warmUpAgain";
  return completion.skill === "reading" || completion.skill === "listening" ? "againAll" : "again";
}
