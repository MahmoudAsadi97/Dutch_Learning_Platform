"use client";

import { useState } from "react";

import { ContentLabel } from "@/components/ContentLabel";
import { FeedbackPanel } from "@/components/FeedbackPanel";
import { HelpLadder } from "@/components/HelpLadder";
import { QuestionList } from "@/components/QuestionList";
import type { StepProps } from "@/components/ReadingStep";
import { StepHeader } from "@/components/StepHeader";
import { ApiError, apiFetch } from "@/lib/client/api";
import { usePlayback } from "@/lib/client/playback";
import { recordHelp, submitAnswer } from "@/lib/client/practice";
import type { HelpRung, ListeningPayload, Step } from "@/lib/types";

interface Props extends StepProps {
  missionId: string;
  step: Step & { payload: ListeningPayload };
}

/**
 * The listening step: the fixed clip (synthesised once by the API and labelled as such), the questions
 * judged by the API, the transcript on request, and the help ladder.
 */
export function ListeningStep({ missionId, step, labels, detail, ensureSession, onDetail, onProgressChanged }: Props) {
  const { payload } = step;
  const [audioLabel, setAudioLabel] = useState("");
  const [audioNotice, setAudioNotice] = useState("");
  const [playing, setPlaying] = useState(false);
  const [plays, setPlays] = useState(0);
  const [showTranscript, setShowTranscript] = useState(false);
  const playback = usePlayback();
  const progress = detail?.session.step_progress[step.key];

  async function play() {
    setAudioNotice("");
    try {
      const response = await apiFetch(`missions/${missionId}/audio/${payload.audio_key}`);
      if (!response.ok) {
        const body = (await response.json().catch(() => ({}))) as { detail?: string };
        throw new ApiError(response.status, body.detail ?? response.statusText, response.headers.get("x-request-id") ?? "");
      }
      setAudioLabel(response.headers.get("x-audio-label") ?? "unknown");
      const wav = await response.blob();
      setPlaying(true);
      setPlays((n) => n + 1);
      const outcome = await playback.play(wav, () => setPlaying(false));
      if (outcome.failed) {
        setPlaying(false);
        setAudioNotice("Afspelen mislukt.");
      } else if (outcome.blocked) {
        setPlaying(false);
        setAudioNotice("Afspelen werd geblokkeerd; klik nog eens op de knop.");
      }
    } catch (cause) {
      setPlaying(false);
      setAudioNotice(cause instanceof ApiError ? `Audio niet beschikbaar: ${cause.detail}` : "Audio niet beschikbaar.");
    }
  }

  async function answer(questionId: string, chosenIndex: number) {
    const current = detail ?? (await ensureSession());
    const result = await submitAnswer(current, step.key, questionId, chosenIndex);
    onDetail(result.detail);
    onProgressChanged();
    return { correct: result.correct, answer_index: result.answer_index };
  }

  function help(rung: HelpRung, questionId = "") {
    void (async () => {
      try {
        const current = detail ?? (await ensureSession());
        onDetail(await recordHelp(current, step.key, rung, questionId));
      } catch {
        // the rung is shown regardless; the evidence is best effort
      }
    })();
  }

  return (
    <article aria-labelledby="step-title" data-step={step.key} data-step-type="listening">
      <StepHeader step={step} labels={labels} />

      <section className="card" aria-labelledby="clip-heading">
        <h3 id="clip-heading">Beluister de boodschap</h3>
        <p>
          <button type="button" className="button" onClick={() => void play()} disabled={playing} data-testid="play-clip">
            {playing ? "Speelt…" : plays > 0 ? "Nog eens beluisteren" : "Beluister"}
          </button>
          {plays > 0 && (
            <span className="muted" style={{ marginInlineStart: "0.75rem" }} data-testid="play-count">
              {plays}× beluisterd
            </span>
          )}
        </p>
        {audioLabel && (
          <p>
            <span className="label warn" data-testid="clip-label">
              audio: {audioLabel}
            </span>
            <span className="muted" style={{ fontSize: "0.85rem" }}>
              synthetische stem; wordt in fase B vervangen door de Azure nl-BE-stem
            </span>
          </p>
        )}
        {audioNotice && (
          <p className="error" role="alert">
            {audioNotice}
          </p>
        )}
        <p>
          <button type="button" className="button secondary" aria-expanded={showTranscript} onClick={() => setShowTranscript(!showTranscript)} data-testid="toggle-transcript">
            {showTranscript ? "Verberg de tekst" : "Toon de tekst"}
          </button>
        </p>
        {showTranscript && (
          <>
            <p>
              <ContentLabel status={payload.transcript.review_status} labelNl={labels.unreviewed_nl} labelFa={labels.unreviewed_fa} />
            </p>
            <div className="dutch-text nl" lang="nl" data-testid="transcript">
              {payload.transcript.nl}
            </div>
            <div className="dutch-text fa" lang="fa" dir="rtl">
              {payload.transcript.fa}
            </div>
          </>
        )}
      </section>

      <QuestionList stepKey={step.key} questions={payload.questions} progress={progress} onAnswer={answer} onHelp={help} />

      <section className="card" aria-labelledby="help-heading">
        <h3 id="help-heading">
          Hulp · <span className="fa" lang="fa" style={{ display: "inline" }}>کمک</span>
        </h3>
        <HelpLadder rungs={payload.help} idPrefix={step.key} onReveal={(rung) => help(rung)} />
      </section>

      <FeedbackPanel stepKey={step.key} detail={detail} onDetail={onDetail} onProgressChanged={onProgressChanged} />
    </article>
  );
}
