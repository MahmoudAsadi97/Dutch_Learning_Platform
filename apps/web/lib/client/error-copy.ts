import { errorFor, type ErrorOverrides } from "@/lib/client/errors";
import { uiCopy, type Copy } from "@/lib/ui-copy";

/**
 * What a failure means for the screen: an `action` (a button that did something), `input` (the learner's
 * typed or recorded answer stays on screen, so the message may say so) or `load` (nothing was entered; a
 * dropped connection or an unreachable server reads as the screen's own "could not be loaded").
 */
export type FailureContext = "action" | "input" | "load";

/**
 * The catalogue copy for a failed call on a screen. A screen's own `fallback` says what did not work
 * ("Bewaren lukte niet.") where the general message could only say that something did not.
 */
export function errorCopy(
  cause: unknown,
  fallback?: Copy,
  overrides?: ErrorOverrides,
  context: FailureContext = "action",
): Copy {
  const errors = uiCopy.errors;
  const copy = errorFor(cause, errors, overrides, { keepsInput: context === "input" });
  if (!fallback) return copy;
  if (copy === errors.generic || copy === errors.genericKept) return fallback;
  if (context === "load" && (copy === errors.offline || copy === errors.serverAway)) return fallback;
  return copy;
}
