import assert from "node:assert/strict";
import { test } from "node:test";
import { currentItem, initialState, reduce, requestIdFor } from "../../components/exercise/sessionReducer.ts";

const option = (id) => ({ id, nl: id });
const choice = (id, position) => ({
  id,
  position,
  kind: "choice",
  skill: "",
  state: "open",
  attempts_left: 2,
  prompt: { kind: "choice", direction: "term", stem: { en: "x" }, options: ["a", "b", "c", "d"].map(option) },
  feedback: null,
});
const session = (overrides = {}) => ({
  id: "s1",
  source: "stage_skill",
  stage_id: "a1",
  focus: "words",
  library_topic: null,
  status: "active",
  content_status: "unreviewed",
  resumed: false,
  items: [
    { ...choice("intro", 0), kind: "intro", attempts_left: 1, prompt: { kind: "intro", words: [] } },
    choice("i1", 1),
    choice("i2", 2),
  ],
  next_item_id: "intro",
  progress: { closed: 0, total: 2, queued: 0 },
  summary: null,
  ...overrides,
});
const result = (itemId, overrides = {}) => ({
  item_id: itemId,
  attempt: 1,
  outcome: "correct",
  closed: true,
  requeue: false,
  attempts_left: 0,
  feedback: { outcome: "correct", correct: "a" },
  points: 1,
  progress: { closed: 1, total: 2, queued: 0 },
  next_item_id: "i2",
  ...overrides,
});
const pending = (itemId, requestId, answer = { option: "a" }) => ({ itemId, requestId, answer, skip: null });

test("a loaded session shows its next item; an intro card goes straight on to the first item", () => {
  let state = reduce(initialState, { type: "LOADED", session: session() });
  assert.equal(state.phase, "answering");
  assert.equal(currentItem(state).id, "intro");
  state = reduce(state, { type: "SUBMIT", pending: pending("intro", "r-intro", { done: true }) });
  state = reduce(state, {
    type: "ANSWERED",
    result: result("intro", {
      outcome: "done",
      next_item_id: "i1",
      progress: { closed: 0, total: 2, queued: 0 },
    }),
  });
  assert.equal(state.phase, "answering");
  assert.equal(state.current, "i1");
});

test("an answer is checked, shown, and the learner continues to the next item", () => {
  let state = reduce(initialState, { type: "LOADED", session: session({ next_item_id: "i1" }) });
  state = reduce(state, { type: "SUBMIT", pending: pending("i1", "r1") });
  assert.equal(state.phase, "checking");
  state = reduce(state, { type: "ANSWERED", result: result("i1") });
  assert.equal(state.phase, "feedback");
  assert.equal(state.result.outcome, "correct");
  assert.equal(state.session.items.find((item) => item.id === "i1").state, "closed");
  state = reduce(state, { type: "CONTINUE" });
  assert.equal(state.current, "i2");
});

test("a failed answer keeps its request id for the same answer, and another answer gets a new one", () => {
  let state = reduce(initialState, { type: "LOADED", session: session({ next_item_id: "i1" }) });
  const item = currentItem(state);
  const first = requestIdFor(state, item, { option: "a" }, null, () => "minted-1");
  state = reduce(state, { type: "SUBMIT", pending: pending("i1", first) });
  state = reduce(state, { type: "ANSWER_FAILED" });
  assert.equal(state.phase, "answering");
  assert.equal(state.failed, true);
  assert.equal(
    requestIdFor(state, currentItem(state), { option: "a" }, null, () => "minted-2"),
    "minted-1",
  );
  assert.equal(
    requestIdFor(state, currentItem(state), { option: "b" }, null, () => "minted-3"),
    "minted-3",
  );
  assert.equal(
    requestIdFor(state, currentItem(state), null, "unknown", () => "minted-4"),
    "minted-4",
  );
});

test("a miss comes back with a new attempt and a new request id", () => {
  let state = reduce(initialState, { type: "LOADED", session: session({ next_item_id: "i1" }) });
  state = reduce(state, { type: "SUBMIT", pending: pending("i1", "first-try") });
  state = reduce(state, {
    type: "ANSWERED",
    result: result("i1", {
      outcome: "incorrect",
      closed: false,
      requeue: true,
      attempts_left: 1,
      next_item_id: "i2",
      progress: { closed: 0, total: 2, queued: 1 },
    }),
  });
  const missed = state.session.items.find((item) => item.id === "i1");
  assert.equal(missed.state, "open");
  assert.equal(missed.attempts_left, 1);
  assert.equal(
    requestIdFor(state, missed, { option: "a" }, null, () => "second-try"),
    "second-try",
  );
  state = reduce(state, { type: "CONTINUE" });
  assert.equal(state.current, "i2", "the miss waits until the end");
});

test("the last answer leads to finishing, and the summary ends the run", () => {
  let state = reduce(initialState, { type: "LOADED", session: session({ next_item_id: "i2" }) });
  state = reduce(state, { type: "SUBMIT", pending: pending("i2", "r2") });
  state = reduce(state, { type: "ANSWERED", result: result("i2", { next_item_id: null }) });
  state = reduce(state, { type: "CONTINUE" });
  assert.equal(state.phase, "finishing");
  const summary = { items_total: 2, answered: 2, points_earned: 2 };
  state = reduce(state, { type: "FINISHED", result: { id: "s1", status: "finished", summary, points: 0 } });
  assert.equal(state.phase, "summary");
  assert.equal(state.session.status, "finished");
});

test("a finished session resumes on its summary; a session that cannot load is an error", () => {
  const done = reduce(initialState, {
    type: "LOADED",
    session: session({ status: "finished", next_item_id: null, summary: { items_total: 2 } }),
  });
  assert.equal(done.phase, "summary");
  assert.equal(reduce(initialState, { type: "LOAD_FAILED" }).phase, "error");
});

test("events out of turn change nothing", () => {
  const state = reduce(initialState, { type: "LOADED", session: session({ next_item_id: "i1" }) });
  assert.equal(reduce(state, { type: "CONTINUE" }), state);
  assert.equal(reduce(state, { type: "ANSWERED", result: result("i1") }), state);
});
