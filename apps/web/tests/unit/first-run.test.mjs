import assert from "node:assert/strict";
import { test } from "node:test";
import { firstSegment, gateFor, needsWelcome } from "../../lib/client/first-run.ts";

test("a learner who has not onboarded is sent to the welcome from any learning page", () => {
  for (const path of ["/", "/leerpad", "/learn/a1", "/verhalen/abc", "/spreken", "/woorden?x=1"]) {
    assert.equal(needsWelcome(path, null, true), true, path);
  }
});

test("the welcome, settings, the about page and developer pages stay open", () => {
  for (const path of ["/welkom", "/welkom?stap=uitleg", "/settings", "/over", "/dev/ui"]) {
    assert.equal(needsWelcome(path, null, true), false, path);
  }
});

test("an onboarded learner, an unknown profile or a switched-off gate never redirects", () => {
  assert.equal(needsWelcome("/", "2026-10-09T10:00:00Z", true), false);
  assert.equal(needsWelcome("/", undefined, true), false);
  assert.equal(needsWelcome("/", null, false), false);
});

test("a learning page waits while the profile loads, then opens if it cannot be loaded", () => {
  assert.equal(gateFor("/", undefined, true, true), "wait");
  assert.equal(gateFor("/", undefined, true, false), "open");
  assert.equal(gateFor("/settings", undefined, true, true), "open");
  assert.equal(gateFor("/", undefined, false, true), "open");
  assert.equal(gateFor("/", null, true, false), "welcome");
});

test("the first segment ignores queries, fragments and repeated slashes", () => {
  assert.equal(firstSegment("/"), "/");
  assert.equal(firstSegment("//welkom/x"), "/welkom");
  assert.equal(firstSegment("/settings?tab=1"), "/settings");
  assert.equal(firstSegment("/over#top"), "/over");
});
