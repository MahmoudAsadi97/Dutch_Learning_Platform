/**
 * Answer round trips as the browser sees them (send to verdict), for the step 3.6 target of a p95 at or under
 * 300 ms. Each one is also a `performance.measure` named "exercise-answer", so DevTools' Performance panel
 * shows them on any environment, Azure included. Pure apart from `performance`, so node:test loads it.
 */
const KEPT = 200;
const durations: number[] = [];

export function recordRoundTrip(milliseconds: number, start?: number): void {
  durations.push(milliseconds);
  if (durations.length > KEPT) durations.shift();
  try {
    if (start !== undefined && typeof performance !== "undefined" && performance.measure)
      performance.measure("exercise-answer", { start, duration: milliseconds });
  } catch {
    // an old browser without measure options: the number is still kept
  }
}

export function roundTrips(): readonly number[] {
  return durations;
}

/** The value below which `share` (0 to 1) of the values fall: nearest rank, as load tests report it. */
export function percentile(values: readonly number[], share: number): number | null {
  if (!values.length) return null;
  const sorted = [...values].sort((a, b) => a - b);
  const rank = Math.min(sorted.length, Math.max(1, Math.ceil(share * sorted.length)));
  return sorted[rank - 1];
}
