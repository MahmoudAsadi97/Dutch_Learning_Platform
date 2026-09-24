import assert from "node:assert/strict";
import { test } from "node:test";
import { claimAudioFocus, isAudioRecording, releaseAudioFocus, stopFocusedAudio, subscribeAudioRecording, suspendAudioForRecording } from "../../lib/client/audio-focus.ts";

test("a phrase and a legacy player cannot both own audio focus", () => {
  const first = Symbol("first");
  const next = Symbol("next");
  const stopped = [];
  claimAudioFocus(first, () => { stopped.push("first"); releaseAudioFocus(first); });
  claimAudioFocus(next, () => stopped.push("next"));
  assert.deepEqual(stopped, ["first"]);
  releaseAudioFocus(first);
  stopFocusedAudio();
  assert.deepEqual(stopped, ["first", "next"]);
});

test("repeated focus updates do not stop the current phrase and release never stops unrelated audio", () => {
  const owner = Symbol("current");
  let stops = 0;
  claimAudioFocus(owner, () => stops++);
  claimAudioFocus(owner, () => stops++);
  assert.equal(stops, 0);
  releaseAudioFocus(owner);
  stopFocusedAudio();
  assert.equal(stops, 0);
});

test("microphone permission and recording stop examples and block playback until the last capture releases", () => {
  let stops = 0;
  const states = [];
  const unsubscribe = subscribeAudioRecording(() => states.push(isAudioRecording()));
  claimAudioFocus(Symbol("example"), () => stops++);
  const first = suspendAudioForRecording();
  const second = suspendAudioForRecording();
  assert.equal(stops, 1);
  assert.equal(isAudioRecording(), true);
  assert.equal(claimAudioFocus(Symbol("accidental click"), () => {}), false);
  first(); first();
  assert.equal(isAudioRecording(), true);
  second();
  assert.equal(isAudioRecording(), false);
  const owner = Symbol("after recording");
  assert.equal(claimAudioFocus(owner, () => {}), true);
  releaseAudioFocus(owner);
  unsubscribe();
  assert.deepEqual(states, [true, true, true, false]);
});
