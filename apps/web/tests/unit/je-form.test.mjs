import assert from "node:assert/strict";
import { readdirSync, readFileSync } from "node:fs";
import path from "node:path";
import { test } from "node:test";

/**
 * Interface Dutch speaks to the learner as "je". Practice content keeps its own register (a learner says
 * "Kunt u dat herhalen?" to a stranger), so files that hold practice phrases are named here, with a reason.
 */
const PRACTICE_CONTENT = {
  "components/CommunicationCoach.tsx": "phrases the learner practises saying to other people",
};

const web = path.resolve(import.meta.dirname, "..", "..");
const formal = /(?<![\w-])(u|uw|uzelf)(?![\w-])/i;

function sources(dir, out = []) {
  for (const entry of readdirSync(path.join(web, dir), { withFileTypes: true })) {
    const rel = `${dir}/${entry.name}`;
    if (entry.isDirectory()) sources(rel, out);
    else if (/\.(tsx|ts)$/.test(entry.name)) out.push(rel);
  }
  return out;
}

/** The text a learner can read: string literals, template literals and JSX text, without comments. */
function readableText(code) {
  const withoutComments = code.replace(/\/\*[\s\S]*?\*\//g, "").replace(/(^|[^:"'`])\/\/.*$/gm, "$1");
  const strings = [...withoutComments.matchAll(/"([^"\n]*)"|`([^`]*)`/g)].map((m) => m[1] ?? m[2]);
  const jsxText = [...withoutComments.matchAll(/>([^<>{}]+)</g)].map((m) => m[1]);
  return [...strings, ...jsxText].filter((text) => /[a-zà-ÿ]{2,} /i.test(text));
}

test("interface Dutch uses je, never u or uw", () => {
  const offenders = [];
  for (const file of [...sources("components"), ...sources("app"), ...sources("lib")]) {
    if (file in PRACTICE_CONTENT) continue;
    for (const text of readableText(readFileSync(path.join(web, file), "utf8"))) {
      if (formal.test(text)) offenders.push(`${file}: ${text.trim().slice(0, 90)}`);
    }
  }
  assert.deepEqual(offenders, []);
});

test("the practice-content exceptions still exist and still need the exception", () => {
  for (const file of Object.keys(PRACTICE_CONTENT)) {
    const text = readableText(readFileSync(path.join(web, file), "utf8"));
    assert.ok(
      text.some((line) => formal.test(line)),
      `${file} no longer needs to be listed`,
    );
  }
});
