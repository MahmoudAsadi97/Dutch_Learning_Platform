import assert from "node:assert/strict";
import { existsSync, readFileSync } from "node:fs";
import path from "node:path";
import { test } from "node:test";
import { hardCodedText, measureAll, web } from "./dutch-text.mjs";

/**
 * A ratchet on interface text written straight into components: per file it may only go down, and a file
 * that is not listed must have none. Text from the catalogue (`UiText`, `lib/copy/*`, `lib/ui-copy.ts`)
 * carries its English and Persian, so moving a string there lowers the count. Lower the budget in
 * dutch-budget.json in the same change; never raise it.
 */
const budget = JSON.parse(readFileSync(path.join(import.meta.dirname, "dutch-budget.json"), "utf8"));

test("hard-coded interface text only shrinks", () => {
  const over = [];
  for (const [file, count] of Object.entries(measureAll())) {
    const allowed = budget[file] ?? 0;
    if (count > allowed) over.push(`${file}: ${count} (budget ${allowed})`);
  }
  assert.deepEqual(over, []);
});

test("the budget lists only files that exist", () => {
  const missing = Object.keys(budget).filter((file) => !existsSync(path.join(web, file)));
  assert.deepEqual(missing, []);
});

test("the count sees JSX text and spoken attributes, not code", () => {
  const sample = `<p className="x">Lees de tekst</p><button aria-label="Sluiten" onClick={() => go(1)}>{label}</button>`;
  assert.deepEqual(hardCodedText(sample), ["Lees de tekst", "Sluiten"]);
});
