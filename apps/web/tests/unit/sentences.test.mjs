import assert from "node:assert/strict";
import test from "node:test";
import {dutchSentences} from "../../lib/client/sentences.ts";

test("sentence replay preserves decimal appointment times, prices and the original text", () => {
  const text = "De afspraak is om 14.00 uur. Het kost 12,50 euro. Kom je ook?";
  const parts = dutchSentences(text);
  assert.equal(parts.join(""), text);
  assert.ok(parts.some(part => part.includes("14.00")));
  assert.ok(parts.some(part => part.includes("12,50")));
});
test("sentence replay preserves quotes, Dutch accented words and line breaks", () => {
  for (const text of ["‘Tot morgen!’ zegt Zoë.\nHij lacht.", "Eén woord", ""]) assert.equal(dutchSentences(text).join(""), text);
});
