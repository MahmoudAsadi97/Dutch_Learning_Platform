import assert from "node:assert/strict";
import { readdirSync } from "node:fs";
import path from "node:path";
import { test } from "node:test";
import { pathToFileURL } from "node:url";
import { PERSIAN_REVIEWED } from "../../lib/copy/review.ts";
import { allCopy, fill, uiCopy } from "../../lib/ui-copy.ts";

/** The per-screen batches in lib/copy, loaded the way the catalogue's own groups are. */
const copyDir = path.resolve(import.meta.dirname, "..", "..", "lib", "copy");
const batchFiles = readdirSync(copyDir).filter((file) => file.endsWith(".ts") && file !== "review.ts");
const batches = {};
for (const file of batchFiles) {
  const loaded = await import(pathToFileURL(path.join(copyDir, file)).href);
  batches[file.replace(/\.ts$/, "")] = loaded[`${file.replace(/\.ts$/, "")}Copy`];
}

const entries = [
  ...allCopy(),
  ...Object.entries(batches).flatMap(([group, copies]) =>
    Object.entries(copies).map(([name, copy]) => ({ key: `${group}.${name}`, copy })),
  ),
];

test("every batch module exports its copy under <name>Copy", () => {
  for (const [name, copies] of Object.entries(batches)) assert.equal(typeof copies, "object", name);
});

test("every batch has a Persian review flag, and no flag names a batch that does not exist", () => {
  const names = [...Object.keys(uiCopy), ...Object.keys(batches)].sort();
  assert.deepEqual(Object.keys(PERSIAN_REVIEWED).sort(), names);
});

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
