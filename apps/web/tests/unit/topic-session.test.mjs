import assert from "node:assert/strict";
import { test } from "node:test";
import {
  againLabel,
  completionLines,
  completionState,
  summaryActions,
} from "../../components/exercise/completion.ts";
import {
  RENDERED_KINDS,
  isPassagePrompt,
  passageAudioPath,
  passageRevealed,
  sessionRequest,
} from "../../components/exercise/registry.ts";

const kinds = ["choice", "cloze_choice"];

test("a page's session asks for its kinds only; a topic's names the topic, and retry only when retrying", () => {
  assert.deepEqual(sessionRequest("stage_skill", null, false, kinds), { source: "stage_skill", kinds });
  assert.deepEqual(sessionRequest("while_you_wait", null, true, kinds), { source: "while_you_wait", kinds });
  const topic = { stageId: "pre-a1", topicId: "pre-a1-t001", skill: "reading" };
  assert.deepEqual(sessionRequest("topic", topic, false, kinds), {
    source: "topic",
    stage_id: "pre-a1",
    topic_id: "pre-a1-t001",
    skill: "reading",
    kinds,
  });
  assert.equal(sessionRequest("topic", topic, true, kinds).retry, true);
});

test("passage steps are never asked for, and say when their translation or transcript has come", () => {
  for (const kind of ["intro", "read_passage", "listen_passage"]) assert.ok(!RENDERED_KINDS.includes(kind));
  const read = { kind: "read_passage", text: { nl: "Ik woon in Gent." }, vocabulary: [] };
  const heard = { kind: "listen_passage", parts: 2, transcript: null, vocabulary: [] };
  assert.ok(isPassagePrompt(read) && isPassagePrompt(heard));
  assert.ok(!isPassagePrompt({ kind: "choice", direction: "question", stem: {}, options: [] }));
  assert.equal(passageRevealed(read), false);
  assert.equal(passageRevealed({ ...read, text: { nl: "Ik woon in Gent.", en: "I live in Ghent." } }), true);
  assert.equal(passageRevealed(heard), false);
  assert.equal(passageRevealed({ ...heard, transcript: { nl: "Hallo." } }), true);
});

test("a listening passage is heard from the topic's own route, or the lesson's", () => {
  assert.equal(
    passageAudioPath({ stage_id: "pre-a1", topic_id: "pre-a1-t001" }),
    "curriculum/pre-a1/topics/pre-a1-t001/listening",
  );
  assert.equal(passageAudioPath({ stage_id: "a1", topic_id: null }), "curriculum/a1/listening");
  assert.equal(passageAudioPath({ stage_id: "a1", topic_id: "a b" }), "curriculum/a1/topics/a%20b/listening");
});

const completion = (overrides = {}) => ({
  scope: "topic",
  skill: "reading",
  topic_id: "pre-a1-t001",
  counted: true,
  reason: null,
  passed: true,
  correct: 2,
  total: 2,
  required: 2,
  completed: true,
  to_retry: 0,
  ...overrides,
});
const keys = (value) => completionLines(value).map((line) => line.key);

test("the summary says what the session did for the topic, as the server decided", () => {
  assert.deepEqual(keys(completion()), ["completionPassed"]);
  assert.deepEqual(keys(completion({ passed: false, correct: 1, to_retry: 1 })), ["completionKept"]);
  assert.deepEqual(keys(completion({ passed: false, completed: false, correct: 1 })), ["completionRuleAll"]);
  assert.deepEqual(completionLines(completion({ passed: false, completed: false, total: 4, required: 3 })), [
    { key: "completionRule", values: { required: 3, total: 4 } },
  ]);
  assert.deepEqual(keys(completion({ counted: false, reason: "retry", completed: false })), [
    "completionRetry",
    "completionWhole",
  ]);
  assert.deepEqual(keys(completion({ counted: false, reason: "retry" })), [
    "completionRetry",
    "completionAlready",
  ]);
  assert.deepEqual(keys(completion({ counted: false, reason: "unfinished", completed: false })), [
    "completionUnfinished",
  ]);
  assert.deepEqual(keys(completion({ counted: false, reason: "content_changed" })), [
    "completionChanged",
    "completionAlready",
  ]);
  assert.deepEqual(keys(completion({ counted: false, reason: "open_task", skill: "writing" })), [
    "completionWarmUp",
  ]);
  assert.deepEqual(keys(completion({ counted: false, reason: "assisted", completed: false })), [
    "completionAssisted",
  ]);
  assert.deepEqual(keys(completion({ counted: false, reason: "assisted" })), [
    "completionAssisted",
    "completionAlready",
  ]);
  assert.deepEqual(keys(completion({ scope: "lesson" })), []);
  assert.deepEqual(keys(null), []);
  // done is a check; anything else is neutral, and a warm-up never reads as done
  assert.equal(completionState(completion()), "done");
  assert.equal(completionState(completion({ completed: false })), "open");
  assert.equal(completionState(completion({ reason: "open_task", skill: "writing" })), "open");
});

test("the way that helps most comes first: the missed questions, the task, or all again", () => {
  const order = (value, canRetry = true) => summaryActions(value, canRetry).map((action) => action.kind);
  assert.deepEqual(order(null), ["again", "exit"]);
  assert.deepEqual(order(completion()), ["exit", "again"]);
  assert.deepEqual(order(completion({ passed: false, completed: false, to_retry: 1 })), [
    "retry",
    "again",
    "exit",
  ]);
  assert.deepEqual(order(completion({ passed: false, completed: false, to_retry: 1 }), false), [
    "again",
    "exit",
  ]);
  assert.deepEqual(order(completion({ passed: false, completed: false, to_retry: 0 })), ["again", "exit"]);
  // questions never tried, or content that changed, are not "missed": all the questions again leads
  assert.deepEqual(
    order(completion({ counted: false, reason: "unfinished", completed: false, to_retry: 2 })),
    ["again", "exit"],
  );
  assert.deepEqual(
    order(completion({ counted: false, reason: "content_changed", completed: false, to_retry: 1 })),
    ["again", "exit"],
  );
  // a retry may still be followed by another on what it missed
  assert.deepEqual(order(completion({ counted: false, reason: "retry", completed: false, to_retry: 1 })), [
    "retry",
    "again",
    "exit",
  ]);
  assert.deepEqual(order(completion({ counted: false, reason: "open_task", skill: "writing" })), [
    "exit",
    "again",
  ]);
  assert.deepEqual(order(completion({ counted: false, reason: "assisted", completed: false })), [
    "again",
    "exit",
  ]);
  assert.equal(summaryActions(null, false)[0].variant, "primary");
  assert.equal(againLabel(null), "again");
  assert.equal(againLabel(completion()), "againAll");
  assert.equal(againLabel(completion({ reason: "open_task", skill: "speaking" })), "warmUpAgain");
});
