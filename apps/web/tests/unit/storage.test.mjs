import assert from "node:assert/strict";
import { test } from "node:test";
import {
  LEARNER_KEY_PREFIXES,
  clearLearnerStorage,
  isLearnerKey,
  storageKeys,
} from "../../lib/client/storage.ts";

function fakeStorage(entries) {
  const map = new Map(Object.entries(entries));
  return {
    get length() {
      return map.size;
    },
    key: (index) => [...map.keys()][index] ?? null,
    removeItem: (key) => map.delete(key),
    has: (key) => map.has(key),
  };
}

test("key builders produce the established names", () => {
  assert.equal(storageKeys.languageSupport, "taalstudio.language-support");
  assert.equal(storageKeys.draft("L1", "a1"), "taalstudio.draft.L1.a1");
  assert.equal(storageKeys.test("L1", "a1"), "taalstudio.test.L1.a1");
  assert.equal(storageKeys.stories("L1", "a1"), "taalstudio.stories.L1.a1");
  assert.equal(storageKeys.practiceStage("L1"), "taalstudio.practice-stage.L1");
  assert.equal(
    storageKeys.topicDraft("L1", "a1", "writing", "a1-t001"),
    "taalstudio.topic-draft.L1.a1.writing.a1-t001",
  );
  assert.equal(storageKeys.conversation("L1", "a1", "a1-t001"), "taalstudio.conversation.L1.a1.a1-t001");
  for (const prefix of LEARNER_KEY_PREFIXES) assert.ok(prefix.startsWith("taalstudio."));
  assert.ok(!isLearnerKey(storageKeys.languageSupport));
});

test("sign-out removes every learner key and keeps the language preference", () => {
  const local = fakeStorage({
    [storageKeys.languageSupport]: "nl-fa",
    [storageKeys.stories("L1", "a1")]: "[]",
    [storageKeys.practiceStage("L1")]: "a2",
    "unrelated.key": "x",
  });
  const session = fakeStorage({
    [storageKeys.draft("L1", "a1")]: "tekst",
    [storageKeys.test("L1", "a1")]: "{}",
    [storageKeys.topicDraft("L1", "a1", "writing", "a1-t001")]: "tekst",
    [storageKeys.conversation("L1", "a1", "a1-t001")]: "{}",
  });
  assert.equal(clearLearnerStorage([local, session]), 6);
  assert.ok(local.has(storageKeys.languageSupport) && local.has("unrelated.key"));
  assert.equal(local.length, 2);
  assert.equal(session.length, 0);
});

test("a storage that throws does not stop the sweep", () => {
  const broken = {
    get length() {
      throw new Error("disabled");
    },
    key: () => null,
    removeItem: () => undefined,
  };
  const fine = fakeStorage({ [storageKeys.draft("L1", "a1")]: "tekst" });
  assert.equal(clearLearnerStorage([broken, fine]), 1);
});
