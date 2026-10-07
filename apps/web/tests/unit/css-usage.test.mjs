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

/** Class families built from template strings; a member passes only when its prefix is built somewhere. */
const DYNAMIC = [/^tone-\d+$/, /^grade-/, /^status-/, /^kind-/, /^cover-/];

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

/** Every stylesheet under app/, including the layered ones in app/styles. */
export function stylesheetFiles() {
  const files = [];
  const visit = (dir) => {
    for (const entry of readdirSync(dir, { withFileTypes: true })) {
      const full = path.join(dir, entry.name);
      if (entry.isDirectory()) {
        if (entry.name === "styles" || dir.includes(`${path.sep}styles`)) visit(full);
      } else if (entry.name.endsWith(".css")) files.push(full);
    }
  };
  visit(path.join(web, "app"));
  return files;
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
      const prefix = name.match(/^([a-z]+-)/)?.[1] ?? "";
      if (DYNAMIC.some((pattern) => pattern.test(name)) && sources.includes(`${prefix}$\{`)) continue;
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
    .map((file) =>
      readFileSync(file, "utf8")
        .replace(/\/\*[\s\S]*?\*\//g, "")
        .replace(/^\s*\/\/.*$/gm, ""),
    )
    .join("\n");
  const stylesheets = Object.fromEntries(
    stylesheetFiles().map((file) => [path.relative(path.join(web, "app"), file), readFileSync(file, "utf8")]),
  );
  const dead = unreferenced(stylesheets, sources);
  assert.deepEqual(dead, {}, "unreferenced class selectors (delete the rules or add a DYNAMIC pattern)");
});

test("the scan sees template-string families as live", () => {
  const dead = unreferenced(
    { "x.css": ".tone-3 {} .grade-again {} .brand-new {}" },
    'className="brand" tone-${n} grade-${g}',
  );
  assert.deepEqual(dead, { "x.css": ["brand-new"] });
});

/** The primitives app/styles/ui owns; a legacy stylesheet may add contextual rules, never a bare one. */
const PRIMITIVES = [
  "button",
  "card",
  "label",
  "error",
  "notice",
  "icon-tile",
  "field-control",
  "skeleton",
  "empty-state",
  "information-callout",
  "practice-correct",
  "practice-hint",
  "practice-feedback",
  "path-loading",
];

function insideMedia(css, index) {
  const start = css.lastIndexOf("@media", index);
  if (start < 0) return false;
  const segment = css.slice(start, index);
  return (segment.match(/\{/g) ?? []).length > (segment.match(/\}/g) ?? []).length;
}

/** Classes a stylesheet styles on their own (`.button {}`), outside @media blocks. */
export function bareSelectors(css) {
  const names = new Set();
  const clean = css.replace(/\/\*[\s\S]*?\*\//g, "");
  for (const match of clean.matchAll(/([^{}]+)\{[^{}]*\}/g)) {
    if (insideMedia(clean, match.index)) continue;
    for (const selector of match[1].split(",")) {
      const bare = selector.trim().match(/^\.([\w-]+)$/);
      if (bare) names.add(bare[1]);
    }
  }
  return names;
}

test("each primitive is defined as a bare selector in exactly one stylesheet", () => {
  const files = stylesheetFiles();
  for (const name of PRIMITIVES) {
    const where = files
      .filter((file) => bareSelectors(readFileSync(file, "utf8")).has(name))
      .map((file) => path.relative(path.join(web, "app"), file));
    assert.equal(where.length, 1, `${name} is defined bare in ${where.join(", ") || "no stylesheet"}`);
  }
});
