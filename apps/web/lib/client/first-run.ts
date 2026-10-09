/**
 * Who is sent to /welkom first. Pure, so the node:test suite can pin it. The gate fails open: a profile
 * that is not known yet (`undefined`) never redirects, only a known "not onboarded" (`null`) does.
 */

/** Places a learner who has not finished the welcome may still open. */
export const FIRST_RUN_EXEMPT = ["/welkom", "/settings", "/over", "/dev"] as const;

export function firstSegment(path: string): string {
  return `/${path.replace(/^\/+/, "").split(/[/?#]/)[0] ?? ""}`;
}

export function needsWelcome(
  path: string,
  onboardedAt: string | null | undefined,
  enabled: boolean,
): boolean {
  if (!enabled || onboardedAt !== null) return false;
  return !(FIRST_RUN_EXEMPT as readonly string[]).includes(firstSegment(path));
}
