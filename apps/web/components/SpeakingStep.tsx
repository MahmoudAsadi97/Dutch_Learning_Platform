"use client";

import { useEffect, useRef, useState } from "react";

import { LearningText } from "@/components/LanguageSupport";
import { ContentLabel } from "@/components/ContentLabel";
import { FeedbackPanel } from "@/components/FeedbackPanel";
import { HelpLadder } from "@/components/HelpLadder";
import { UiText } from "@/components/ui/UiText";
import { ApiError, apiFetch, apiJson, newRequestId } from "@/lib/client/api";
import { errorCopy } from "@/lib/client/error-copy";
import { useDeveloperDetails } from "@/components/shell/EnvContext";
import { usePlayback } from "@/lib/client/playback";
import { recordHelp } from "@/lib/client/practice";
import { type Recording, talkButtonHandlers, useRecorder } from "@/lib/client/recorder";
import { missionsCopy } from "@/lib/copy/missions";
import type {
  CheckpointPayload,
  ConversationStepInfo,
  HelpRung,
  SessionDetail,
  SpeakingPayload,
  Step,
  TurnResponse,
  TurnView,
} from "@/lib/types";
import { fill, uiCopy, type Copy } from "@/lib/ui-copy";

interface Props {
  step: Step & { payload: SpeakingPayload | CheckpointPayload };
  labels: { unreviewed_nl: string; unreviewed_fa: string };
  detail: SessionDetail | null;
  starting: boolean;
  onStart: () => void;
  /** Closes the current session of this variant and starts a fresh one (practice steps only). */
  onRestart?: () => void;
  onDetail: (detail: SessionDetail) => void;
  onProgressChanged: () => void;
}

type Pending = { requestId: string; modality: "speech" | "typed"; text?: string; recording?: Recording };
type SendState =
  | { kind: "idle" }
  | { kind: "sending"; pending: Pending }
  | { kind: "failed"; pending: Pending; message: Copy; sameRequestId: boolean };

const DAY_NAMES_NL = ["zondag", "maandag", "dinsdag", "woensdag", "donderdag", "vrijdag", "zaterdag"];
const MONTH_NAMES_NL = [
  "januari",
  "februari",
  "maart",
  "april",
  "mei",
  "juni",
  "juli",
  "augustus",
  "september",
  "oktober",
  "november",
  "december",
];

export function describeSlot(info: ConversationStepInfo | undefined, slotId: string | undefined): string {
  const slot = info?.slots.find((s) => s.id === slotId);
  if (!slot) return slotId ?? "";
  const [year, month, day] = slot.day.split("-").map(Number);
  const date = new Date(Date.UTC(year, month - 1, day));
  const [hour, minute] = slot.start.split(":");
  const time = minute === "00" ? `${Number(hour)} uur` : `${Number(hour)}.${minute} uur`;
  return `${DAY_NAMES_NL[date.getUTCDay()]} ${day} ${MONTH_NAMES_NL[month - 1]} om ${time}`;
}

const ACTION_LABEL: Record<string, Copy> = {
  state_need: missionsCopy.actionStateNeed,
  choose_option: missionsCopy.actionChooseOption,
  state_reason: missionsCopy.actionStateReason,
  accept_slot: missionsCopy.actionAcceptSlot,
  confirm: missionsCopy.actionConfirm,
  propose_slot: missionsCopy.actionProposeSlot,
  ask_repeat: missionsCopy.actionAskRepeat,
  cancel: missionsCopy.actionCancel,
  none: missionsCopy.actionNone,
};

/** The label of a conversation action; an action this screen does not know yet shows its code. */
function ActionLabel({ action }: { action: string }) {
  const label = ACTION_LABEL[action];
  return label ? <UiText text={label} inline /> : <>{action}</>;
}

/**
 * The speaking step and the checkpoint: a push-to-talk conversation with the character.
 * Every learner turn is sent with its own request id; a retry after a network failure reuses that id,
 * so the server answers from the stored turn instead of running the model twice.
 */
export function SpeakingStep({
  step,
  labels,
  detail,
  starting,
  onStart,
  onRestart,
  onDetail,
  onProgressChanged,
}: Props) {
  const payload = step.payload;
  const checkpoint = payload.type === "checkpoint";
  const info = detail?.conversation.find((c) => c.step_key === step.key);
  const session = detail?.session ?? null;
  const turns = (detail?.turns ?? []).filter((t) => t.step_key === step.key);
  const progress = session?.step_progress[step.key];
  const appointment = session?.appointment ?? {};
  const typedAllowed = info?.typed_allowed ?? (checkpoint ? false : payload.typed_fallback_allowed);
  const helpAllowed = info?.help_allowed ?? !checkpoint;
  const helpRungs = checkpoint ? [] : payload.help;
  const maxTurns = info?.max_turns ?? payload.max_turns;
  const completed = progress?.completed ?? false;
  const typedOnly = completed && !(progress?.modalities ?? []).includes("speech");
  const sessionOpen = session?.status === "active";
  const turnsLeft = Math.max(0, maxTurns - (progress?.turns ?? 0));

  const [send, setSend] = useState<SendState>({ kind: "idle" });
  const [typedText, setTypedText] = useState("");
  const [audioLabel, setAudioLabel] = useState<string>("");
  const developer = useDeveloperDetails();
  const [audioNotice, setAudioNotice] = useState<Copy | null>(null);
  const [playingTurnId, setPlayingTurnId] = useState<string>("");
  const abortRef = useRef<AbortController | null>(null);
  const listRef = useRef<HTMLOListElement | null>(null);
  const playback = usePlayback();

  useEffect(() => {
    return () => {
      abortRef.current?.abort();
    };
  }, []);

  useEffect(() => {
    const list = listRef.current;
    if (list) list.scrollTop = list.scrollHeight;
  }, [turns.length, send.kind]);

  const canSend = Boolean(
    session && sessionOpen && info && !completed && send.kind !== "sending" && turnsLeft > 0,
  );

  async function submit(pending: Pending) {
    if (!session) return;
    setSend({ kind: "sending", pending });
    const controller = new AbortController();
    abortRef.current = controller;
    try {
      let response: TurnResponse;
      if (pending.modality === "typed") {
        response = await apiJson<TurnResponse>(`practice/sessions/${session.id}/turns`, {
          method: "POST",
          body: { step_key: step.key, text: pending.text ?? "" },
          requestId: pending.requestId,
          signal: controller.signal,
        });
      } else {
        const form = new FormData();
        form.append("audio", pending.recording!.blob, pending.recording!.fileName);
        form.append("step_key", step.key);
        response = await apiJson<TurnResponse>(`practice/sessions/${session.id}/turns/speech`, {
          method: "POST",
          formData: form,
          requestId: pending.requestId,
          signal: controller.signal,
        });
      }
      applyTurn(response);
      setSend({ kind: "idle" });
      if (pending.modality === "typed") setTypedText("");
      void playCharacterAudio(response.turn);
    } catch (cause) {
      if (controller.signal.aborted) {
        // The request may still have completed on the server: reconcile from the stored session.
        await reload();
        setSend({ kind: "idle" });
        return;
      }
      if (cause instanceof ApiError) {
        // 502: the model did not answer and the turn is recorded as failed; a retry needs a new request id.
        // Anything else that is not retryable (403, 409, 422) is shown; the learner changes the input.
        const retryWithSameId = cause.status >= 500 && cause.status !== 502;
        // the answer stays for a retry; a recording the speech service heard nothing in is not a typing mistake
        const message = errorCopy(
          cause,
          missionsCopy.turnNotProcessed,
          {
            502: missionsCopy.turnNotProcessed,
            ...(pending.modality === "typed" ? {} : { 422: missionsCopy.nothingHeard }),
          },
          "input",
        );
        setSend({ kind: "failed", pending, message, sameRequestId: retryWithSameId });
        if (cause.status === 502) await reload();
      } else {
        setSend({
          kind: "failed",
          pending,
          message: errorCopy(cause, undefined, undefined, "input"),
          sameRequestId: true,
        });
      }
    } finally {
      abortRef.current = null;
    }
  }

  function applyTurn(response: TurnResponse) {
    if (!detail) return;
    const others = detail.turns.filter((t) => t.id !== response.turn.id);
    onDetail({
      ...detail,
      session: response.session,
      turns: [...others, response.turn].sort((a, b) => a.turn_index - b.turn_index),
    });
    onProgressChanged();
  }

  async function reload() {
    if (!session) return;
    try {
      onDetail(await apiJson<SessionDetail>(`practice/sessions/${session.id}`));
      onProgressChanged();
    } catch {
      // the next successful call refreshes the view
    }
  }

  const recorder = useRecorder(
    (recording) => void submit({ requestId: newRequestId(), modality: "speech", recording }),
  );

  function retry() {
    if (send.kind !== "failed") return;
    const pending = send.sameRequestId ? send.pending : { ...send.pending, requestId: newRequestId() };
    void submit(pending);
  }

  function cancel() {
    abortRef.current?.abort();
  }

  async function recordHelpUse(rung: HelpRung) {
    if (!detail) throw new Error("Start a session before requesting help.");
    onDetail(await recordHelp(detail, step.key, rung));
  }

  async function playCharacterAudio(turn: TurnView) {
    if (!session || !turn.character_audio_asset_id) {
      if (turn.audio_error) setAudioNotice(missionsCopy.audioMissing);
      return;
    }
    setAudioNotice(null);
    try {
      const response = await apiFetch(`practice/sessions/${session.id}/turns/${turn.id}/audio`);
      if (!response.ok) throw new Error(`audio ${response.status}`);
      setAudioLabel(response.headers.get("x-audio-label") ?? "unknown");
      const wav = await response.blob();
      setPlayingTurnId(turn.id);
      const outcome = await playback.play(wav, () =>
        setPlayingTurnId((current) => (current === turn.id ? "" : current)),
      );
      if (outcome.failed) {
        setPlayingTurnId("");
        setAudioNotice(missionsCopy.replyPlaybackFailed);
      } else if (outcome.blocked) {
        setPlayingTurnId("");
        setAudioNotice(missionsCopy.replyPlaybackBlocked);
      }
    } catch {
      setPlayingTurnId("");
      setAudioNotice(missionsCopy.replyPlaybackFailed);
    }
  }

  const stepStatus: Copy = !session
    ? missionsCopy.statusNoSession
    : session.status === "completed"
      ? missionsCopy.statusCheckDone
      : session.status === "ended"
        ? missionsCopy.statusEnded
        : session.status === "abandoned"
          ? missionsCopy.statusAbandoned
          : completed
            ? typedOnly
              ? missionsCopy.statusTypedOnly
              : missionsCopy.statusGoalReached
            : fill(missionsCopy.statusTurnsLeft, { left: turnsLeft, max: maxTurns });

  return (
    <article aria-labelledby="step-title" data-step={step.key} data-step-type={payload.type}>
      <header>
        <h2 id="step-title">
          <LearningText text={step.title} />
        </h2>
        <p>
          <ContentLabel
            status={step.instructions.review_status}
            labelNl={labels.unreviewed_nl}
            labelFa={labels.unreviewed_fa}
          />
        </p>
        <p>
          <LearningText text={step.instructions} />
        </p>
        {checkpoint && (
          <p>
            <span className="label warn" data-testid="checkpoint-rules">
              <UiText text={missionsCopy.checkpointRules} inline />
            </span>
          </p>
        )}
      </header>

      <section className="card" aria-labelledby="goal-heading">
        <h3 id="goal-heading">
          <UiText text={missionsCopy.goalTitle} />
        </h3>
        <p>
          <ContentLabel
            status={payload.goal.review_status}
            labelNl={labels.unreviewed_nl}
            labelFa={labels.unreviewed_fa}
          />
        </p>
        <p>
          <LearningText text={payload.goal} />
        </p>
      </section>

      {!session ? (
        <section className="card">
          <p>
            <UiText
              text={
                info?.character.name
                  ? fill(missionsCopy.startCallWith, { name: info.character.name })
                  : missionsCopy.startCallDefault
              }
              tier="guide"
            />
          </p>
          <button
            type="button"
            className="button"
            onClick={onStart}
            disabled={starting}
            data-testid="start-conversation"
          >
            <UiText
              text={
                starting
                  ? missionsCopy.busy
                  : checkpoint
                    ? missionsCopy.startCheck
                    : missionsCopy.startConversation
              }
              inline
            />
          </button>
        </section>
      ) : (
        <div className="grid two">
          <section className="card" aria-labelledby="conversation-heading">
            <h3 id="conversation-heading">
              <UiText text={fill(missionsCopy.conversationWith, { name: info?.character.name ?? "" })} />
              {info && (
                <span className="muted" style={{ fontWeight: 400, fontSize: "0.85rem" }}>
                  {" "}
                  · {info.character.role.nl}
                </span>
              )}
            </h3>
            <ol className="conversation" ref={listRef} data-testid="conversation" aria-live="polite">
              <li className="bubble character" data-testid="turn-character" data-source="fixed_line">
                <span className="who">{info?.character.name}</span>
                <span lang="nl">{info?.opening_line}</span>
              </li>
              {turns.map((turn) => (
                <TurnBubbles
                  key={turn.id}
                  turn={turn}
                  characterName={info?.character.name ?? ""}
                  playing={playingTurnId === turn.id}
                  onPlay={() => void playCharacterAudio(turn)}
                />
              ))}
              {send.kind === "sending" && (
                <li className="bubble learner pending" data-testid="turn-pending">
                  <span className="who">
                    <UiText text={missionsCopy.you} inline />
                  </span>
                  <span lang="nl">
                    {send.pending.text ?? <UiText text={missionsCopy.recordingPlaceholder} inline />}
                  </span>
                  <span className="muted" style={{ display: "block", fontSize: "0.8rem" }}>
                    <UiText
                      text={
                        send.pending.modality === "speech"
                          ? missionsCopy.pendingSpeech
                          : missionsCopy.pendingTyped
                      }
                      inline
                    />
                  </span>
                </li>
              )}
            </ol>
            {send.kind === "sending" && (
              <p>
                <button type="button" className="button secondary" onClick={cancel} data-testid="cancel-turn">
                  <UiText text={missionsCopy.cancel} inline />
                </button>
              </p>
            )}
            {send.kind === "failed" && (
              <div role="alert" data-testid="turn-error">
                <p className="error">
                  <UiText text={send.message} tier="guide" />
                </p>
                <button type="button" className="button secondary" onClick={retry} data-testid="retry-turn">
                  <UiText text={uiCopy.action.retry} inline />
                </button>
              </div>
            )}
            <p role="status" className="status-line" data-testid="step-status">
              <UiText text={stepStatus} tier="guide" />
            </p>
            {!checkpoint && onRestart && (completed || !sessionOpen) && (
              <p>
                <button
                  type="button"
                  className="button secondary"
                  onClick={onRestart}
                  disabled={starting}
                  data-testid="restart-session"
                >
                  <UiText text={missionsCopy.restartSession} inline />
                </button>
              </p>
            )}
            {audioLabel && (
              <p>
                {/* the reply is a computer voice; which one is a developer detail */}
                <span className="label warn" data-testid="character-audio-label">
                  <UiText text={uiCopy.chip.voiceLabel} inline />
                  {developer && <> · {audioLabel}</>}
                </span>
              </p>
            )}
            {audioNotice && (
              <p className="muted">
                <UiText text={audioNotice} tier="guide" />
              </p>
            )}

            <div className="talk-controls">
              <button
                type="button"
                className="button talk"
                aria-pressed={recorder.phase === "recording"}
                disabled={!canSend || recorder.phase === "unsupported"}
                {...talkButtonHandlers(() => void recorder.start(), recorder.stop)}
                data-testid="talk-button"
              >
                <UiText
                  text={recorder.phase === "recording" ? missionsCopy.talkRecording : missionsCopy.talkHold}
                  inline
                />
              </button>
              {recorder.phase === "unsupported" && (
                <p className="error">
                  <UiText text={missionsCopy.recordingUnsupported} tier="guide" />
                </p>
              )}
              {recorder.error && <p className="error">{recorder.error}</p>}
            </div>

            {typedAllowed ? (
              <form
                className="typed-form"
                onSubmit={(event) => {
                  event.preventDefault();
                  const text = typedText.trim();
                  if (!text || !canSend) return;
                  void submit({ requestId: newRequestId(), modality: "typed", text });
                }}
              >
                <label
                  htmlFor={`typed-${step.key}`}
                  className="muted"
                  style={{ display: "block", fontSize: "0.85rem" }}
                >
                  <UiText text={missionsCopy.typedLabel} />
                </label>
                <textarea
                  id={`typed-${step.key}`}
                  value={typedText}
                  onChange={(event) => setTypedText(event.target.value)}
                  rows={2}
                  maxLength={600}
                  lang="nl"
                  disabled={!canSend}
                  data-testid="typed-input"
                  style={{ width: "100%", font: "inherit", padding: "0.5rem" }}
                />
                <button
                  type="submit"
                  className="button secondary"
                  disabled={!canSend || !typedText.trim()}
                  data-testid="typed-send"
                >
                  <UiText text={missionsCopy.typedSend} inline />
                </button>
              </form>
            ) : (
              <p className="muted" data-testid="typed-disabled">
                <UiText text={missionsCopy.typedNotAllowed} tier="guide" />
              </p>
            )}
          </section>

          <aside>
            <section className="card" aria-labelledby="appointment-heading" data-testid="appointment-panel">
              <h3 id="appointment-heading">
                <UiText
                  text={
                    info?.scenario_kind === "service"
                      ? missionsCopy.yourConversation
                      : missionsCopy.appointment
                  }
                />
              </h3>
              <ul className="checklist">
                <li data-done={Boolean(appointment.reason_stated)}>
                  {appointment.reason_stated ? "✓" : "○"}{" "}
                  <UiText
                    text={
                      info?.scenario_kind === "service"
                        ? missionsCopy.actionStateNeed
                        : missionsCopy.actionStateReason
                    }
                    inline
                  />
                </li>
                {info?.scenario_kind === "service" ? (
                  <li data-done={Boolean(appointment.selected_choice_id)}>
                    {appointment.selected_choice_id ? "✓" : "○"}{" "}
                    <UiText text={missionsCopy.choiceLine} inline />{" "}
                    {info.choices?.find((c) => c.id === appointment.selected_choice_id)?.label.nl || "—"}
                  </li>
                ) : (
                  <li data-done={Boolean(appointment.accepted_slot_id)}>
                    {appointment.accepted_slot_id ? "✓" : "○"}{" "}
                    <UiText text={missionsCopy.newMomentLine} inline />{" "}
                    {appointment.accepted_slot_id ? describeSlot(info, appointment.accepted_slot_id) : "—"}
                  </li>
                )}
                <li data-done={Boolean(appointment.confirmed)}>
                  {appointment.confirmed ? "✓" : "○"} <UiText text={missionsCopy.actionConfirm} inline />
                </li>
                {appointment.cancelled && (
                  <li>
                    {"✗ "}
                    <UiText text={missionsCopy.conversationCancelled} inline />
                  </li>
                )}
              </ul>
              <p className="muted" style={{ fontSize: "0.85rem" }}>
                <UiText
                  text={
                    info?.scenario_kind === "service"
                      ? fill(missionsCopy.choicesList, {
                          list: info.choices?.map((c) => c.label.nl).join("; ") ?? "",
                        })
                      : fill(missionsCopy.slotsList, {
                          list: info?.slots.map((s) => describeSlot(info, s.id)).join("; ") ?? "",
                        })
                  }
                  inline
                />
              </p>
              <p className="mono" style={{ fontSize: "0.8rem" }}>
                <UiText
                  text={fill(missionsCopy.turnCount, { used: progress?.turns ?? 0, max: maxTurns })}
                  inline
                />
              </p>
            </section>
            <section className="card" aria-labelledby="help-heading">
              <h3 id="help-heading">
                <UiText text={missionsCopy.help} />
              </h3>
              <HelpLadder
                rungs={helpRungs}
                idPrefix={step.key}
                disabled={!helpAllowed || send.kind === "sending"}
                onReveal={recordHelpUse}
              />
            </section>
            {(!checkpoint || !sessionOpen) && (
              <FeedbackPanel
                stepKey={step.key}
                detail={detail}
                onDetail={onDetail}
                onProgressChanged={onProgressChanged}
              />
            )}
          </aside>
        </div>
      )}
    </article>
  );
}

function TurnBubbles({
  turn,
  characterName,
  playing,
  onPlay,
}: {
  turn: TurnView;
  characterName: string;
  playing: boolean;
  onPlay: () => void;
}) {
  const result = turn.action_result;
  const actionText = result ? (
    result.accepted ? (
      <ActionLabel action={result.action} />
    ) : result.action === "none" ? (
      <UiText text={missionsCopy.actionNotRecognised} inline />
    ) : (
      <>
        <ActionLabel action={result.action} />
        {" — "}
        <UiText text={missionsCopy.actionNotAccepted} inline />
      </>
    )
  ) : null;
  return (
    <>
      <li
        className={`bubble learner ${turn.status}`}
        data-testid="turn-learner"
        data-modality={turn.modality}
        data-turn-status={turn.status}
      >
        <span className="who">
          <UiText text={missionsCopy.you} inline />
        </span>
        <span lang="nl">{turn.learner_text}</span>
        <span className="muted" style={{ display: "block", fontSize: "0.8rem" }}>
          <UiText
            text={turn.modality === "speech" ? missionsCopy.spokenTranscript : missionsCopy.typedSaved}
            inline
          />
          {actionText && (
            <>
              {" · "}
              {actionText}
            </>
          )}
          {turn.status === "failed" && (
            <>
              {" · "}
              <UiText text={missionsCopy.turnFailed} inline />
            </>
          )}
        </span>
        {turn.recording_warning && (
          <span className="muted" role="status">
            <UiText text={missionsCopy.recordingWarning} tier="guide" inline />
          </span>
        )}
      </li>
      {turn.status === "completed" && (
        <li className="bubble character" data-testid="turn-character" data-source={turn.reply_source ?? ""}>
          <span className="who">{characterName}</span>
          <span lang="nl">{turn.character_text}</span>
          <span className="muted" style={{ display: "block", fontSize: "0.8rem" }}>
            {turn.character_audio_asset_id && (
              <>
                {" · "}
                <button
                  type="button"
                  className="linklike"
                  onClick={onPlay}
                  aria-pressed={playing}
                  data-testid="play-turn"
                >
                  <UiText text={playing ? missionsCopy.playing : missionsCopy.play} inline />
                </button>
              </>
            )}
          </span>
        </li>
      )}
    </>
  );
}
