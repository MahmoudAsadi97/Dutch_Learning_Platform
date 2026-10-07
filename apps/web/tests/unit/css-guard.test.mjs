import assert from "node:assert/strict";
import { readdirSync, readFileSync } from "node:fs";
import path from "node:path";
import { test } from "node:test";

/**
 * A ratchet over every global stylesheet: the number of colour literals, font sizes under 12 px, outline
 * rules and !important declarations per file may only go down. The budgets in css-budget.json equal the
 * counts measured when the guard was introduced; lower them in the same change that removes the rules.
 * A stylesheet without a budget entry is held to zero on every metric, so new styles are token-driven.
 * app/styles/tokens.css is the one place colour literals belong and is exempt from the hex metric only.
 */

const web = path.resolve(import.meta.dirname, "..", "..");
const budgets = JSON.parse(readFileSync(path.join(import.meta.dirname, "css-budget.json"), "utf8"));

const NAMED =
  "white|black|red|green|blue|yellow|orange|purple|pink|gray|grey|silver|navy|teal|maroon|olive|lime|aqua|fuchsia";

export const METRICS = {
  /** Colour literals in every form: hex, rgb()/hsl(), and the CSS keyword colours. */
  hex: (css) =>
    (
      css.match(
        new RegExp(`#[0-9a-fA-F]{3,8}\\b|\\b(?:rgba?|hsla?)\\(|(?<=[:\\s,(])(?:${NAMED})(?![-\\w])`, "g"),
      ) ?? []
    ).length,
  /** Sizes under the 12px floor, whether written in px, rem or em. */
  smallFont: (css) =>
    (
      css.match(
        /font-size:\s*(?:(?:[0-9]|1[01])(?:\.[0-9]+)?px|0?\.(?:[0-6][0-9]*|7(?:[0-4][0-9]*)?)r?em)(?![\w.])/g,
      ) ?? []
    ).length,
  outline: (css) => (css.match(/(?:^|[^-\w])outline(?:-style|-width|-color)?\s*:/g) ?? []).length,
  important: (css) => (css.match(/!important/g) ?? []).length,
};

const TOKEN_SOURCE = "styles/tokens.css";

export function measure(css) {
  return Object.fromEntries(Object.entries(METRICS).map(([name, count]) => [name, count(css)]));
}

function stylesheets(dir) {
  const out = [];
  for (const entry of readdirSync(path.join(web, "app", dir), { withFileTypes: true })) {
    const rel = dir ? `${dir}/${entry.name}` : entry.name;
    if (entry.isDirectory() && (rel === "styles" || rel.startsWith("styles/"))) out.push(...stylesheets(rel));
    else if (entry.isFile() && entry.name.endsWith(".css")) out.push(rel);
  }
  return out;
}

const files = stylesheets("");

test("every stylesheet stays within its budget", () => {
  for (const file of files) {
    const actual = measure(readFileSync(path.join(web, "app", file), "utf8"));
    const budget = budgets[file] ?? { hex: 0, smallFont: 0, outline: 0, important: 0 };
    for (const metric of Object.keys(METRICS)) {
      if (file === TOKEN_SOURCE && metric === "hex") continue;
      assert.ok(
        actual[metric] <= budget[metric],
        `${file}: ${metric} is ${actual[metric]}, budget ${budget[metric]} (lower the budget in css-budget.json when you remove rules; never raise it)`,
      );
    }
  }
});

test("colour literals outside the token source only shrink", () => {
  const outside = files.filter((file) => file !== TOKEN_SOURCE);
  const literals = outside.map((file) => METRICS.hex(readFileSync(path.join(web, "app", file), "utf8")));
  const budgeted = outside.map((file) => budgets[file]?.hex ?? 0);
  assert.ok(
    literals.reduce((a, b) => a + b, 0) <= budgeted.reduce((a, b) => a + b, 0),
    "colour literals belong in app/styles/tokens.css",
  );
});

test("budgets do not list stylesheets that no longer exist", () => {
  for (const file of Object.keys(budgets)) {
    assert.ok(files.includes(file), `${file} is budgeted but missing from app/`);
  }
});
