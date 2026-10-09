import assert from "node:assert/strict";
import { test } from "node:test";
import { allCopy, fill } from "../../lib/ui-copy.ts";

const entries = allCopy();

test("every key carries Dutch, English and Persian", () => {
  assert.ok(entries.length >= 20);
  for (const { key, copy } of entries) {
    for (const language of ["nl", "en", "fa"]) {
      assert.ok(copy[language]?.trim(), `${key}.${language} is empty`);
    }
  }
});

test("placeholders match across the three languages", () => {
  const names = (text) => [...text.matchAll(/\{(\w+)\}/g)].map((m) => m[1]).sort();
  for (const { key, copy } of entries) {
    assert.deepEqual(names(copy.en), names(copy.nl), `${key}: en placeholders`);
    assert.deepEqual(names(copy.fa), names(copy.nl), `${key}: fa placeholders`);
  }
});

test("interface Dutch speaks to the learner as je, never u", () => {
  for (const { key, copy } of entries) {
    assert.doesNotMatch(copy.nl, /\b(u|uw|uzelf)\b/i, `${key}.nl uses the formal form`);
  }
});

test("Persian copy is written in the Arabic script", () => {
  for (const { key, copy } of entries) {
    assert.match(copy.fa, /[؀-ۿ]/, `${key}.fa`);
  }
});

test("fill replaces placeholders in every language and leaves unknown ones", () => {
  const filled = fill(
    { nl: "Nog {points} punten", en: "{points} points", fa: "{points} امتیاز {x}" },
    { points: 7 },
  );
  assert.equal(filled.nl, "Nog 7 punten");
  assert.equal(filled.en, "7 points");
  assert.equal(filled.fa, "7 امتیاز {x}");
});
