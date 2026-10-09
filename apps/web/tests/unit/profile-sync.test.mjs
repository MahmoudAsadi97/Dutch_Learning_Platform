import assert from "node:assert/strict";
import { test } from "node:test";
import { isSupportMode, reconcileMode } from "../../lib/client/profile-sync.ts";

test("a server without a value adopts the device's choice and uploads it once", () => {
  assert.deepEqual(reconcileMode("nl-fa", null), { mode: "nl-fa", upload: true });
  assert.deepEqual(reconcileMode("nl-fa-en", undefined), { mode: "nl-fa-en", upload: true });
});

test("a server value wins over the device", () => {
  assert.deepEqual(reconcileMode("nl-fa", "nl-en"), { mode: "nl-en", upload: false });
  assert.deepEqual(reconcileMode(null, "nl-fa-en"), { mode: "nl-fa-en", upload: false });
});

test("invalid values fall back to Dutch with English", () => {
  assert.deepEqual(reconcileMode("de", "xx"), { mode: "nl-en", upload: false });
  assert.deepEqual(reconcileMode(null, null), { mode: "nl-en", upload: false });
  assert.equal(isSupportMode("nl-fa"), true);
  assert.equal(isSupportMode("fa"), false);
});
