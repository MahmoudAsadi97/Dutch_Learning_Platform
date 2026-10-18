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

// A retained source batch keeps its whole translation contract. New bilingual batches
// need no invented Persian text, but removing one legacy translation must still fail.
const persianBatches = new Set([
  ...Object.keys(uiCopy),
  ...Object.entries(batches)
    .filter(([, copies]) => Object.values(copies).some((copy) => Object.hasOwn(copy, "fa")))
    .map(([name]) => name),
]);

const entries = [
  ...allCopy(),
  ...Object.entries(batches).flatMap(([group, copies]) =>
    Object.entries(copies).map(([name, copy]) => ({ key: `${group}.${name}`, copy })),
  ),
];

test("every batch module exports its copy under <name>Copy", () => {
  for (const [name, copies] of Object.entries(batches)) assert.equal(typeof copies, "object", name);
});

test("every source batch with Persian has a review flag and no flag names an absent batch", () => {
  const names = [...persianBatches].sort();
  assert.deepEqual(Object.keys(PERSIAN_REVIEWED).sort(), names);
});

test("every key has Dutch and English; existing Persian source entries remain complete", () => {
  assert.ok(entries.length >= 20);
  for (const { key, copy } of entries) {
    const languages = persianBatches.has(key.split(".")[0]) ? ["nl", "en", "fa"] : ["nl", "en"];
    for (const language of languages) {
      assert.ok(copy[language]?.trim(), `${key}.${language} is empty`);
    }
    assert.deepEqual(Object.keys(copy).sort(), [...languages].sort(), `${key} has an unsupported copy field`);
  }
});

test("placeholders match in every language present in each entry", () => {
  const names = (text) => [...text.matchAll(/\{(\w+)\}/g)].map((m) => m[1]).sort();
  for (const { key, copy } of entries) {
    assert.deepEqual(names(copy.en), names(copy.nl), `${key}: en placeholders`);
    if (Object.hasOwn(copy, "fa"))
      assert.deepEqual(names(copy.fa), names(copy.nl), `${key}: fa placeholders`);
  }
});

test("interface Dutch speaks to the learner as je, never u", () => {
  for (const { key, copy } of entries) {
    assert.doesNotMatch(copy.nl, /\b(u|uw|uzelf)\b/i, `${key}.nl uses the formal form`);
  }
});

test("retained Persian source copy is written in the Arabic script", () => {
  for (const { key, copy } of entries) {
    if (Object.hasOwn(copy, "fa")) assert.match(copy.fa, /[؀-ۿ]/, `${key}.fa`);
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
