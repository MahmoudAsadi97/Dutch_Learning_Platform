/**
 * The exercise runner's state, as a pure reducer: server responses are events, never cache entries, so a
 * session can be resumed exactly from what the API returns. An answer that did not reach the server is kept,
 * and sending the same answer again reuses its request id, so the API replays instead of counting twice; a
 * different answer gets a new id (the API refuses one id for two answers). The phases: creating, answering
 * (an item is shown), checking (an answer is on its way), feedback (the answer's result is shown),
 * finishing, summary, and error (the session could not be loaded).
 */
import type { Answer, AnswerResult, FinishResult, ItemView, SessionView } from "../../lib/client/exercises";

export type Phase = "creating" | "answering" | "checking" | "feedback" | "finishing" | "summary" | "error";
export type SkipReason = "unknown" | "no_microphone" | "no_audio";

export interface Pending {
  itemId: string;
  requestId: string;
  answer: Answer | null; // null for a skip
  skip: SkipReason | null;
}

export interface RunnerState {
  phase: Phase;
  session: SessionView | null;
  current: string | null; // the item on screen
  result: AnswerResult | null; // the last answer's result, shown in the feedback phase
  pending: Pending | null; // the answer on its way, kept after a failure for sending again
  failed: boolean; // the last answer or finish did not reach the server
  finished: FinishResult | null;
}

export type RunnerEvent =
  | { type: "RESET" }
  | { type: "LOADED"; session: SessionView }
  | { type: "LOAD_FAILED" }
  | { type: "SUBMIT"; pending: Pending }
  | { type: "ANSWERED"; result: AnswerResult }
  | { type: "ANSWER_FAILED" }
  | { type: "CONTINUE" }
  | { type: "FINISH" }
  | { type: "FINISHED"; result: FinishResult }
  | { type: "FINISH_FAILED" };

export const initialState: RunnerState = {
  phase: "creating",
  session: null,
  current: null,
  result: null,
  pending: null,
  failed: false,
  finished: null,
};

function sameAnswer(pending: Pending, answer: Answer | null, skip: SkipReason | null): boolean {
  return pending.skip === skip && JSON.stringify(pending.answer) === JSON.stringify(answer);
}

/** The request id for sending `answer` (or `skip`) to `item` now: the failed one's again, or a fresh one. */
export function requestIdFor(
  state: RunnerState,
  item: Pick<ItemView, "id">,
  answer: Answer | null,
  skip: SkipReason | null,
  mint: () => string,
): string {
  const kept = state.pending;
  return kept && state.failed && kept.itemId === item.id && sameAnswer(kept, answer, skip)
    ? kept.requestId
    : mint();
}

export function currentItem(state: RunnerState): ItemView | null {
  return state.session?.items.find((item) => item.id === state.current) ?? null;
}

function withResult(session: SessionView, result: AnswerResult): SessionView {
  return {
    ...session,
    progress: result.progress,
    next_item_id: result.next_item_id,
    items: session.items.map((item) =>
      item.id === result.item_id
        ? {
            ...item,
            state: result.closed ? "closed" : "open",
            attempts_left: result.attempts_left,
            feedback: result.closed ? result.feedback : null,
          }
        : item,
    ),
  };
}

function next(state: RunnerState, session: SessionView): RunnerState {
  if (session.status !== "active")
    return { ...state, session, phase: "summary", current: null, result: null };
  if (!session.next_item_id) return { ...state, session, phase: "finishing", current: null, result: null };
  return { ...state, session, phase: "answering", current: session.next_item_id, result: null };
}

export function reduce(state: RunnerState, event: RunnerEvent): RunnerState {
  switch (event.type) {
    case "RESET":
      // a new session is on its way: nothing of the last one stays on screen
      return initialState;
    case "LOADED": {
      const loaded = { ...state, failed: false, pending: null };
      if (event.session.status === "finished" && event.session.summary)
        return {
          ...loaded,
          session: event.session,
          phase: "summary",
          current: null,
          result: null,
          finished: { id: event.session.id, status: "finished", summary: event.session.summary, points: 0 },
        };
      return next(loaded, event.session);
    }
    case "LOAD_FAILED":
      return state.session ? state : { ...state, phase: "error" };
    case "SUBMIT": {
      if (state.phase !== "answering" || !state.session) return state;
      if (!state.session.items.some((candidate) => candidate.id === event.pending.itemId)) return state;
      return { ...state, phase: "checking", failed: false, pending: event.pending };
    }
    case "ANSWERED": {
      if (!state.session || state.phase !== "checking") return state;
      const session = withResult(state.session, event.result);
      const settled = { ...state, session, pending: null, failed: false };
      // an intro card has nothing to show back: straight to the first item
      if (event.result.outcome === "done") return next(settled, session);
      return { ...settled, phase: "feedback", result: event.result };
    }
    case "ANSWER_FAILED":
      // back to the item with the answer kept; sending it again reuses the same request id
      return state.phase === "checking" ? { ...state, phase: "answering", failed: true } : state;
    case "CONTINUE":
      return state.phase === "feedback" && state.session ? next(state, state.session) : state;
    case "FINISH":
      return state.session && state.phase !== "summary"
        ? { ...state, phase: "finishing", failed: false }
        : state;
    case "FINISHED":
      return {
        ...state,
        phase: "summary",
        finished: event.result,
        failed: false,
        current: null,
        result: null,
        session: state.session
          ? { ...state.session, status: "finished", summary: event.result.summary }
          : null,
      };
    case "FINISH_FAILED":
      return state.phase === "finishing" ? { ...state, failed: true } : state;
  }
}
