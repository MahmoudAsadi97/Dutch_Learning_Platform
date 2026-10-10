"use client";

import {
  useEffect,
  useEffectEvent,
  useReducer,
  useRef,
  useState,
  type KeyboardEvent as ReactKeyboardEvent,
} from "react";

import { Button, ButtonLink } from "@/components/ui/Button";
import { Dialog } from "@/components/ui/Dialog";
import { HonestyChip } from "@/components/ui/HonestyChip";
import { Notice } from "@/components/ui/Notice";
import { ProgressBar } from "@/components/ui/ProgressBar";
import { SkeletonPanel } from "@/components/ui/Skeleton";
import { UiText } from "@/components/ui/UiText";
import { exerciseCopy } from "@/lib/copy/exercise";
import { ApiError, newRequestId } from "@/lib/client/api";
import { errorCopy } from "@/lib/client/error-copy";
import { isAbort } from "@/lib/client/errors";
import { exercises, type Answer } from "@/lib/client/exercises";
import { timeRoundTrip } from "@/lib/client/round-trips";
import { playTone } from "@/lib/client/tones";
import { fill, uiCopy, type Copy } from "@/lib/ui-copy";

import { ChoiceItem } from "./ChoiceItem";
import { FeedbackBar, outcomeCopy } from "./FeedbackBar";
import { IntroCard } from "./IntroCard";
import { RENDERED_KINDS, isChoicePrompt, optionForKey } from "./registry";
import { ReportDialog } from "./ReportDialog";
import { SessionSummary } from "./SessionSummary";
import { currentItem, initialState, reduce, requestIdFor, type SkipReason } from "./sessionReducer";

/** A new key for each live-region message, so the same words are announced again. */
let announcements = 0;
function nextAnnouncement(): number {
  announcements += 1;
  return announcements;
}

/** Attempts an item starts with (MAX_ATTEMPTS on the server); fewer means it was missed once. */
const FIRST_ATTEMPTS = 2;

/** Keys typed into a field belong to that field, not to the session. */
function isTextEntry(target: EventTarget | null): boolean {
  if (!(target instanceof HTMLElement)) return false;
  if (target.isContentEditable) return true;
  if (target instanceof HTMLTextAreaElement || target instanceof HTMLSelectElement) return true;
  return target instanceof HTMLInputElement && target.type !== "radio";
}

interface Props {
  source: "stage_skill" | "while_you_wait";
}

/**
 * One practice session, start to summary, driven by the reducer in sessionReducer.ts. The server generates
 * and grades; this screen shows one item at a time, sends the answer, shows what it revealed, and moves on.
 * Keyboard, while focus is in the item: 1 to 4 choose an option (the number row's key on any layout, or a
 * Persian digit) and move focus to it, Enter checks it (on "Verder" it goes on); Escape asks to stop.
 * Focus moves to each new question, then to "Verder" after the verdict; a polite live region says the
 * outcome. Tones play only after the server's verdict, and never for a miss.
 */
export function ExerciseSession({ source }: Props) {
  const [state, dispatch] = useReducer(reduce, initialState);
  // minted once, so a second effect run (or a retry) asks for the same session and the API replays it
  const [createId, setCreateId] = useState(() => newRequestId());
  const [loadTry, setLoadTry] = useState(0);
  const [loadError, setLoadError] = useState<Copy | null>(null);
  const [selected, setSelected] = useState<string | null>(null);
  const [actionError, setActionError] = useState<Copy | null>(null);
  const [nudge, setNudge] = useState(false);
  const [dialog, setDialog] = useState<"exit" | "report" | null>(null);
  const [announcement, setAnnouncement] = useState<{ id: number; text: Copy } | null>(null);
  const headingRef = useRef<HTMLHeadingElement>(null);
  const continueRef = useRef<HTMLButtonElement>(null);
  const busy = useRef(false);
  const finishId = useRef<string | null>(null);
  const early = useRef(false);
  const shown = useRef<string | null>(null);

  const session = state.session;
  const item = currentItem(state);

  useEffect(() => {
    let live = true;
    exercises
      .create({ source, kinds: RENDERED_KINDS }, createId)
      .then((created) => {
        if (live) dispatch({ type: "LOADED", session: created });
      })
      .catch((cause: unknown) => {
        if (!live || isAbort(cause)) return;
        setLoadError(errorCopy(cause, exerciseCopy.loadFailed, { not_ready: exerciseCopy.notReady }, "load"));
        dispatch({ type: "LOAD_FAILED" });
      });
    return () => {
      live = false;
    };
  }, [source, createId, loadTry]);

  // the last item answered: close the session (the same request id on every try, so it counts once)
  const sessionId = session?.id;
  useEffect(() => {
    if (state.phase !== "finishing" || !sessionId || state.failed) return;
    const requestId = (finishId.current ??= newRequestId());
    let live = true;
    exercises
      .finish(sessionId, requestId, early.current)
      .then((result) => {
        if (!live) return;
        setActionError(null);
        dispatch({ type: "FINISHED", result });
      })
      .catch(async (cause: unknown) => {
        if (!live) return;
        if (cause instanceof ApiError && cause.status === 409) {
          // stopped or finished elsewhere: show what the server holds (a summary, or the stopped notice)
          try {
            const fresh = await exercises.get(sessionId);
            if (!live) return;
            setActionError(null);
            dispatch({ type: "LOADED", session: fresh });
            return;
          } catch {
            // the message below says the result was not saved
          }
        }
        if (!live) return;
        setActionError(errorCopy(cause, exerciseCopy.finishFailed));
        dispatch({ type: "FINISH_FAILED" });
      });
    return () => {
      live = false;
    };
  }, [state.phase, sessionId, state.failed]);

  // focus: each new question (or the summary) once, then "Verder" after a verdict
  const { phase, current } = state;
  useEffect(() => {
    if (phase === "feedback") {
      // a missed item may come straight back: it is a new question then, and gets the focus again
      shown.current = null;
      continueRef.current?.focus();
      return;
    }
    const target = phase === "summary" ? "summary" : phase === "answering" ? current : null;
    if (target && target !== shown.current) {
      shown.current = target;
      headingRef.current?.focus();
    }
  }, [phase, current]);

  async function send(answer: Answer | null, skip: SkipReason | null) {
    if (!session || !item || state.phase !== "answering" || busy.current) return;
    busy.current = true;
    const requestId = requestIdFor(state, item, answer, skip, newRequestId);
    dispatch({ type: "SUBMIT", pending: { itemId: item.id, requestId, answer, skip } });
    setActionError(null);
    setNudge(false);
    const timed = timeRoundTrip();
    try {
      const result = skip
        ? await exercises.skip(session.id, item.id, requestId, skip)
        : await exercises.answer(session.id, item.id, answer as Answer, requestId);
      timed();
      dispatch({ type: "ANSWERED", result });
      if (result.outcome === "correct") playTone("correct");
      else if (result.outcome === "almost") playTone("almost");
      const headline = outcomeCopy(result.outcome);
      if (headline) setAnnouncement({ id: nextAnnouncement(), text: headline });
    } catch (cause) {
      if (cause instanceof ApiError && cause.status === 409) {
        // the server already holds an answer for this item, or the session closed: carry on from what it holds
        try {
          const fresh = await exercises.get(session.id);
          setSelected(null);
          dispatch({ type: "LOADED", session: fresh });
          return;
        } catch {
          // the message below says the answer did not go through
        }
      }
      setActionError(errorCopy(cause, exerciseCopy.answerFailed));
      dispatch({ type: "ANSWER_FAILED" });
    } finally {
      busy.current = false;
    }
  }

  function check() {
    if (!selected) {
      setNudge(true);
      setAnnouncement({ id: nextAnnouncement(), text: exerciseCopy.chooseFirst });
      return;
    }
    void send({ option: selected }, null);
  }

  async function goOn() {
    if (busy.current) return; // the item coming back is still being fetched
    setSelected(null);
    setActionError(null);
    const coming = session?.items.find((entry) => entry.id === session.next_item_id);
    if (session && coming && coming.state === "open" && coming.attempts_left < FIRST_ATTEMPTS) {
      // a missed item comes back with its options reshuffled by the server: ask for the session as it is now
      busy.current = true;
      try {
        dispatch({ type: "LOADED", session: await exercises.get(session.id) });
        return;
      } catch {
        // shown in the order it had; nothing is lost
      } finally {
        busy.current = false;
      }
    }
    dispatch({ type: "CONTINUE" });
  }

  function finishNow() {
    setDialog(null);
    early.current = true;
    setActionError(null);
    dispatch({ type: "FINISH" });
  }

  function again() {
    finishId.current = null;
    early.current = false;
    shown.current = null;
    setSelected(null);
    setActionError(null);
    setLoadError(null);
    dispatch({ type: "RESET" });
    setCreateId(newRequestId());
  }

  // Escape anywhere asks to stop, unless a dialog (this screen's or another one's) is open and takes it
  const onKey = useEffectEvent((event: KeyboardEvent) => {
    if (event.key !== "Escape" || event.altKey || event.ctrlKey || event.metaKey) return;
    if (document.querySelector("dialog[open]")) return;
    if (state.phase === "answering" || state.phase === "feedback") {
      event.preventDefault();
      setDialog("exit");
    }
  });

  // the number keys and Enter only while focus is in the item, so they never take keys meant elsewhere
  function onStageKey(event: ReactKeyboardEvent<HTMLDivElement>) {
    if (event.altKey || event.ctrlKey || event.metaKey || event.nativeEvent.isComposing) return;
    if (state.phase !== "answering" || !item || !isChoicePrompt(item.prompt) || isTextEntry(event.target))
      return;
    const option = optionForKey(
      event.key,
      event.code,
      item.prompt.options.map((entry) => entry.id),
    );
    if (option) {
      event.preventDefault();
      setSelected(option);
      setNudge(false);
      // the focus ring and a screen reader follow the choice
      Array.from(event.currentTarget.querySelectorAll<HTMLInputElement>("input[type=radio]"))
        .find((input) => input.value === option)
        ?.focus();
    } else if (
      event.key === "Enter" &&
      !(event.target instanceof HTMLElement && event.target.closest("button, a[href]"))
    ) {
      event.preventDefault();
      check();
    }
  }
  useEffect(() => {
    const listener = (event: KeyboardEvent) => onKey(event);
    document.addEventListener("keydown", listener);
    return () => document.removeEventListener("keydown", listener);
  }, []);

  const loading = state.phase === "creating" || (state.phase === "error" && !loadError);
  return (
    <div className="exercise-session">
      <header className="exercise-frame">
        <h1 className="exercise-title">
          <UiText text={exerciseCopy.pageTitle} />
        </h1>
        {session && state.phase !== "summary" && (
          <div className="exercise-progress">
            <ProgressBar
              value={session.progress.closed}
              max={Math.max(session.progress.total, 1)}
              label={exerciseCopy.progressLabel.nl}
              size="thin"
            />
            <span className="exercise-progress-text">
              <UiText
                text={fill(exerciseCopy.progress, {
                  closed: session.progress.closed,
                  total: session.progress.total,
                })}
                inline
              />
            </span>
          </div>
        )}
        <div className="exercise-frame-actions">
          {session && <HonestyChip kind="unreviewed" />}
          {session &&
            (state.phase === "answering" || state.phase === "feedback" || state.phase === "checking") && (
              <Button variant="ghost" size="small" icon="close" onClick={() => setDialog("exit")}>
                <UiText text={exerciseCopy.exit} inline />
              </Button>
            )}
        </div>
      </header>

      <p className="visually-hidden" role="status" aria-live="polite">
        {announcement && (
          <span key={announcement.id}>
            <UiText text={announcement.text} inline />
          </span>
        )}
      </p>

      {loading && <SkeletonPanel label={exerciseCopy.loading.nl} />}

      {state.phase === "error" && loadError && (
        <Notice tone="warning" role="alert">
          <UiText text={loadError} tier="guide" />
          <div className="exercise-actions">
            <Button
              variant="secondary"
              icon="refresh"
              onClick={() => {
                setLoadError(null);
                setLoadTry((count) => count + 1);
              }}
            >
              <UiText text={uiCopy.action.retry} inline />
            </Button>
            <ButtonLink href="/" variant="ghost">
              <UiText text={exerciseCopy.backToday} inline />
            </ButtonLink>
          </div>
        </Notice>
      )}

      {session?.resumed && state.phase === "answering" && session.progress.closed > 0 && (
        <p className="exercise-resumed">
          <UiText text={exerciseCopy.resumed} tier="guide" />
        </p>
      )}

      {item && (state.phase === "answering" || state.phase === "checking" || state.phase === "feedback") && (
        <div className="exercise-stage" aria-busy={state.phase === "checking"} onKeyDown={onStageKey}>
          {item.prompt.kind === "intro" ? (
            <>
              <IntroCard words={item.prompt.words} headingRef={headingRef} />
              <div className="exercise-actions">
                <Button onClick={() => void send({ done: true }, null)} icon="arrow" iconEnd>
                  <UiText text={exerciseCopy.introDone} inline />
                </Button>
              </div>
            </>
          ) : isChoicePrompt(item.prompt) ? (
            <>
              <ChoiceItem
                key={`${item.id}:${item.attempts_left}`}
                prompt={item.prompt}
                selected={selected}
                onSelect={(option) => {
                  setSelected(option);
                  setNudge(false);
                }}
                feedback={state.phase === "feedback" ? (state.result?.feedback ?? null) : null}
                headingRef={headingRef}
              />
              {state.phase !== "feedback" && (
                <div className="exercise-actions">
                  <Button onClick={check} disabled={state.phase === "checking"} icon="check">
                    <UiText text={state.failed ? exerciseCopy.sendAgain : uiCopy.action.check} inline />
                  </Button>
                  <Button
                    variant="ghost"
                    onClick={() => void send(null, "unknown")}
                    disabled={state.phase === "checking"}
                  >
                    <UiText text={exerciseCopy.skip} inline />
                  </Button>
                  <span className="exercise-keys">
                    <UiText text={exerciseCopy.keysHint} tier="guide" />
                  </span>
                </div>
              )}
              {nudge && (
                <p className="exercise-nudge">
                  <UiText text={exerciseCopy.chooseFirst} inline />
                </p>
              )}
            </>
          ) : null}
          {state.phase === "feedback" && state.result && (
            <FeedbackBar
              result={state.result}
              onContinue={() => void goOn()}
              onReport={() => setDialog("report")}
              continueRef={continueRef}
            />
          )}
        </div>
      )}

      {actionError && state.phase !== "summary" && (
        <Notice tone="warning" role="alert">
          <UiText text={actionError} tier="guide" />
          {state.phase === "finishing" && state.failed && (
            <div className="exercise-actions">
              <Button
                variant="secondary"
                icon="refresh"
                onClick={() => {
                  setActionError(null);
                  dispatch({ type: "FINISH" });
                }}
              >
                <UiText text={uiCopy.action.retry} inline />
              </Button>
              <ButtonLink href="/" variant="ghost">
                <UiText text={exerciseCopy.backToday} inline />
              </ButtonLink>
            </div>
          )}
        </Notice>
      )}

      {state.phase === "finishing" && !state.failed && <SkeletonPanel label={exerciseCopy.loading.nl} />}

      {state.phase === "summary" && session?.summary && (
        <SessionSummary summary={session.summary} onAgain={again} headingRef={headingRef} />
      )}
      {state.phase === "summary" && session && !session.summary && (
        <Notice tone="info">
          <h2 className="exercise-question" tabIndex={-1} ref={headingRef}>
            <UiText text={exerciseCopy.stoppedElsewhere} tier="guide" />
          </h2>
          <div className="exercise-actions">
            <Button onClick={again} icon="repeat">
              <UiText text={exerciseCopy.again} inline />
            </Button>
            <ButtonLink href="/" variant="secondary">
              <UiText text={exerciseCopy.backToday} inline />
            </ButtonLink>
          </div>
        </Notice>
      )}

      {/* both dialogs stay mounted while there is a session, so closing one returns focus to its opener */}
      {session && (
        <Dialog
          open={dialog === "exit"}
          onClose={() => setDialog(null)}
          title={<UiText text={exerciseCopy.exitTitle} />}
          description={<UiText text={exerciseCopy.exitLead} tier="guide" />}
          closeLabel={uiCopy.action.close.nl}
          actions={
            <>
              <Button variant="secondary" onClick={finishNow}>
                <UiText text={exerciseCopy.exitFinish} inline />
              </Button>
              <ButtonLink href="/" variant="secondary">
                <UiText text={exerciseCopy.exitLater} inline />
              </ButtonLink>
              <Button onClick={() => setDialog(null)}>
                <UiText text={exerciseCopy.keepGoing} inline />
              </Button>
            </>
          }
        />
      )}
      {session && item && (
        <ReportDialog
          key={item.id}
          open={dialog === "report"}
          sessionId={session.id}
          itemId={item.id}
          kind={item.kind}
          onClose={() => setDialog(null)}
        />
      )}
    </div>
  );
}
