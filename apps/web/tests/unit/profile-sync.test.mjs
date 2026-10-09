import assert from "node:assert/strict";
import { test } from "node:test";
import { isSupportMode, reconcileMode } from "../../lib/client/profile-sync.ts";

const chosen = (stored) => ({ stored, pending: false });
const unsent = (stored) => ({ stored, pending: true });

test("a server without a value adopts a choice made on this device", () => {
  assert.deepEqual(reconcileMode(chosen("nl-fa"), null), { mode: "nl-fa", upload: true });
  assert.deepEqual(reconcileMode(chosen("nl-fa-en"), undefined), { mode: "nl-fa-en", upload: true });
});

test("a default is not a choice: with nothing chosen anywhere nothing is sent", () => {
  assert.deepEqual(reconcileMode(chosen(null), null), { mode: "nl-en", upload: false });
  assert.deepEqual(reconcileMode(chosen("de"), null), { mode: "nl-en", upload: false });
});

test("a server value wins over an older device value", () => {
  assert.deepEqual(reconcileMode(chosen("nl-fa"), "nl-en"), { mode: "nl-en", upload: false });
  assert.deepEqual(reconcileMode(chosen(null), "nl-fa-en"), { mode: "nl-fa-en", upload: false });
});

test("a change the server never confirmed wins and is sent again", () => {
  assert.deepEqual(reconcileMode(unsent("nl-fa"), "nl-en"), { mode: "nl-fa", upload: true });
  assert.deepEqual(reconcileMode(unsent(null), "nl-en"), { mode: "nl-en", upload: false });
});

test("only the three modes are valid", () => {
  assert.equal(isSupportMode("nl-fa"), true);
  assert.equal(isSupportMode("fa"), false);
  assert.equal(isSupportMode(null), false);
});
