/**
 * Pure arithmetic behind the progress visuals. A ring or bar never shows more than its maximum and never
 * invents a value: callers pass what the API recorded, these helpers only shape it for the SVG.
 */

export function clamp(value: number, min = 0, max = 1): number {
  if (Number.isNaN(value)) return min;
  return Math.min(max, Math.max(min, value));
}

/** The share of `max` that `value` fills, as 0..1; a zero or negative maximum means nothing to fill. */
export function fraction(value: number, max: number): number {
  if (!(max > 0)) return 0;
  return clamp(value / max);
}

/** Whole-number percentage for labels and aria-valuenow. */
export function percent(value: number, max: number): number {
  return Math.round(fraction(value, max) * 100);
}

/**
 * Dash offset for a stroke drawn with `pathLength="100"`: 100 hides the whole ring, 0 shows it all. The
 * ring is drawn from the top, clockwise, so a quarter filled reads as "a quarter of the day".
 */
export function dashOffset(value: number, max: number): number {
  return Math.round((1 - fraction(value, max)) * 100 * 100) / 100;
}

/** Positions of `count` dots around a circle of radius `r`, starting at the top. */
export function ringPoints(count: number, r: number, cx = 0, cy = 0): { x: number; y: number }[] {
  if (count <= 0) return [];
  return Array.from({ length: count }, (_, index) => {
    const angle = (index / count) * Math.PI * 2 - Math.PI / 2;
    return {
      x: Math.round((cx + Math.cos(angle) * r) * 100) / 100,
      y: Math.round((cy + Math.sin(angle) * r) * 100) / 100,
    };
  });
}
