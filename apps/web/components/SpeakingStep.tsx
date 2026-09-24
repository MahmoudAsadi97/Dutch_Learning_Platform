"use client";

import { useEffect, useRef, useState } from "react";

import { ContentLabel } from "@/components/ContentLabel";
import { FeedbackPanel } from "@/components/FeedbackPanel";
import { HelpLadder } from "@/components/HelpLadder";
import { ApiError, apiFetch, apiJson, newRequestId } from "@/lib/client/api";
import { usePlayback } from "@/lib/client/playback";
import { recordHelp } from "@/lib/client/practice";
import { type Recording, talkButtonHandlers, useRecorder } from "@/lib/client/recorder";
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
  | { kind: "failed"; pending: Pending; message: string; sameRequestId: boolean };

const DAY_NAMES_NL = ["zondag", "maandag", "dinsdag", "woensdag", "donderdag", "vrijdag", "zaterdag"];
const MONTH_NAMES_NL = ["januari", "februari", "maart", "april", "mei", "juni", "juli", "augustus", "september", "oktober", "november", "december"];

export function describeSlot(info: ConversationStepInfo | undefined, slotId: string | undefined): string {
  const slot = info?.slots.find((s) => s.id === slotId);
  if (!slot) return slotId ?? "";
  const [year, month, day] = slot.day.split("-").map(Number);
  const date = new Date(Date.UTC(year, month - 1, day));
  const [hour, minute] = slot.start.split(":");
  const time = minute === "00" ? `${Number(hour)} uur` : `${Number(hour)}.${minute} uur`;
  return `${DAY_NAMES_NL[date.getUTCDay()]} ${day} ${MONTH_NAMES_NL[month - 1]} om ${time}`;
}

const ACTION_LABEL: Record<string, string> = {
  state_need: "vraag uitgelegd",
  choose_option: "keuze gemaakt",
  state_reason: "reden gegeven",
  accept_slot: "nieuw moment gekozen",
  confirm: "bevestigd",
  propose_slot: "moment voorgesteld",
  ask_repeat: "om herhaling gevraagd",
  cancel: "geannuleerd",
  none: "geen actie",
};

/**
 * The speaking step and the checkpoint: a push-to-talk conversation with the character.
 * Every learner turn is sent with its own request id; a retry after a network failure reuses that id,
 * so the server answers from the stored turn instead of running the model twice.
 */
export function SpeakingStep({ step, labels, detail, starting, onStart, onRestart, onDetail, onProgressChanged }: Props) {
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
  const [audioNotice, setAudioNotice] = useState<string>("");
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

  const canSend = Boolean(session && sessionOpen && info && !completed && send.kind !== "sending" && turnsLeft > 0);

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
        const message = cause.status === 429 ? "Uw oefenlimiet is bereikt. Bekijk uw gebruik in Instellingen." : cause.status === 401 || cause.status === 403 ? "Meld u opnieuw aan om verder te oefenen." : "Uw antwoord kon niet worden verwerkt. Probeer opnieuw.";
        setSend({ kind: "failed", pending, message, sameRequestId: retryWithSameId });
        if (cause.status === 502) await reload();
      } else {
        setSend({ kind: "failed", pending, message: "Geen verbinding met de server.", sameRequestId: true });
      }
    } finally {
      abortRef.current = null;
    }
  }

  function applyTurn(response: TurnResponse) {
    if (!detail) return;
    const others = detail.turns.filter((t) => t.id !== response.turn.id);
    onDetail({ ...detail, session: response.session, turns: [...others, response.turn].sort((a, b) => a.turn_index - b.turn_index) });
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

  const recorder = useRecorder((recording) => void submit({ requestId: newRequestId(), modality: "speech", recording }));

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
      if (turn.audio_error) setAudioNotice("Geen audio voor dit antwoord; lees de tekst.");
      return;
    }
    setAudioNotice("");
    try {
      const response = await apiFetch(`practice/sessions/${session.id}/turns/${turn.id}/audio`);
      if (!response.ok) throw new Error(`audio ${response.status}`);
      setAudioLabel(response.headers.get("x-audio-label") ?? "unknown");
      const wav = await response.blob();
      setPlayingTurnId(turn.id);
      const outcome = await playback.play(wav, () => setPlayingTurnId((current) => (current === turn.id ? "" : current)));
      if (outcome.failed) {
        setPlayingTurnId("");
        setAudioNotice("Afspelen mislukt; lees de tekst van het antwoord.");
      } else if (outcome.blocked) {
        setPlayingTurnId("");
        setAudioNotice("Automatisch afspelen is geblokkeerd; druk op \u201cspeel af\u201d bij het antwoord.");
      }
    } catch {
      setPlayingTurnId("");
      setAudioNotice("Afspelen mislukt; lees de tekst van het antwoord.");
    }
  }

  const stepStatus = !session
    ? "Nog geen sessie."
    : session.status === "completed"
      ? "Controle afgerond: het doel is bereikt."
      : session.status === "ended"
        ? "De beurten zijn opgebruikt; de controle is afgesloten."
        : session.status === "abandoned"
          ? "Deze sessie is afgebroken."
          : completed
            ? typedOnly
              ? "Doel bereikt met getypte tekst. Dat telt niet als spreekoefening: start een nieuwe oefensessie en spreek de beurten in."
              : "Doel bereikt. U kunt verder naar de volgende stap."
            : `${turnsLeft} van ${maxTurns} beurten over.`;

  return (
    <article aria-labelledby="step-title" data-step={step.key} data-step-type={payload.type}>
      <header>
        <h2 id="step-title">
          {step.title.nl}
          <span className="fa" lang="fa" style={{ display: "block", fontSize: "1rem", fontWeight: 400 }}>
            {step.title.fa}
          </span>
        </h2>
        <p>
          <ContentLabel status={step.instructions.review_status} labelNl={labels.unreviewed_nl} labelFa={labels.unreviewed_fa} />
        </p>
        <p lang="nl">{step.instructions.nl}</p>
        <p className="fa" lang="fa">
          {step.instructions.fa}
        </p>
        {checkpoint && (
          <p>
            <span className="label warn" data-testid="checkpoint-rules">
              zelfstandige controle: alleen spreken, geen hulp, één poging
            </span>
          </p>
        )}
      </header>

      <section className="card" aria-labelledby="goal-heading">
        <h3 id="goal-heading">Doel</h3>
        <p>
          <ContentLabel status={payload.goal.review_status} labelNl={labels.unreviewed_nl} labelFa={labels.unreviewed_fa} />
        </p>
        <p lang="nl">{payload.goal.nl}</p>
        <p className="fa" lang="fa">
          {payload.goal.fa}
        </p>
      </section>

      {!session ? (
        <section className="card">
          <p>Start een sessie om met {info?.character.name ?? "de medewerker"} te bellen.</p>
          <button type="button" className="button" onClick={onStart} disabled={starting} data-testid="start-conversation">
            {starting ? "Bezig…" : checkpoint ? "Start de controle (één poging)" : "Start het gesprek"}
          </button>
        </section>
      ) : (
        <div className="grid two">
          <section className="card" aria-labelledby="conversation-heading">
            <h3 id="conversation-heading">
              Gesprek met {info?.character.name}
              {info && (
                <span className="muted" style={{ fontWeight: 400, fontSize: "0.85rem" }}>
                  {" "}· {info.character.role.nl}
                </span>
              )}
            </h3>
            <ol className="conversation" ref={listRef} data-testid="conversation" aria-live="polite">
              <li className="bubble character" data-testid="turn-character" data-source="fixed_line">
                <span className="who">{info?.character.name}</span>
                <span lang="nl">{info?.opening_line}</span>
              </li>
              {turns.map((turn) => (
                <TurnBubbles key={turn.id} turn={turn} characterName={info?.character.name ?? ""} playing={playingTurnId === turn.id} onPlay={() => void playCharacterAudio(turn)} />
              ))}
              {send.kind === "sending" && (
                <li className="bubble learner pending" data-testid="turn-pending">
                  <span className="who">U</span>
                  <span lang="nl">{send.pending.text ?? "(opname)"}</span>
                  <span className="muted" style={{ display: "block", fontSize: "0.8rem" }}>
                    {send.pending.modality === "speech" ? "Uploaden, herkennen en antwoord opstellen…" : "Antwoord opstellen…"}
                  </span>
                </li>
              )}
            </ol>
            {send.kind === "sending" && (
              <p>
                <button type="button" className="button secondary" onClick={cancel} data-testid="cancel-turn">
                  Annuleren
                </button>
              </p>
            )}
            {send.kind === "failed" && (
              <div role="alert" data-testid="turn-error">
                <p className="error">{send.message}</p>
                <button type="button" className="button secondary" onClick={retry} data-testid="retry-turn">
                  Opnieuw proberen
                </button>
              </div>
            )}
            <p role="status" className="status-line" data-testid="step-status">
              {stepStatus}
            </p>
            {!checkpoint && onRestart && (completed || !sessionOpen) && (
              <p>
                <button type="button" className="button secondary" onClick={onRestart} disabled={starting} data-testid="restart-session">
                  Nieuwe oefensessie (de huidige wordt afgesloten)
                </button>
              </p>
            )}
            {audioLabel && (
              <p>
                <span className="label warn" data-testid="character-audio-label">
                  audio: {audioLabel}
                </span>
              </p>
            )}
            {audioNotice && <p className="muted">{audioNotice}</p>}

            <div className="talk-controls">
              <button
                type="button"
                className="button talk"
                aria-pressed={recorder.phase === "recording"}
                disabled={!canSend || recorder.phase === "unsupported"}
                {...talkButtonHandlers(() => void recorder.start(), recorder.stop)}
                data-testid="talk-button"
              >
                {recorder.phase === "recording" ? "Opname loopt… laat los om te versturen" : "Houd ingedrukt om te spreken"}
              </button>
              {recorder.phase === "unsupported" && <p className="error">Deze browser ondersteunt geen opname.</p>}
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
                <label htmlFor={`typed-${step.key}`} className="muted" style={{ display: "block", fontSize: "0.85rem" }}>
                  Of typ uw zin (wordt als getypte tekst opgeslagen, niet als spraak)
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
                <button type="submit" className="button secondary" disabled={!canSend || !typedText.trim()} data-testid="typed-send">
                  Verstuur getypt
                </button>
              </form>
            ) : (
              <p className="muted" data-testid="typed-disabled">
                Typen is in deze stap niet toegestaan.
              </p>
            )}
          </section>

          <aside>
            <section className="card" aria-labelledby="appointment-heading" data-testid="appointment-panel">
              <h3 id="appointment-heading">{info?.scenario_kind === "service" ? "Uw gesprek" : "Afspraak"}</h3>
              <ul className="checklist">
                <li data-done={Boolean(appointment.reason_stated)}>
                  {appointment.reason_stated ? "✓" : "○"} {info?.scenario_kind === "service" ? "vraag uitgelegd" : "reden gegeven"}
                </li>
                {info?.scenario_kind === "service" ? (
                  <li data-done={Boolean(appointment.selected_choice_id)}>
                    {appointment.selected_choice_id ? "✓" : "○"} keuze: {info.choices?.find(c => c.id === appointment.selected_choice_id)?.label.nl || "—"}
                  </li>
                ) : (
                  <li data-done={Boolean(appointment.accepted_slot_id)}>
                    {appointment.accepted_slot_id ? "✓" : "○"} nieuw moment: {appointment.accepted_slot_id ? describeSlot(info, appointment.accepted_slot_id) : "—"}
                  </li>
                )}
                <li data-done={Boolean(appointment.confirmed)}>{appointment.confirmed ? "✓" : "○"} bevestigd</li>
                {appointment.cancelled && <li>✗ gesprek geannuleerd</li>}
              </ul>
              <p className="muted" style={{ fontSize: "0.85rem" }}>
                {info?.scenario_kind === "service" ? "Keuzes: " + info.choices?.map(c => c.label.nl).join("; ") : "Beschikbare momenten: " + info?.slots.map((s) => describeSlot(info, s.id)).join("; ")}
              </p>
              <p className="mono" style={{ fontSize: "0.8rem" }}>
                Gespreksbeurten {progress?.turns ?? 0}/{maxTurns}
              </p>
            </section>
            <section className="card" aria-labelledby="help-heading">
              <h3 id="help-heading">Hulp</h3>
              <HelpLadder rungs={helpRungs} idPrefix={step.key} disabled={!helpAllowed || send.kind === "sending"} onReveal={recordHelpUse} />
            </section>
            {(!checkpoint || !sessionOpen) && (
              <FeedbackPanel stepKey={step.key} detail={detail} onDetail={onDetail} onProgressChanged={onProgressChanged} />
            )}
          </aside>
        </div>
      )}
    </article>
  );
}

function TurnBubbles({ turn, characterName, playing, onPlay }: { turn: TurnView; characterName: string; playing: boolean; onPlay: () => void }) {
  const result = turn.action_result;
  const actionText = result
    ? result.accepted
      ? `${ACTION_LABEL[result.action] ?? result.action}`
      : result.action === "none"
        ? "geen actie herkend"
        : `${ACTION_LABEL[result.action] ?? result.action} — niet aanvaard`
    : "";
  return (
    <>
      <li className={`bubble learner ${turn.status}`} data-testid="turn-learner" data-modality={turn.modality} data-turn-status={turn.status}>
        <span className="who">U</span>
        <span lang="nl">{turn.learner_text}</span>
        <span className="muted" style={{ display: "block", fontSize: "0.8rem" }}>
          {turn.modality === "speech" ? "gesproken · transcriptie" : "getypt · als getypte tekst opgeslagen"}
          {actionText && ` · ${actionText}`}
          {turn.status === "failed" && " · mislukt"}
        </span>
        {turn.recording_warning && (
          <span className="muted" role="status">Uw tekst is bewaard. De geluidsopname kon niet worden opgeslagen.</span>
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
                <button type="button" className="linklike" onClick={onPlay} aria-pressed={playing} data-testid="play-turn">
                  {playing ? "speelt" : "speel af"}
                </button>
              </>
            )}
          </span>
        </li>
      )}
    </>
  );
}
