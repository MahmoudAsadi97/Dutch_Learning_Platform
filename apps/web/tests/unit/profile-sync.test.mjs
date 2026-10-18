import assert from "node:assert/strict";
import { test } from "node:test";
import { isSupportMode, normalizeSupportMode, reconcileMode } from "../../lib/client/profile-sync.ts";

const chosen = (stored) => ({ stored, pending: false });
const unsent = (stored) => ({ stored, pending: true });

test("a server without a value adopts a choice made on this device", () => {
  assert.deepEqual(reconcileMode(chosen("nl"), null), { mode: "nl", upload: true });
  assert.deepEqual(reconcileMode(chosen("nl-en"), undefined), { mode: "nl-en", upload: true });
});

test("a default is not a choice: with nothing chosen anywhere nothing is sent", () => {
  assert.deepEqual(reconcileMode(chosen(null), null), { mode: "nl-en", upload: false });
  assert.deepEqual(reconcileMode(chosen("de"), null), { mode: "nl-en", upload: false });
});

test("a server value wins over an older device value", () => {
  assert.deepEqual(reconcileMode(chosen("nl"), "nl-en"), { mode: "nl-en", upload: false });
  assert.deepEqual(reconcileMode(chosen(null), "nl"), { mode: "nl", upload: false });
});

test("a change the server never confirmed wins and is sent again", () => {
  assert.deepEqual(reconcileMode(unsent("nl"), "nl-en"), { mode: "nl", upload: true });
  assert.deepEqual(reconcileMode(unsent(null), "nl-en"), { mode: "nl-en", upload: false });
});

test("only Dutch and Dutch with English are current choices", () => {
  assert.equal(isSupportMode("nl"), true);
  assert.equal(isSupportMode("nl-en"), true);
  assert.equal(isSupportMode("nl-fa"), false);
  assert.equal(isSupportMode("fa"), false);
  assert.equal(isSupportMode(null), false);
});

test("retired preferences normalize without restoring Persian or uploading a server choice", () => {
  assert.equal(normalizeSupportMode("nl-fa"), "nl-en");
  assert.equal(normalizeSupportMode("nl-fa-en"), "nl-en");
  assert.equal(normalizeSupportMode("unknown"), null);
  assert.deepEqual(reconcileMode(chosen("nl-fa"), null), { mode: "nl-en", upload: true });
  assert.deepEqual(reconcileMode(chosen(null), "nl-fa-en"), { mode: "nl-en", upload: false });
  assert.deepEqual(reconcileMode(unsent("nl-fa"), "nl"), { mode: "nl-en", upload: true });
});
