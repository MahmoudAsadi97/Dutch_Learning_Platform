import assert from "node:assert/strict";
import { test } from "node:test";
import { clamp, dashOffset, fraction, percent, ringPoints } from "../../lib/design/progress.ts";

test("a value above its maximum never exceeds 100 percent", () => {
  assert.equal(percent(30, 20), 100);
  assert.equal(fraction(30, 20), 1);
  assert.equal(dashOffset(30, 20), 0);
});

test("zero and negative maxima show nothing filled", () => {
  assert.equal(percent(5, 0), 0);
  assert.equal(percent(5, -1), 0);
  assert.equal(dashOffset(5, 0), 100);
});

test("the dash offset hides the unfilled share from the top", () => {
  assert.equal(dashOffset(0, 20), 100);
  assert.equal(dashOffset(5, 20), 75);
  assert.equal(dashOffset(20, 20), 0);
});

test("clamp keeps NaN and out-of-range values inside the bounds", () => {
  assert.equal(clamp(Number.NaN), 0);
  assert.equal(clamp(-2), 0);
  assert.equal(clamp(2), 1);
  assert.equal(clamp(7, 0, 10), 7);
});

test("ring points start at the top and go around once", () => {
  const points = ringPoints(4, 10);
  assert.deepEqual(points[0], { x: 0, y: -10 });
  assert.deepEqual(points[1], { x: 10, y: 0 });
  assert.equal(points.length, 4);
  assert.deepEqual(ringPoints(0, 10), []);
});
