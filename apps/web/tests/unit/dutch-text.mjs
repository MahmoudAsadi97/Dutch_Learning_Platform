import { readdirSync, readFileSync } from "node:fs";
import path from "node:path";

/**
 * Interface text written straight into components instead of coming from the catalogue: JSX text and the
 * literal values of the attributes a learner reads or hears (aria-label, placeholder, title, alt, label).
 * Shared by the ratchet test and the budget recount, so both count the same way.
 */
export const web = path.resolve(import.meta.dirname, "..", "..");

const ATTRIBUTES = /\b(?:aria-label|placeholder|title|alt|label)="([^"]*)"/g;

/** Text between a JSX tag and the next tag; generics, arrows and statements between two JSX blocks are code. */
const JSX_TEXT = /(?:<[A-Za-z][\w.]*(?:\s[^<>]*?)?>|<\/[\w.]*>|<>)([^<>{}]+)(?=<)/g;
const CODE =
  /\b(?:return|const|let|if|else|null|await|useState|useRef|Promise)\b|=>|&&|\|\||;\s*$|^\s*[)(;]/m;

export function hardCodedText(code) {
  const stripped = code.replace(/\/\*[\s\S]*?\*\//g, "").replace(/(^|[^:"'`])\/\/.*$/gm, "$1");
  const jsx = [...stripped.matchAll(JSX_TEXT)].map((m) => m[1].trim()).filter((text) => !CODE.test(text));
  const attributes = [...stripped.matchAll(ATTRIBUTES)].map((m) => m[1].trim());
  return [...jsx, ...attributes].filter((text) => /\p{L}{2,}/u.test(text));
}

export function sourceFiles(dir = "components", out = []) {
  for (const entry of readdirSync(path.join(web, dir), { withFileTypes: true })) {
    const rel = `${dir}/${entry.name}`;
    if (entry.isDirectory()) sourceFiles(rel, out);
    else if (entry.name.endsWith(".tsx")) out.push(rel);
  }
  return out;
}

export function measureAll() {
  const counts = {};
  for (const file of [...sourceFiles("components"), ...sourceFiles("app")].sort()) {
    const n = hardCodedText(readFileSync(path.join(web, file), "utf8")).length;
    if (n) counts[file] = n;
  }
  return counts;
}
