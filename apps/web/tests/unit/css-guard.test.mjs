import assert from "node:assert/strict";
import { readdirSync, readFileSync } from "node:fs";
import path from "node:path";
import { test } from "node:test";

/**
 * A ratchet over the legacy stylesheets in app/*.css: the number of colour literals, font sizes under
 * 12 px, outline rules and !important declarations per file may only go down. The budgets in
 * css-budget.json equal the counts measured when the guard was introduced; lower them in the same change
 * that removes the rules. A stylesheet without a budget entry is held to zero on every metric, so new
 * styles go into app/styles (token-driven) rather than into a new legacy file.
 */

const web = path.resolve(import.meta.dirname, "..", "..");
const budgets = JSON.parse(readFileSync(path.join(import.meta.dirname, "css-budget.json"), "utf8"));

export const METRICS = {
  hex: (css) => (css.match(/#[0-9a-fA-F]{3,8}\b/g) ?? []).length,
  smallFont: (css) => (css.match(/font-size:\s*(?:[0-9]|1[01])(?:\.[0-9]+)?px/g) ?? []).length,
  outline: (css) => (css.match(/(?:^|[^-])outline\s*:/g) ?? []).length,
  important: (css) => (css.match(/!important/g) ?? []).length,
};

export function measure(css) {
  return Object.fromEntries(Object.entries(METRICS).map(([name, count]) => [name, count(css)]));
}

const files = readdirSync(path.join(web, "app")).filter((name) => name.endsWith(".css"));

test("every legacy stylesheet stays within its budget", () => {
  for (const file of files) {
    const actual = measure(readFileSync(path.join(web, "app", file), "utf8"));
    const budget = budgets[file] ?? { hex: 0, smallFont: 0, outline: 0, important: 0 };
    for (const metric of Object.keys(METRICS)) {
      assert.ok(
        actual[metric] <= budget[metric],
        `${file}: ${metric} is ${actual[metric]}, budget ${budget[metric]} (lower the budget in css-budget.json when you remove rules; never raise it)`,
      );
    }
  }
});

test("budgets do not list stylesheets that no longer exist", () => {
  for (const file of Object.keys(budgets)) {
    assert.ok(files.includes(file), `${file} is budgeted but missing from app/`);
  }
});
