import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import path from "node:path";
import { test } from "node:test";
import { animFor, withViewTransition } from "../../lib/client/motion.ts";

const motionCss = readFileSync(
  path.resolve(import.meta.dirname, "..", "..", "app", "styles", "motion.css"),
  "utf8",
);

test("answer states map to one animation each and to none under reduced motion", () => {
  assert.equal(animFor("correct", false), "pop");
  assert.equal(animFor("incorrect", false), "shake");
  assert.equal(animFor("almost", false), "rise");
  assert.equal(animFor("celebrate", false), "burst");
  assert.equal(animFor("none", false), undefined);
  for (const state of ["correct", "incorrect", "almost", "reveal", "celebrate", "enter"]) {
    assert.equal(animFor(state, true), undefined, state);
  }
});

test("withViewTransition runs the update directly without a document", () => {
  let ran = 0;
  withViewTransition(() => {
    ran += 1;
  });
  assert.equal(ran, 1);
});

test("every named animation has a reduced-motion fallback", () => {
  const names = [...motionCss.matchAll(/\[data-anim="([a-z]+)"\]\s*\{/g)].map((m) => m[1]);
  const fallback = motionCss.slice(motionCss.indexOf("@media (prefers-reduced-motion: reduce)"));
  assert.ok(names.length >= 7, "expected the animation set");
  assert.match(fallback, /\[data-anim\]\s*\{\s*animation:\s*none;/);
  for (const name of ["pulse", "shimmer", "dots"]) {
    assert.ok(fallback.includes(`[data-anim="${name}"]`), `${name} needs an explicit static state`);
  }
});

test("the shake stays within 4px", () => {
  const shake = motionCss.slice(
    motionCss.indexOf("@keyframes ts-shake"),
    motionCss.indexOf("@keyframes ts-pulse"),
  );
  for (const px of shake.matchAll(/translateX\((-?\d+)px\)/g)) {
    assert.ok(Math.abs(Number(px[1])) <= 4, `shake moved ${px[1]}px`);
  }
});
