import { errorFor, type ErrorOverrides } from "@/lib/client/errors";
import { uiCopy, type Copy } from "@/lib/ui-copy";

/**
 * The catalogue copy for a failed call on a screen. A screen's own `fallback` says what did not work
 * ("Bewaren lukte niet.") where the general message could only say that something did not.
 */
export function errorCopy(cause: unknown, fallback?: Copy, overrides?: ErrorOverrides): Copy {
  const copy = errorFor(cause, uiCopy.errors, overrides);
  return copy === uiCopy.errors.generic && fallback ? fallback : copy;
}
