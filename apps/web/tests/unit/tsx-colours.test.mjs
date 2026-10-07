import assert from "node:assert/strict";
import { readdirSync, readFileSync } from "node:fs";
import path from "node:path";
import { test } from "node:test";

/** Components never carry a colour of their own: inline styles and SVG fills go through tokens. */
const web = path.resolve(import.meta.dirname, "..", "..");
const LITERAL = /#[0-9a-fA-F]{3,8}\b|\brgba?\(|\bhsla?\(/;

function walk(dir, out = []) {
  for (const entry of readdirSync(dir, { withFileTypes: true })) {
    const full = path.join(dir, entry.name);
    if (entry.isDirectory()) {
      if (!["node_modules", ".next", "tests", "styles"].includes(entry.name)) walk(full, out);
    } else if (/\.tsx?$/.test(entry.name)) out.push(full);
  }
  return out;
}

test("no component, page or client module holds a colour literal", () => {
  const offenders = [];
  const roots = ["components", "app", "lib"].map((dir) => path.join(web, dir));
  for (const file of roots.flatMap((root) => walk(root))) {
    readFileSync(file, "utf8")
      .split("\n")
      .forEach((line, index) => {
        if (LITERAL.test(line)) offenders.push(`${path.relative(web, file)}:${index + 1}`);
      });
  }
  assert.deepEqual(offenders, [], "colour literals belong in app/styles/tokens.css");
});
