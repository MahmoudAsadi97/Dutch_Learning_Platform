import assert from "node:assert/strict";
import { test } from "node:test";
import { PhraseAudioController, splitSpeechText } from "../../lib/client/phrase-audio.ts";

const flush = () => new Promise(resolve => setImmediate(resolve));
function fixture(synthesize = async () => ({ blob: new Blob(["wav"]) }), limits) {
  const players = [];
  const created = [];
  const revoked = [];
  const calls = [];
  const controller = new PhraseAudioController({
    async synthesize(text, signal) { calls.push({ text, signal }); return synthesize(text, signal); },
    createUrl(blob) { const url = `blob:${created.length}`; created.push({ url, blob }); return url; },
    revokeUrl(url) { revoked.push(url); },
    player(url) {
      const item = { url, onended: null, onerror: null, pauses: 0, loads: 0, removed: [], play: () => Promise.resolve(), pause() { this.pauses++; }, load() { this.loads++; }, removeAttribute(value) { this.removed.push(value); } };
      players.push(item); return item;
    },
  }, limits);
  return { controller, players, created, revoked, calls };
}
async function finish(f, owner, text) {
  const result = f.controller.play(owner, text);
  await flush();
  f.players.at(-1).onended();
  await result;
}

test("audio is never fetched or played until explicitly requested", () => {
  const f = fixture();
  assert.equal(f.calls.length, 0);
  assert.equal(f.players.length, 0);
  assert.equal(f.controller.getSnapshot().phase, "idle");
});

test("a stopped pending request cannot start stale speech even when the provider ignores cancellation", async () => {
  let release;
  const f = fixture(() => new Promise(resolve => { release = resolve; }));
  const attempt = f.controller.play("first", "Dag.");
  await flush();
  f.controller.stop("first");
  assert.equal(f.calls[0].signal.aborted, true);
  release({ blob: new Blob(["old"]) });
  await attempt;
  assert.equal(f.players.length, 0);
  assert.equal(f.controller.getSnapshot().phase, "idle");
});

test("a new button preempts the old player and object URLs are revoked exactly once", async () => {
  const f = fixture();
  const first = f.controller.play("first", "Dag.");
  await flush();
  const second = f.controller.play("second", "Tot morgen.");
  await flush();
  assert.equal(f.players[0].pauses, 1);
  assert.deepEqual(f.players[0].removed, ["src"]);
  assert.equal(f.players[0].onended, null);
  assert.equal(f.controller.getSnapshot().owner, "second");
  f.controller.stop("first");
  assert.equal(f.controller.getSnapshot().owner, "second");
  f.players[1].onended();
  await Promise.all([first, second]);
  assert.deepEqual(f.revoked, ["blob:0", "blob:1"]);
});

test("replay uses bounded memory cache, while a new phrase evicts the least-recent item", async () => {
  const f = fixture(undefined, { entries: 1, bytes: 8 });
  await finish(f, "a", "Dag.");
  await finish(f, "a", "Dag.");
  assert.equal(f.calls.length, 1);
  await finish(f, "b", "Hallo.");
  await finish(f, "a", "Dag.");
  assert.equal(f.calls.length, 3);
  f.controller.clear();
  await finish(f, "a", "Dag.");
  assert.equal(f.calls.length, 4);
});

test("oversize clips are playable but not retained in the replay cache", async () => {
  const f = fixture(undefined, { entries: 10, bytes: 2 });
  await finish(f, "a", "Dag.");
  await finish(f, "a", "Dag.");
  assert.equal(f.calls.length, 2);
});

test("long passages preserve text and respect the speech endpoint length limit", () => {
  const original = Array.from({ length: 400 }, (_, index) => index % 3 ? "goedemorgen" : "  dag\n").join(" ");
  const chunks = splitSpeechText(original);
  assert.ok(chunks.length > 1);
  assert.ok(chunks.every(chunk => chunk.length <= 600 && chunk.length > 0));
  assert.equal(chunks.join(" "), original.trim().replace(/\s+/g, " "));
  assert.deepEqual(splitSpeechText(" \n "), []);
  assert.throws(() => splitSpeechText("x".repeat(601)), /too long/);
  assert.throws(() => splitSpeechText("dag ".repeat(4000)), /too long/);
});

test("cancelling a long passage prevents fetching the next segment", async () => {
  const f = fixture();
  const result = f.controller.play("long", "Een woord. ".repeat(100));
  await flush();
  assert.equal(f.calls.length, 1);
  f.controller.stop("long");
  await result;
  assert.equal(f.calls.length, 1);
});

test("playback errors are observed and release the audio element", async () => {
  const f = fixture();
  const result = f.controller.play("first", "Dag.");
  await flush();
  f.players[0].onerror();
  await result;
  assert.equal(f.controller.getSnapshot().error, "unavailable");
  assert.deepEqual(f.revoked, ["blob:0"]);
});

test("provider internals are replaced by a safe error state", async () => {
  const f = fixture(async () => { throw new Error("secret-provider-diagnostics"); });
  await f.controller.play("first", "Dag.");
  assert.equal(f.controller.getSnapshot().error, "unavailable");
  assert.equal(f.players.length, 0);
});

test("late rejection of an interrupted play promise is observed and cannot overwrite the new state", async () => {
  let rejectPlay;
  const players = [];
  const controller = new PhraseAudioController({
    synthesize: async () => ({ blob: new Blob(["wav"]) }),
    createUrl: () => "blob:late",
    revokeUrl: () => {},
    player: () => {
      const value = { onended: null, onerror: null, pause() {}, load() {}, removeAttribute() {}, play: () => new Promise((_, reject) => { rejectPlay = reject; }) };
      players.push(value); return value;
    },
  });
  const result = controller.play("old", "Dag.");
  await flush();
  controller.stop();
  rejectPlay(new DOMException("aborted", "AbortError"));
  await result;
  await flush();
  assert.equal(controller.getSnapshot().phase, "idle");
  assert.equal(players[0].onended, null);
});
