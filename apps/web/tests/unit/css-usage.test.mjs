import assert from "node:assert/strict";
import { readdirSync, readFileSync } from "node:fs";
import path from "node:path";
import { test } from "node:test";

/**
 * Every class selector in a stylesheet must be referenced by a component, page or client module. Classes
 * built from template strings are allowed through the DYNAMIC patterns; add a pattern when you introduce
 * a new family, never a bare class name.
 */

const web = path.resolve(import.meta.dirname, "..", "..");

const DYNAMIC = [/^tone-\d+$/, /^grade-/, /^status-/, /^kind-/, /^is-/, /^cover-/];

function walk(dir, out = []) {
  for (const entry of readdirSync(dir, { withFileTypes: true })) {
    const full = path.join(dir, entry.name);
    if (entry.isDirectory()) {
      if (["node_modules", ".next", "tests", "__screenshots__"].includes(entry.name)) continue;
      walk(full, out);
    } else if (/\.(tsx?|mjs)$/.test(entry.name)) out.push(full);
  }
  return out;
}

export function classesIn(css) {
  const names = new Set();
  for (const match of css.replace(/\/\*[\s\S]*?\*\//g, "").matchAll(/\.([A-Za-z_][\w-]*)/g)) {
    if (!/^\d/.test(match[1])) names.add(match[1]);
  }
  return names;
}

export function unreferenced(stylesheets, sources) {
  const result = {};
  for (const [file, css] of Object.entries(stylesheets)) {
    const dead = [];
    for (const name of classesIn(css)) {
      if (DYNAMIC.some((pattern) => pattern.test(name))) continue;
      const word = new RegExp(`(?<![\\w-])${name.replace(/-/g, "\\-")}(?![\\w-])`);
      if (!word.test(sources)) dead.push(name);
    }
    if (dead.length) result[file] = dead.sort();
  }
  return result;
}

test("every stylesheet class is referenced by a source file", () => {
  const sources = [
    ...walk(path.join(web, "components")),
    ...walk(path.join(web, "app")),
    ...walk(path.join(web, "lib")),
  ]
    .map((file) => readFileSync(file, "utf8"))
    .join("\n");
  const stylesheets = Object.fromEntries(
    readdirSync(path.join(web, "app"))
      .filter((name) => name.endsWith(".css"))
      .map((name) => [name, readFileSync(path.join(web, "app", name), "utf8")]),
  );
  const dead = unreferenced(stylesheets, sources);
  assert.deepEqual(dead, {}, "unreferenced class selectors (delete the rules or add a DYNAMIC pattern)");
});

test("the scan sees template-string families as live", () => {
  const dead = unreferenced({ "x.css": ".tone-3 {} .grade-again {} .brand-new {}" }, 'className="brand"');
  assert.deepEqual(dead, { "x.css": ["brand-new"] });
});
