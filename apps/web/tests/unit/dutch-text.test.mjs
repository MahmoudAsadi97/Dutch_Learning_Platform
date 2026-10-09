import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import path from "node:path";
import { test } from "node:test";
import { hardCodedText, measureAll } from "./dutch-text.mjs";

/**
 * A ratchet on interface text written straight into components. The budget is an exact snapshot: a file
 * may not gain hard-coded text, and a change that moves text into the catalogue (`UiText`, `lib/copy/*`,
 * `lib/ui-copy.ts`) lowers its number in dutch-budget.json in the same change, or the test says by how much.
 */
const budget = JSON.parse(readFileSync(path.join(import.meta.dirname, "dutch-budget.json"), "utf8"));

test("hard-coded interface text matches the budget exactly", () => {
  const counts = measureAll();
  const files = new Set([...Object.keys(counts), ...Object.keys(budget)]);
  const wrong = [];
  for (const file of [...files].sort()) {
    const count = counts[file] ?? 0;
    const allowed = budget[file] ?? 0;
    if (count > allowed) wrong.push(`${file}: ${count} (budget ${allowed}); use the catalogue`);
    else if (count < allowed)
      wrong.push(count ? `${file}: lower the budget to ${count}` : `${file}: remove it from the budget`);
  }
  assert.deepEqual(wrong, []);
});

test("the count sees JSX text and spoken attributes, not code", () => {
  const sample = `<p className="x">Lees de tekst</p><button aria-label="Sluiten" onClick={() => go(1)}>{label}</button>`;
  assert.deepEqual(hardCodedText(sample), ["Lees de tekst", "Sluiten"]);
});

test("the count sees text next to handlers, expressions and conditions", () => {
  assert.deepEqual(hardCodedText(`<button onClick={() => go(1)}>Toon de tekst</button>`), ["Toon de tekst"]);
  assert.deepEqual(hardCodedText(`<p>Start een sessie om met {name} te bellen.</p>`), [
    "Start een sessie om met",
    "te bellen.",
  ]);
  assert.deepEqual(hardCodedText(`<p>{busy ? "Bezig…" : "Start"}</p>`), ["Bezig…", "Start"]);
  assert.deepEqual(hardCodedText(`<EmptyState description="Nog geen woorden" />`), ["Nog geen woorden"]);
  assert.deepEqual(hardCodedText(`<p aria-label={"Sluit het venster"} />`), ["Sluit het venster"]);
  assert.deepEqual(hardCodedText(`const label = { nl: "Hulp", en: "Help", fa: "کمک" };`), ["Hulp"]);
});

test("strings that are not shown as text do not count", () => {
  assert.deepEqual(
    hardCodedText(`<p className="error muted" data-testid="score">{fill(copy, { n: "twee" })}</p>`),
    [],
  );
  assert.deepEqual(hardCodedText(`const kind = status === "ready" ? "klaar" : "wacht";`), []);
});
