import assert from "node:assert/strict";
import { test } from "node:test";
import { RENDERED_KINDS, isChoicePrompt, optionForKey } from "../../components/exercise/registry.ts";
import { percentile, recordRoundTrip, roundTrips } from "../../lib/client/round-trips.ts";

test("the runner asks only for kinds it draws, always with choice", () => {
  assert.ok(RENDERED_KINDS.includes("choice"));
  assert.ok(!RENDERED_KINDS.includes("intro"), "the intro card is not a kind to ask for");
  assert.equal(isChoicePrompt({ kind: "odd_one_out", topic: {}, options: [] }), true);
  assert.equal(isChoicePrompt({ kind: "dictation", word_count: 3 }), false);
});

test("the number keys pick the options in order, and nothing else does", () => {
  const ids = ["qwer", "asdf", "zxcv", "tyui"];
  assert.equal(optionForKey("1", ids), "qwer");
  assert.equal(optionForKey("4", ids), "tyui");
  assert.equal(optionForKey("5", ids), null);
  assert.equal(optionForKey("0", ids), null);
  assert.equal(optionForKey("a", ids), null);
  assert.equal(optionForKey("Enter", ids), null);
});

test("the p95 of the answer round trips is a nearest-rank percentile", () => {
  assert.equal(percentile([], 0.95), null);
  const values = Array.from({ length: 20 }, (_, n) => (n + 1) * 10);
  assert.equal(percentile(values, 0.95), 190);
  assert.equal(percentile(values, 0.5), 100);
  assert.equal(percentile([42], 0.95), 42);
  recordRoundTrip(120);
  recordRoundTrip(80);
  assert.deepEqual(roundTrips().slice(-2), [120, 80]);
});
