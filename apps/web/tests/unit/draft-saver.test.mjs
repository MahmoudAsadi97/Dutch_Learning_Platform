import assert from "node:assert/strict";
import { test } from "node:test";
import { DraftSaver } from "../../lib/client/draft-saver.ts";

test("writes are serial and an older write cannot win over newer text", async () => {
  const writes = [];
  let release;
  const firstWrite = new Promise((resolve) => { release = resolve; });
  const saver = new DraftSaver("", async (text) => {
    if (text === "first") await firstWrite;
    writes.push(text);
  });
  const first = saver.save("first");
  const next = saver.save("latest");
  await Promise.resolve();
  assert.deepEqual(writes, []);
  release();
  await Promise.all([first, next]);
  assert.deepEqual(writes, ["first", "latest"]);
  assert.equal(saver.isSaved("latest"), true);
});

test("clearing a saved draft persists the empty text", async () => {
  const writes = [];
  const saver = new DraftSaver("old draft", async (text) => { writes.push(text); });
  await saver.save("");
  assert.deepEqual(writes, [""]);
  assert.equal(saver.isSaved(""), true);
});

test("duplicate queued autosaves are written only once", async () => {
  let count = 0;
  const saver = new DraftSaver("", async () => { count++; });
  await Promise.all([saver.save("draft"), saver.save("draft")]);
  assert.equal(count, 1);
});

test("failure stays unsaved and retry is not blocked by the failed promise", async () => {
  let count = 0;
  const saver = new DraftSaver("", async () => {
    if (++count === 1) throw new Error("offline");
  });
  await assert.rejects(saver.save("keep this"), /offline/);
  assert.equal(saver.isSaved("keep this"), false);
  await saver.save("keep this");
  assert.equal(saver.isSaved("keep this"), true);
  assert.equal(count, 2);
});
