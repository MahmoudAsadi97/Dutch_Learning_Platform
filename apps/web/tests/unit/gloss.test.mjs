import assert from "node:assert/strict";
import { test } from "node:test";
import { glossLevelFor, glossShown } from "../../lib/client/gloss.ts";
import { STAGE_IDS } from "../../lib/domain/registry.ts";

test("auto shows every gloss up to A2, guides only at pre-B1 and B1, nothing above", () => {
  const expected = {
    "pre-a1": "chrome",
    a1: "chrome",
    "pre-a2": "chrome",
    a2: "chrome",
    "pre-b1": "guide",
    b1: "guide",
    "pre-b2": "none",
    b2: "none",
    "pre-c1": "none",
    c1: "none",
    "pre-c2": "none",
    c2: "none",
  };
  for (const stage of STAGE_IDS) {
    assert.equal(glossLevelFor(stage, "auto"), expected[stage], stage);
    assert.equal(glossLevelFor(stage, "on"), "chrome", `${stage} on`);
    assert.equal(glossLevelFor(stage, "off"), "none", `${stage} off`);
  }
  assert.equal(glossLevelFor(null, "auto"), "chrome");
  assert.equal(glossLevelFor("z9", "auto"), "chrome");
});

test("tiers: chrome needs the chrome level, guides show at chrome or guide, always always", () => {
  assert.equal(glossShown("chrome", "chrome"), true);
  assert.equal(glossShown("chrome", "guide"), false);
  assert.equal(glossShown("chrome", "none"), false);
  assert.equal(glossShown("guide", "guide"), true);
  assert.equal(glossShown("guide", "chrome"), true);
  assert.equal(glossShown("guide", "none"), false);
  assert.equal(glossShown("always", "none"), true);
});

test("the three gloss bands cover exactly the registry's stages", () => {
  const seen = STAGE_IDS.map((stage) => glossLevelFor(stage, "auto"));
  assert.equal(seen.length, 12);
  assert.deepEqual(new Set(seen), new Set(["chrome", "guide", "none"]));
});
