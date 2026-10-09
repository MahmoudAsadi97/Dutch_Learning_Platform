/**
 * Who is sent to /welkom first. Pure, so the node:test suite can pin it. Only a known "not onboarded"
 * (`null`) redirects. While the profile is still loading the gate waits, so no learning page (and no request
 * that queues work at the default level) runs before the learner has chosen; once loading fails it opens.
 */

/** Places a learner who has not finished the welcome may still open. */
export const FIRST_RUN_EXEMPT = ["/welkom", "/settings", "/over", "/dev"] as const;

export function firstSegment(path: string): string {
  return `/${path.replace(/^\/+/, "").split(/[/?#]/)[0] ?? ""}`;
}

export type Gate = "open" | "wait" | "welcome";

export function gateFor(
  path: string,
  onboardedAt: string | null | undefined,
  enabled: boolean,
  pending = false,
): Gate {
  if (!enabled || (FIRST_RUN_EXEMPT as readonly string[]).includes(firstSegment(path))) return "open";
  if (onboardedAt === null) return "welcome";
  return onboardedAt === undefined && pending ? "wait" : "open";
}

export function needsWelcome(
  path: string,
  onboardedAt: string | null | undefined,
  enabled: boolean,
): boolean {
  return gateFor(path, onboardedAt, enabled) === "welcome";
}
