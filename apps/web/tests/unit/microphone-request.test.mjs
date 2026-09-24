import assert from "node:assert/strict";
import { test } from "node:test";
import { MicrophoneRequestGate } from "../../lib/client/microphone-request.ts";

function deferred() {
  let resolve, reject;
  const promise = new Promise((yes, no) => { resolve = yes; reject = no; });
  return { promise, resolve, reject };
}
function stream() { let stops = 0; return { value: { getTracks: () => [{ stop: () => stops++ }] }, stops: () => stops }; }

test("releasing the talk button before permission is granted closes a late microphone stream", async () => {
  const gate = new MicrophoneRequestGate();
  const permission = deferred();
  const microphone = stream();
  const result = gate.open(() => permission.promise);
  gate.cancel();
  permission.resolve(microphone.value);
  assert.equal(await result, null);
  assert.equal(microphone.stops(), 1);
  assert.equal(gate.isPending(), false);
});

test("an old permission response cannot replace or clear a newer pending request", async () => {
  const gate = new MicrophoneRequestGate();
  const old = deferred(); const current = deferred();
  const oldMic = stream(); const nextMic = stream();
  const first = gate.open(() => old.promise);
  gate.cancel();
  const second = gate.open(() => current.promise);
  old.resolve(oldMic.value);
  assert.equal(await first, null);
  assert.equal(gate.isPending(), true);
  current.resolve(nextMic.value);
  assert.equal(await second, nextMic.value);
  assert.equal(nextMic.stops(), 0);
});

test("repeated pointer events cannot open two microphone permission requests", async () => {
  const gate = new MicrophoneRequestGate();
  const permission = deferred(); const microphone = stream();
  const first = gate.open(() => permission.promise);
  let calls = 0;
  assert.equal(await gate.open(async () => { calls++; return microphone.value; }), null);
  assert.equal(calls, 0);
  permission.resolve(microphone.value);
  assert.equal(await first, microphone.value);
});

test("a current denial is surfaced, while a denial after cancellation cannot affect a new request", async () => {
  const gate = new MicrophoneRequestGate();
  await assert.rejects(gate.open(async () => { throw new Error("permission denied"); }), /permission denied/);
  assert.equal(gate.isPending(), false);
  const permission = deferred();
  const pending = gate.open(() => permission.promise);
  gate.cancel();
  permission.reject(new Error("stale denial"));
  assert.equal(await pending, null);
});
