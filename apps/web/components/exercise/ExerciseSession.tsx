"use client";

import {
  useCallback,
  useEffect,
  useEffectEvent,
  useId,
  useReducer,
  useRef,
  useState,
  useSyncExternalStore,
  type KeyboardEvent as ReactKeyboardEvent,
} from "react";

import { Button, ButtonLink } from "@/components/ui/Button";
import { Dialog } from "@/components/ui/Dialog";
import { HonestyChip } from "@/components/ui/HonestyChip";
import { Notice } from "@/components/ui/Notice";
import { ProgressBar } from "@/components/ui/ProgressBar";
import { SkeletonPanel } from "@/components/ui/Skeleton";
import { UiText } from "@/components/ui/UiText";
import { AudioAssistanceProvider } from "@/components/AudioAssistance";
import { exerciseCopy } from "@/lib/copy/exercise";
import { ApiError, newRequestId } from "@/lib/client/api";
import { errorCopy } from "@/lib/client/error-copy";
import { isAbort } from "@/lib/client/errors";
import { isAudioRecording, subscribeAudioRecording } from "@/lib/client/audio-focus";
import {
  exercises,
  type Answer,
  type AnswerResult,
  type ItemView,
  type Summary,
} from "@/lib/client/exercises";
import { pickMimeType, type Recording } from "@/lib/client/recorder";
import { timeRoundTrip } from "@/lib/client/round-trips";
import { playTone } from "@/lib/client/tones";
import { fill, uiCopy, type Copy } from "@/lib/ui-copy";

import { ChoiceItem } from "./ChoiceItem";
import { ItemAudio } from "./ItemAudio";
import { ShadowItem } from "./ShadowItem";
import { TypedItem } from "./TypedItem";
import { MatchPairsItem } from "./MatchPairsItem";
import { OrderItem } from "./OrderItem";
import { SortBinsItem } from "./SortBinsItem";
import { TilesItem } from "./TilesItem";
import { FeedbackBar, outcomeCopy } from "./FeedbackBar";
import { IntroCard } from "./IntroCard";
import { HeadingLevel } from "./heading";
import { PassagePanel, PassageReview } from "./PassagePanel";
import {
  RENDERED_KINDS,
  hasSound,
  isChoicePrompt,
  isPassagePrompt,
  isTypedPrompt,
  optionForKey,
  passageAudioPath,
  passageRevealed,
  sessionRequest,
  type TopicActivity,
} from "./registry";
import { ReportDialog } from "./ReportDialog";
import { SessionSummary, type SessionExit } from "./SessionSummary";
import { currentItem, initialState, reduce, requestIdFor, type SkipReason } from "./sessionReducer";
import { ItemHeading } from "./heading";

/** What to say when "Controleer" is pressed too early: choose an option, type an answer, or finish the board. */
function nudgeFor(item: ItemView | null): Copy {
  if (item && isChoicePrompt(item.prompt)) return exerciseCopy.chooseFirst;
  if (item && isTypedPrompt(item.prompt)) return exerciseCopy.typeFirst;
  return exerciseCopy.finishFirst;
}

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

interface Common {
  /** Inside another page (a practice topic): no page title or honesty chip, Escape only within the session, and
   * the host's own way out in place of the links to Today. */
  embedded?: SessionExit;
  /** The level of the session's headings under the host's own (2 on a page of its own). */
  headingLevel?: 2 | 3 | 4 | 5;
  /** While a recording runs or the session is being closed: the host keeps the learner on the page. */
  onActivityChange?: (busy: boolean) => void;
  /** Once, when the session has its summary (also a finished session found again). */
  onFinished?: (summary: Summary) => void;
}

type Props =
  ({ source: "stage_skill" | "while_you_wait" } & Common) | ({ source: "topic" } & TopicActivity & Common);

/**
 * One practice session, start to summary, driven by the reducer in sessionReducer.ts. The server generates
 * and grades; this screen shows one item at a time, sends the answer, shows what it revealed, and moves on.
 * Keyboard, while focus is in the item: 1 to 4 choose an option (the number row's key on any layout, or a
 * Persian digit) and move focus to it, Enter checks it (on "Verder" it goes on); Escape asks to stop.
 * Focus moves to each new question, then to "Verder" after the verdict; a polite live region says the
 * outcome. Tones play only after the server's verdict, and never for a miss.
 */
export function ExerciseSession(props: Props) {
  const { source, embedded, headingLevel = 2, onActivityChange, onFinished } = props;
  // the activity as primitives, so the create effect sees no new object on every render
  const stageId = props.source === "topic" ? props.stageId : undefined;
  const topicId = props.source === "topic" ? props.topicId : undefined;
  const skill = props.source === "topic" ? props.skill : undefined;
  const receptiveTopic = skill === "reading" || skill === "listening";
  const warmUp = skill === "speaking" || skill === "writing";
  const [state, dispatch] = useReducer(reduce, initialState);
  // minted once, so a second effect run (or a retry) asks for the same session and the API replays it
  const [createId, setCreateId] = useState(() => newRequestId());
  // a topic's short session on the questions its last session missed
  const [retry, setRetry] = useState(false);
  const [loadTry, setLoadTry] = useState(0);
  const [loadError, setLoadError] = useState<Copy | null>(null);
  const [loadCode, setLoadCode] = useState("");
  // the answer as it stands: an option, or a whole board once every part is in place (null before)
  const [draft, setDraft] = useState<Answer | null>(null);
  const [actionError, setActionError] = useState<Copy | null>(null);
  const [nudge, setNudge] = useState(false);
  const [dialog, setDialog] = useState<"exit" | "report" | null>(null);
  const [announcement, setAnnouncement] = useState<{ id: number; text: Copy } | null>(null);
  const verdictId = useId();
  const headingRef = useRef<HTMLHeadingElement>(null);
  const continueRef = useRef<HTMLButtonElement>(null);
  const busy = useRef(false);
  const finishId = useRef<string | null>(null);
  const early = useRef(false);
  const shown = useRef<string | null>(null);
  // the item whose hint the learner asked for (reported with that item's answer only)
  const hinted = useRef<string | null>(null);
  const assistedPassages = useRef(new Set<string>());
  // one request id per overruled item, so a retried "mijn antwoord klopt ook" replays
  const overrideIds = useRef<Record<string, string>>({});

  const session = state.session;
  const item = currentItem(state);

  useEffect(() => {
    let live = true;
    // a browser that cannot record is not given shadowing at all (the same list on every try of this id)
    const kinds =
      pickMimeType() !== null ? RENDERED_KINDS : RENDERED_KINDS.filter((kind) => kind !== "shadow");
    const activity = source === "topic" && stageId && topicId && skill ? { stageId, topicId, skill } : null;
    exercises
      .create(sessionRequest(source, activity, retry, kinds), createId)
      .then((created) => {
        if (live) dispatch({ type: "LOADED", session: created });
      })
      .catch((cause: unknown) => {
        if (!live || isAbort(cause)) return;
        // a warm-up that cannot be made sends the learner on to the task
        const notReady =
          skill === "speaking" || skill === "writing" ? exerciseCopy.warmUpNotReady : exerciseCopy.notReady;
        setLoadError(errorCopy(cause, exerciseCopy.loadFailed, { not_ready: notReady }, "load"));
        setLoadCode(cause instanceof ApiError ? cause.code : "");
        dispatch({ type: "LOAD_FAILED" });
      });
    return () => {
      live = false;
    };
  }, [source, stageId, topicId, skill, retry, createId, loadTry]);

  // a recording, or the session being closed: the host keeps the learner on the page meanwhile (an answer on its
  // way is safe to leave: the server keeps it)
  const recording = useSyncExternalStore(subscribeAudioRecording, isAudioRecording, () => false);
  const active = recording || (state.phase === "finishing" && !state.failed);
  const reportActivity = useEffectEvent((busy: boolean) => onActivityChange?.(busy));
  useEffect(() => {
    reportActivity(active);
  }, [active]);
  useEffect(() => () => reportActivity(false), []);

  // the summary, once per session (a finished session found again counts too)
  const reported = useRef<string | null>(null);
  const reportFinished = useEffectEvent((id: string, summary: Summary) => {
    if (reported.current === id) return;
    reported.current = id;
    onFinished?.(summary);
  });
  useEffect(() => {
    if (state.finished) reportFinished(state.finished.id, state.finished.summary);
  }, [state.finished]);

  // the last item answered: close the session (the same request id on every try, so it counts once)
  const sessionId = session?.id;
  // In a reading or listening topic the last verdict already ends the session, so its finish goes out with it
  // (under the id "Verder" sends again): the first answers count even when the learner leaves before "Verder".
  // A failure here says nothing; "Verder" sends it again and shows its own.
  const lastVerdict =
    receptiveTopic && state.phase === "feedback" && session?.status === "active" && !session.next_item_id;
  useEffect(() => {
    if (!lastVerdict || !sessionId) return;
    const requestId = (finishId.current ??= newRequestId());
    exercises
      .finish(sessionId, requestId, false)
      .then((result) => reportFinished(result.id, result.summary))
      .catch(() => {});
  }, [lastVerdict, sessionId]);
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

  /**
   * Sends an answer, a skip or a recording, and shows the verdict. `call` makes the request under the given id;
   * a recording is always a new take (`fresh`), an answer sent again after a failure keeps its id.
   */
  async function deliver(
    answer: Answer | null,
    skip: SkipReason | null,
    call: (sessionId: string, itemId: string, requestId: string) => Promise<AnswerResult>,
    failed: Copy,
    fresh = false,
  ) {
    if (!session || !item || state.phase !== "answering" || busy.current) return;
    busy.current = true;
    const requestId = fresh ? newRequestId() : requestIdFor(state, item, answer, skip, newRequestId);
    dispatch({ type: "SUBMIT", pending: { itemId: item.id, requestId, answer, skip } });
    setActionError(null);
    setNudge(false);
    const timed = timeRoundTrip();
    try {
      const result = await call(session.id, item.id, requestId);
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
          setDraft(null);
          dispatch({ type: "LOADED", session: fresh });
          return;
        } catch {
          // the message below says the answer did not go through
        }
      }
      setActionError(errorCopy(cause, failed));
      dispatch({ type: "ANSWER_FAILED" });
    } finally {
      busy.current = false;
    }
  }

  function send(answer: Answer | null, skip: SkipReason | null) {
    return deliver(
      answer,
      skip,
      (sessionId, itemId, requestId) =>
        skip
          ? exercises.skip(sessionId, itemId, requestId, skip)
          : exercises.answer(
              sessionId,
              itemId,
              answer as Answer,
              requestId,
              hinted.current === itemId ||
                assistedPassages.current.has(sessionId) ||
                Boolean(
                  session?.items.some(
                    (entry) => (entry.id === itemId || entry.kind === "read_passage") && entry.hint_used,
                  ),
                ),
            ),
      exerciseCopy.answerFailed,
    );
  }

  async function recordOptionalAudio(viewId: string, passageSupport: boolean, signal: AbortSignal) {
    if (!session || session.status !== "active") return;
    if (
      passageSupport
        ? !["answering", "checking", "feedback"].includes(state.phase)
        : state.phase !== "answering"
    )
      return;
    try {
      const saved = await exercises.assistance(session.id, viewId, signal);
      if (!saved.hint_used) throw new Error("support");
      if (passageSupport) assistedPassages.current.add(session.id);
      else hinted.current = viewId;
    } catch {
      throw new Error("support");
    }
  }

  function sendRecording(recording: Recording) {
    return deliver(
      null,
      null,
      (sessionId, itemId, requestId) =>
        exercises.record(sessionId, itemId, requestId, recording.blob, recording.fileName),
      exerciseCopy.recordSendFailed,
      true,
    );
  }

  /** "Mijn antwoord klopt ook": the learner overrules the check of a typed answer or a built sentence. */
  async function overrule() {
    if (!session || !state.result || busy.current) return;
    const itemId = state.result.item_id;
    const requestId = (overrideIds.current[itemId] ??= newRequestId());
    busy.current = true;
    setActionError(null);
    try {
      const result = await exercises.override(session.id, itemId, requestId);
      // the override button goes with the verdict: focus moves on to "Verder", which stays
      continueRef.current?.focus();
      dispatch({ type: "OVERRIDDEN", result });
      setAnnouncement({ id: nextAnnouncement(), text: exerciseCopy.accepted });
    } catch (cause) {
      setActionError(errorCopy(cause, exerciseCopy.overrideFailed));
    } finally {
      busy.current = false;
    }
  }

  const onDraft = useCallback((answer: Answer | null) => {
    setDraft(answer);
    setNudge(false);
  }, []);

  function check() {
    if (!draft) {
      setNudge(true);
      setAnnouncement({ id: nextAnnouncement(), text: nudgeFor(item) });
      return;
    }
    void send(draft, null);
  }

  async function goOn() {
    if (busy.current) return; // the item coming back is still being fetched
    setDraft(null);
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

  /** A new session: all the questions again, or (a topic's) only those the last session missed. */
  function restart(nextRetry: boolean) {
    finishId.current = null;
    early.current = false;
    shown.current = null;
    hinted.current = null;
    assistedPassages.current.clear();
    overrideIds.current = {};
    setDraft(null);
    setActionError(null);
    setLoadError(null);
    setLoadCode("");
    dispatch({ type: "RESET" });
    setRetry(nextRetry);
    setCreateId(newRequestId());
  }
  const again = () => restart(false);
  const retryMissed = () => restart(true);

  /** Escape asks to stop, unless a dialog (this screen's or another one's) is open and takes it. */
  function askToStop(
    event: Pick<KeyboardEvent, "key" | "altKey" | "ctrlKey" | "metaKey" | "preventDefault">,
  ) {
    if (event.key !== "Escape" || event.altKey || event.ctrlKey || event.metaKey) return;
    if (document.querySelector("dialog[open]")) return;
    if (state.phase === "answering" || state.phase === "feedback") {
      event.preventDefault();
      setDialog("exit");
    }
  }
  // on a page of its own Escape anywhere asks; inside another page only Escape within the session does
  const onKey = useEffectEvent((event: KeyboardEvent) => askToStop(event));
  const isEmbedded = embedded !== undefined;

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
      onDraft({ option });
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
  // Inside a topic the button that started the session has gone: a session that cannot start takes the focus,
  // so the way on is next to it. On a page of its own the load runs with the page and focus is at the top.
  const errorRef = useRef<HTMLDivElement>(null);
  const loadFailed = state.phase === "error" && loadError !== null;
  useEffect(() => {
    if (isEmbedded && loadFailed) errorRef.current?.focus();
  }, [isEmbedded, loadFailed]);
  useEffect(() => {
    if (isEmbedded) return;
    const listener = (event: KeyboardEvent) => onKey(event);
    document.addEventListener("keydown", listener);
    return () => document.removeEventListener("keydown", listener);
  }, [isEmbedded]);

  /** The way out: the host's (a practice topic's) or back to Today. */
  function exitButton(variant: "secondary" | "ghost") {
    return embedded ? (
      <Button
        variant={variant}
        onClick={() => {
          setDialog(null);
          embedded.onExit();
        }}
      >
        <UiText text={embedded.label} inline />
      </Button>
    ) : (
      <ButtonLink href="/" variant={variant}>
        <UiText text={exerciseCopy.backToday} inline />
      </ButtonLink>
    );
  }

  // a topic's passage: one panel from its own step through every question, then read again in the summary
  const passageItem = session?.items.find((entry) => isPassagePrompt(entry.prompt)) ?? null;
  const passage = passageItem && isPassagePrompt(passageItem.prompt) ? passageItem.prompt : null;
  const onPassage = passageItem !== null && item?.id === passageItem.id;
  const needsReveal = state.phase === "summary" && passage !== null && !passageRevealed(passage);
  useEffect(() => {
    if (!needsReveal || !sessionId) return;
    let live = true;
    exercises
      .get(sessionId)
      .then((fresh) => {
        if (live) dispatch({ type: "REVEALED", session: fresh });
      })
      .catch(() => {
        // the summary shows the Dutch only
      });
    return () => {
      live = false;
    };
  }, [needsReveal, sessionId]);

  /** The item's own renderer: a fresh one for each asking of a question (a question that comes straight back
   * starts again from the server's reshuffled prompt) and another for its verdict. */
  function renderItem(view: ItemView) {
    const feedback = state.phase === "feedback" ? (state.result?.feedback ?? null) : null;
    const key = `${view.id}:${view.attempts_left}:${state.phase === "feedback" ? "verdict" : "ask"}`;
    const prompt = view.prompt;
    switch (prompt.kind) {
      case "match_pairs":
        return (
          <MatchPairsItem
            key={key}
            prompt={prompt}
            feedback={feedback}
            onDraft={onDraft}
            headingRef={headingRef}
          />
        );
      case "de_het":
        return (
          <SortBinsItem
            key={key}
            prompt={prompt}
            feedback={feedback}
            onDraft={onDraft}
            headingRef={headingRef}
          />
        );
      case "sentence_builder":
        return (
          <TilesItem
            key={key}
            prompt={prompt}
            feedback={feedback}
            onDraft={onDraft}
            headingRef={headingRef}
          />
        );
      case "cloze_typed":
      case "typed_recall":
      case "dictation":
        return (
          <TypedItem
            key={key}
            prompt={prompt}
            sessionId={session?.id ?? ""}
            itemId={view.id}
            feedback={feedback}
            onDraft={onDraft}
            onHint={() => {
              hinted.current = view.id;
            }}
            onSubmit={check}
            headingRef={headingRef}
            verdictId={verdictId}
          />
        );
      case "shadow":
        return (
          <ShadowItem
            key={key}
            prompt={prompt}
            sessionId={session?.id ?? ""}
            itemId={view.id}
            feedback={feedback}
            busy={state.phase === "checking"}
            onRecording={(recording) => void sendRecording(recording)}
            headingRef={headingRef}
            verdictId={verdictId}
          />
        );
      case "sentence_order":
        return (
          <OrderItem
            key={key}
            prompt={prompt}
            feedback={feedback}
            onDraft={onDraft}
            headingRef={headingRef}
          />
        );
      default:
        return isChoicePrompt(prompt) ? (
          <ChoiceItem
            key={key}
            prompt={prompt}
            selected={draft && "option" in draft ? draft.option : null}
            onSelect={(option) => onDraft({ option })}
            feedback={feedback}
            headingRef={headingRef}
            audio={
              prompt.kind === "listen_choose" ? (
                <ItemAudio sessionId={session?.id ?? ""} itemId={view.id} />
              ) : undefined
            }
          />
        ) : null;
    }
  }

  const loading = state.phase === "creating" || (state.phase === "error" && !loadError);
  const asking = state.phase === "answering" || state.phase === "checking" || state.phase === "feedback";
  return (
    <HeadingLevel value={headingLevel}>
      <div
        className="exercise-session"
        data-embedded={isEmbedded ? "" : undefined}
        onKeyDown={isEmbedded ? (event) => askToStop(event) : undefined}
      >
        <header className="exercise-frame">
          {!isEmbedded && (
            <h1 className="exercise-title">
              <UiText text={exerciseCopy.pageTitle} />
            </h1>
          )}
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
            {/* inside a topic, the page's own chip says it */}
            {session && !isEmbedded && <HonestyChip kind="unreviewed" />}
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
          <Notice
            tone="warning"
            role="alert"
            ref={errorRef}
            tabIndex={isEmbedded ? -1 : undefined}
            className={isEmbedded ? "exercise-load-error" : undefined}
          >
            <UiText text={loadError} tier="guide" />
            <div className="exercise-actions">
              {loadCode === "nothing_to_retry" ? (
                // nothing missed is left: all the questions again is the way on
                <Button variant="secondary" icon="repeat" onClick={again}>
                  <UiText text={exerciseCopy.againAll} inline />
                </Button>
              ) : (
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
              )}
              {exitButton("ghost")}
            </div>
          </Notice>
        )}

        {session?.resumed && state.phase === "answering" && session.progress.closed > 0 && (
          <p className="exercise-resumed">
            <UiText text={exerciseCopy.resumed} tier="guide" />
          </p>
        )}

        {session && passage && asking && (
          <AudioAssistanceProvider
            onRequest={(signal) =>
              recordOptionalAudio(passageItem!.id, passage.kind === "read_passage", signal)
            }
          >
            <PassagePanel
              prompt={passage}
              mode={onPassage ? "step" : "reference"}
              audioPath={passageAudioPath(session)}
              headingRef={onPassage ? headingRef : undefined}
            />
          </AudioAssistanceProvider>
        )}

        {item && asking && (
          <div className="exercise-stage" aria-busy={state.phase === "checking"} onKeyDown={onStageKey}>
            {isPassagePrompt(item.prompt) ? (
              // the passage is above: read or heard, it leads on to the questions
              <div className="exercise-actions">
                <Button
                  onClick={() => void send({ done: true }, null)}
                  disabled={state.phase === "checking"}
                  icon="arrow"
                  iconEnd
                >
                  <UiText text={exerciseCopy.passageDone} inline />
                </Button>
                {item.prompt.kind === "listen_passage" && (
                  <Button
                    variant="ghost"
                    onClick={() => void send(null, "no_audio")}
                    disabled={state.phase === "checking"}
                  >
                    <UiText text={exerciseCopy.cannotListen} inline />
                  </Button>
                )}
              </div>
            ) : item.prompt.kind === "intro" ? (
              <>
                <IntroCard words={item.prompt.words} headingRef={headingRef} />
                <div className="exercise-actions">
                  <Button onClick={() => void send({ done: true }, null)} icon="arrow" iconEnd>
                    <UiText text={exerciseCopy.introDone} inline />
                  </Button>
                </div>
              </>
            ) : (
              <>
                <AudioAssistanceProvider onRequest={(signal) => recordOptionalAudio(item.id, false, signal)}>
                  {renderItem(item)}
                </AudioAssistanceProvider>
                {state.phase !== "feedback" && (
                  <div className="exercise-actions">
                    {/* shadowing is answered by its recording */}
                    {item.prompt.kind !== "shadow" && (
                      <Button onClick={check} disabled={state.phase === "checking"} icon="check">
                        <UiText text={state.failed ? exerciseCopy.sendAgain : uiCopy.action.check} inline />
                      </Button>
                    )}
                    <Button
                      variant="ghost"
                      onClick={() => void send(null, "unknown")}
                      disabled={state.phase === "checking"}
                    >
                      <UiText text={exerciseCopy.skip} inline />
                    </Button>
                    {/* a sound that will not play or a microphone that does not work is never a miss */}
                    {hasSound(item.kind) && (
                      <Button
                        variant="ghost"
                        onClick={() => void send(null, "no_audio")}
                        disabled={state.phase === "checking"}
                      >
                        <UiText text={exerciseCopy.cannotListen} inline />
                      </Button>
                    )}
                    {item.prompt.kind === "shadow" && (
                      <Button
                        variant="ghost"
                        onClick={() => void send(null, "no_microphone")}
                        disabled={state.phase === "checking"}
                      >
                        <UiText text={exerciseCopy.cannotSpeak} inline />
                      </Button>
                    )}
                    {isChoicePrompt(item.prompt) && (
                      <span className="exercise-keys">
                        <UiText text={exerciseCopy.keysHint} tier="guide" />
                      </span>
                    )}
                  </div>
                )}
                {nudge && (
                  <p className="exercise-nudge">
                    <UiText text={nudgeFor(item)} inline />
                  </p>
                )}
              </>
            )}
            {state.phase === "feedback" && state.result && (
              <FeedbackBar
                result={state.result}
                onContinue={() => void goOn()}
                onReport={() => setDialog("report")}
                onOverride={
                  state.result.feedback.overridable && state.result.outcome !== "accepted"
                    ? () => void overrule()
                    : undefined
                }
                continueRef={continueRef}
                describedBy={verdictId}
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
                {exitButton("ghost")}
              </div>
            )}
          </Notice>
        )}

        {state.phase === "finishing" && !state.failed && <SkeletonPanel label={exerciseCopy.loading.nl} />}

        {state.phase === "summary" && session?.summary && (
          <SessionSummary
            summary={session.summary}
            onAgain={again}
            onRetry={receptiveTopic ? retryMissed : undefined}
            exit={embedded}
            headingRef={headingRef}
          >
            {passage && <PassageReview prompt={passage} audioPath={passageAudioPath(session)} />}
          </SessionSummary>
        )}
        {state.phase === "summary" && session && !session.summary && (
          <Notice tone="info">
            <ItemHeading className="exercise-question" tabIndex={-1} ref={headingRef}>
              <UiText text={exerciseCopy.stoppedElsewhere} tier="guide" />
            </ItemHeading>
            <div className="exercise-actions">
              <Button onClick={again} icon="repeat">
                <UiText text={exerciseCopy.again} inline />
              </Button>
              {exitButton("secondary")}
            </div>
          </Notice>
        )}

        {/* both dialogs stay mounted while there is a session, so closing one returns focus to its opener */}
        {session && (
          <Dialog
            open={dialog === "exit"}
            onClose={() => setDialog(null)}
            title={<UiText text={exerciseCopy.exitTitle} />}
            description={
              <UiText
                text={
                  !isEmbedded
                    ? exerciseCopy.exitLead
                    : warmUp
                      ? exerciseCopy.exitLeadWarmUp
                      : retry
                        ? exerciseCopy.exitLeadRetry
                        : exerciseCopy.exitLeadActivity
                }
                tier="guide"
              />
            }
            closeLabel={uiCopy.action.close.nl}
            actions={
              <>
                <Button variant="secondary" onClick={finishNow}>
                  <UiText text={exerciseCopy.exitFinish} inline />
                </Button>
                {isEmbedded ? (
                  exitButton("secondary")
                ) : (
                  <ButtonLink href="/" variant="secondary">
                    <UiText text={exerciseCopy.exitLater} inline />
                  </ButtonLink>
                )}
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
    </HeadingLevel>
  );
}
