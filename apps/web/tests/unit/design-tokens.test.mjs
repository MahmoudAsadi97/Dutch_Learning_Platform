import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import path from "node:path";
import { test } from "node:test";

/**
 * Every colour pairing the system promises is checked against WCAG AA: 4.5:1 for text, 3:1 for the
 * borders of controls (--border-strong, --border-on-inverse), focus rings and solid controls. Decorative
 * borders (--border, --accent-border) make no contrast promise. The check runs over :root and over every
 * [data-accent] block (one light scheme today), and no accent may borrow a feedback ramp.
 */

const tokensPath = path.resolve(import.meta.dirname, "..", "..", "app", "styles", "tokens.css");

export function parseBlocks(css) {
  const blocks = {};
  const pattern = /(:root|\[data-accent="[^"]+"\](?:,\s*\[data-accent="[^"]+"\])*)\s*\{([^}]*)\}/g;
  for (const match of css.replace(/\/\*[\s\S]*?\*\//g, "").matchAll(pattern)) {
    const selectors = match[1].split(",").map((s) => s.trim());
    const declarations = {};
    for (const line of match[2].split(";")) {
      const [name, ...rest] = line.split(":");
      if (name && name.trim().startsWith("--")) declarations[name.trim()] = rest.join(":").trim();
    }
    for (const selector of selectors) blocks[selector] = { ...(blocks[selector] ?? {}), ...declarations };
  }
  return blocks;
}

export function resolve(name, scope, root, depth = 0) {
  const value = scope[name] ?? root[name];
  if (value === undefined || depth > 10) return undefined;
  const reference = value.match(/^var\((--[\w-]+)\)$/);
  return reference ? resolve(reference[1], scope, root, depth + 1) : value;
}

function channel(value) {
  const c = value / 255;
  return c <= 0.03928 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4;
}

export function luminance(hex) {
  const normalized = hex.length === 4 ? hex.replace(/[0-9a-f]/gi, (h) => h + h) : hex;
  const [r, g, b] = [1, 3, 5].map((i) => channel(parseInt(normalized.slice(i, i + 2), 16)));
  return 0.2126 * r + 0.7152 * g + 0.0722 * b;
}

export function contrast(a, b) {
  const [light, dark] = [luminance(a), luminance(b)].sort((x, y) => y - x);
  return (light + 0.05) / (dark + 0.05);
}

const TEXT_PAIRS = [
  ["--text", "--surface-canvas"],
  ["--text", "--surface-raised"],
  ["--text", "--surface-sunken"],
  ["--text-muted", "--surface-canvas"],
  ["--text-muted", "--surface-raised"],
  ["--text-muted", "--surface-sunken"],
  ["--text-subtle", "--surface-raised"],
  ["--text-subtle", "--surface-canvas"],
  ["--text-link", "--surface-raised"],
  ["--text-on-inverse", "--surface-inverse"],
  ["--text-muted-on-inverse", "--surface-inverse"],
  ["--text-on-solid", "--action-solid"],
  ["--text-on-solid", "--action-solid-hover"],
  ["--action-ink", "--action-subtle"],
  ["--success-ink", "--success-bg"],
  ["--warning-ink", "--warning-bg"],
  ["--danger-ink", "--danger-bg"],
  ["--info-ink", "--info-bg"],
  ["--recording-ink", "--recording-bg"],
  ["--text-on-solid", "--success-solid"],
  ["--text-on-solid", "--warning-solid"],
  ["--text-on-solid", "--danger-solid"],
  ["--text-on-solid", "--info-solid"],
  ["--text-on-solid", "--cover-1-b"],
  ["--text-on-solid", "--cover-2-b"],
  ["--text-on-solid", "--cover-3-b"],
  ["--text-on-solid", "--cover-4-b"],
  ["--text-on-solid", "--cover-5-b"],
  ["--text-on-solid", "--cover-6-b"],
];
const GRAPHIC_PAIRS = [
  ["--border-strong", "--surface-raised"],
  ["--border-strong", "--surface-canvas"],
  ["--border-on-inverse", "--surface-inverse"],
  ["--focus-ring-on-inverse", "--surface-inverse"],
  ["--focus-ring-on-inverse", "--surface-media"],
  ["--focus-ring", "--surface-raised"],
  ["--focus-ring", "--surface-canvas"],
  ["--action-solid", "--surface-raised"],
  ["--success-vivid", "--surface-raised"],
  ["--warning-vivid", "--surface-raised"],
  ["--danger-vivid", "--surface-raised"],
  ["--recording-pulse", "--surface-raised"],
  ["--streak-solid", "--streak-track"],
  ["--streak-solid", "--surface-raised"],
  ["--success-solid", "--surface-raised"],
  ["--text-on-inverse", "--border-on-inverse"],
];
const ACCENT_TEXT_PAIRS = [
  ["--accent-ink", "--accent-subtle"],
  ["--accent-ink", "--surface-raised"],
  ["--accent-ink-strong", "--accent-muted"],
  ["--text-on-solid", "--accent-solid"],
  ["--text-on-solid", "--accent-solid-hover"],
];
const ACCENT_GRAPHIC_PAIRS = [
  ["--accent-solid", "--surface-raised"],
  ["--border-strong", "--accent-subtle"],
  ["--accent-vivid", "--surface-raised"],
];

const blocks = parseBlocks(readFileSync(tokensPath, "utf8"));
const root = blocks[":root"];

function check(pairs, scope, minimum, label) {
  for (const [fg, bg] of pairs) {
    const front = resolve(fg, scope, root);
    const back = resolve(bg, scope, root);
    assert.match(front ?? "", /^#[0-9a-f]{3,6}$/i, `${label}: ${fg} must resolve to a hex colour`);
    assert.match(back ?? "", /^#[0-9a-f]{3,6}$/i, `${label}: ${bg} must resolve to a hex colour`);
    const ratio = contrast(front, back);
    assert.ok(ratio >= minimum, `${label}: ${fg} on ${bg} is ${ratio.toFixed(2)}:1, needs ${minimum}:1`);
  }
}

test("root text pairs reach 4.5:1 and graphic pairs 3:1", () => {
  assert.ok(root, "tokens.css must declare :root");
  check(TEXT_PAIRS, root, 4.5, ":root");
  check(GRAPHIC_PAIRS, root, 3, ":root");
});

test("every accent block keeps its ink readable and its solid visible", () => {
  const accents = Object.keys(blocks).filter((selector) => selector.startsWith("[data-accent"));
  assert.ok(accents.length >= 8, "expected the section and skill accents");
  for (const selector of accents) {
    check(ACCENT_TEXT_PAIRS, blocks[selector], 4.5, selector);
    check(ACCENT_GRAPHIC_PAIRS, blocks[selector], 3, selector);
  }
});

test("the contrast formula matches the WCAG reference values", () => {
  assert.equal(contrast("#000000", "#ffffff"), 21);
  assert.ok(Math.abs(contrast("#777777", "#ffffff") - 4.48) < 0.01);
});

test("no accent borrows a feedback ramp", () => {
  const feedback = new Set(
    Object.entries(root)
      .filter(([name]) => /^--(green|amber|red|orange)-\d+$/.test(name))
      .map(([, value]) => value.toLowerCase()),
  );
  for (const selector of Object.keys(blocks).filter((s) => s.startsWith("[data-accent"))) {
    for (const name of Object.keys(blocks[selector])) {
      const value = resolve(name, blocks[selector], root)?.toLowerCase();
      assert.ok(!feedback.has(value), `${selector} ${name} resolves to a feedback colour ${value}`);
    }
  }
});

test("each block declares a token once and every contrast pair is listed once", () => {
  const css = readFileSync(tokensPath, "utf8").replace(/\/\*[\s\S]*?\*\//g, "");
  for (const match of css.matchAll(/([^{}]+)\{([^{}]*)\}/g)) {
    const names = [...match[2].matchAll(/(--[\w-]+)\s*:/g)].map((m) => m[1]);
    const repeated = names.filter((name, index) => names.indexOf(name) !== index);
    assert.deepEqual(repeated, [], `${match[1].trim()} declares ${repeated.join(", ")} more than once`);
  }
  for (const [label, pairs] of Object.entries({
    TEXT_PAIRS,
    GRAPHIC_PAIRS,
    ACCENT_TEXT_PAIRS,
    ACCENT_GRAPHIC_PAIRS,
  })) {
    const keys = pairs.map((pair) => pair.join(" on "));
    const repeated = keys.filter((key, index) => keys.indexOf(key) !== index);
    assert.deepEqual(repeated, [], `${label} lists ${repeated.join(", ")} twice`);
  }
});
