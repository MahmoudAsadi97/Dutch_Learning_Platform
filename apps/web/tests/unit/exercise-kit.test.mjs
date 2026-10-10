import assert from "node:assert/strict";
import { test } from "node:test";
import {
  RENDERED_KINDS,
  hasSound,
  isChoicePrompt,
  optionForKey,
} from "../../components/exercise/registry.ts";
import { percentile, recordRoundTrip, roundTrips } from "../../lib/client/round-trips.ts";

test("the runner asks only for kinds it draws, always with choice", () => {
  assert.ok(RENDERED_KINDS.includes("choice"));
  assert.ok(!RENDERED_KINDS.includes("intro"), "the intro card is not a kind to ask for");
  assert.equal(isChoicePrompt({ kind: "odd_one_out", topic: {}, options: [] }), true);
  assert.equal(isChoicePrompt({ kind: "dictation", word_count: 3 }), false);
});

test("the number keys pick the options in order on any layout, and nothing else does", () => {
  const ids = ["qwer", "asdf", "zxcv", "tyui"];
  assert.equal(optionForKey("1", "Digit1", ids), "qwer");
  assert.equal(optionForKey("4", "Numpad4", ids), "tyui");
  assert.equal(optionForKey("5", "Digit5", ids), null);
  assert.equal(optionForKey("0", "Digit0", ids), null);
  assert.equal(optionForKey("a", "KeyA", ids), null);
  assert.equal(optionForKey("Enter", "Enter", ids), null);
  // Belgian AZERTY types "é" on the 2 key without Shift; a Persian keyboard types Persian digits
  assert.equal(optionForKey("é", "Digit2", ids), "asdf");
  assert.equal(optionForKey("۳", "Digit3", ids), "zxcv");
  assert.equal(optionForKey("٢", "Digit2", ids), "asdf");
  // the number pad with NumLock off moves the caret: not an option
  assert.equal(optionForKey("End", "Numpad1", ids), null);
});

test("only kinds with a sound can be reported for their sound", () => {
  assert.equal(hasSound("listen_choose"), true);
  assert.equal(hasSound("choice"), false);
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
