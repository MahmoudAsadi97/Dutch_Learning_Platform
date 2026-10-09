"use client";

import { useState } from "react";

import { LearningText } from "@/components/LanguageSupport";
import { ContentLabel } from "@/components/ContentLabel";
import { FeedbackPanel } from "@/components/FeedbackPanel";
import { HelpLadder } from "@/components/HelpLadder";
import { QuestionList } from "@/components/QuestionList";
import type { StepProps } from "@/components/ReadingStep";
import { StepHeader } from "@/components/StepHeader";
import { UiText } from "@/components/ui/UiText";
import { ApiError, apiFetch } from "@/lib/client/api";
import { errorCopy } from "@/lib/client/error-copy";
import { usePlayback } from "@/lib/client/playback";
import { recordHelp, submitAnswer } from "@/lib/client/practice";
import { missionsCopy } from "@/lib/copy/missions";
import type { HelpRung, ListeningPayload, Step } from "@/lib/types";
import { fill, type Copy } from "@/lib/ui-copy";

interface Props extends StepProps {
  missionId: string;
  step: Step & { payload: ListeningPayload };
}

/**
 * The listening step: the fixed clip (synthesised once by the API and labelled as such), the questions
 * judged by the API, the transcript on request, and the help ladder.
 */
export function ListeningStep({
  missionId,
  step,
  labels,
  detail,
  ensureSession,
  onDetail,
  onProgressChanged,
}: Props) {
  const { payload } = step;
  const [audioLabel, setAudioLabel] = useState("");
  // A Copy for playback outcomes; a failed download keeps the API's own message as a plain string (step 2.8 maps those).
  const [audioNotice, setAudioNotice] = useState<Copy | null>(null);
  const [playing, setPlaying] = useState(false);
  const [plays, setPlays] = useState(0);
  const [showTranscript, setShowTranscript] = useState(false);
  const [transcriptBusy, setTranscriptBusy] = useState(false);
  const [transcriptError, setTranscriptError] = useState<Copy | null>(null);
  const playback = usePlayback();
  const progress = detail?.session.step_progress[step.key];

  async function play() {
    setAudioNotice(null);
    try {
      const response = await apiFetch(`missions/${missionId}/audio/${payload.audio_key}`);
      if (!response.ok) {
        const body = (await response.json().catch(() => ({}))) as { detail?: string; code?: string };
        throw new ApiError(
          response.status,
          body.detail ?? response.statusText,
          response.headers.get("x-request-id") ?? "",
          body.code ?? "",
        );
      }
      setAudioLabel(response.headers.get("x-audio-label") ?? "unknown");
      const wav = await response.blob();
      setPlaying(true);
      setPlays((n) => n + 1);
      const outcome = await playback.play(wav, () => setPlaying(false));
      if (outcome.failed) {
        setPlaying(false);
        setAudioNotice(missionsCopy.clipPlaybackFailed);
      } else if (outcome.blocked) {
        setPlaying(false);
        setAudioNotice(missionsCopy.clipPlaybackBlocked);
      }
    } catch (cause) {
      setPlaying(false);
      setAudioNotice(
        errorCopy(cause, missionsCopy.audioUnavailable, {
          404: missionsCopy.audioUnavailable,
          502: missionsCopy.audioUnavailable,
          503: missionsCopy.audioUnavailable,
        }),
      );
    }
  }

  async function answer(questionId: string, chosenIndex: number) {
    const current = detail ?? (await ensureSession());
    const result = await submitAnswer(current, step.key, questionId, chosenIndex);
    onDetail(result.detail);
    onProgressChanged();
    return { correct: result.correct, answer_index: result.answer_index };
  }

  async function help(rung: HelpRung, questionId = "") {
    const current = detail ?? (await ensureSession());
    onDetail(await recordHelp(current, step.key, rung, questionId));
  }

  async function toggleTranscript() {
    if (showTranscript) {
      setShowTranscript(false);
      return;
    }
    setTranscriptBusy(true);
    setTranscriptError(null);
    try {
      const current = detail ?? (await ensureSession());
      onDetail(await recordHelp(current, step.key, { level: 3, kind: "listening_transcript" }));
      setShowTranscript(true);
    } catch {
      setTranscriptError(missionsCopy.transcriptFailed);
    } finally {
      setTranscriptBusy(false);
    }
  }

  return (
    <article aria-labelledby="step-title" data-step={step.key} data-step-type="listening">
      <StepHeader step={step} labels={labels} />

      <section className="card" aria-labelledby="clip-heading">
        <h3 id="clip-heading">
          <UiText text={missionsCopy.listenTitle} />
        </h3>
        <p>
          <button
            type="button"
            className="button"
            onClick={() => void play()}
            disabled={playing}
            data-testid="play-clip"
          >
            <UiText
              text={
                playing
                  ? missionsCopy.clipPlaying
                  : plays > 0
                    ? missionsCopy.listenAgain
                    : missionsCopy.listen
              }
              inline
            />
          </button>
          {plays > 0 && (
            <span className="muted" style={{ marginInlineStart: "0.75rem" }} data-testid="play-count">
              <UiText text={fill(missionsCopy.playCount, { count: plays })} inline />
            </span>
          )}
        </p>
        {audioLabel && (
          <p>
            <span className="label warn" data-testid="clip-label">
              <UiText text={missionsCopy.syntheticVoice} inline />
            </span>
            <span className="muted" style={{ fontSize: "0.85rem" }}>
              <UiText text={missionsCopy.listenWhenNeeded} tier="guide" inline />
            </span>
          </p>
        )}
        {audioNotice && (
          <p className="error" role="alert">
            <UiText text={audioNotice} tier="guide" />
          </p>
        )}
        <p>
          <button
            type="button"
            className="button secondary"
            aria-expanded={showTranscript}
            disabled={transcriptBusy}
            onClick={() => void toggleTranscript()}
            data-testid="toggle-transcript"
          >
            <UiText text={showTranscript ? missionsCopy.hideText : missionsCopy.showText} inline />
          </button>
        </p>
        {transcriptError && (
          <p className="error" role="alert">
            <UiText text={transcriptError} tier="guide" />
          </p>
        )}
        {showTranscript && (
          <>
            <p>
              <ContentLabel
                status={payload.transcript.review_status}
                labelNl={labels.unreviewed_nl}
                labelFa={labels.unreviewed_fa}
              />
            </p>
            <div className="dutch-text nl" lang="nl" data-testid="transcript">
              {payload.transcript.nl}
            </div>
            <div className="dutch-text">
              <LearningText text={payload.transcript} supportOnly />
            </div>
          </>
        )}
      </section>

      <QuestionList
        stepKey={step.key}
        questions={payload.questions}
        progress={progress}
        onAnswer={answer}
        onHelp={help}
      />

      <section className="card" aria-labelledby="help-heading">
        <h3 id="help-heading">
          <UiText text={missionsCopy.help} />
        </h3>
        <HelpLadder rungs={payload.help} idPrefix={step.key} onReveal={(rung) => help(rung)} />
      </section>

      <FeedbackPanel
        stepKey={step.key}
        detail={detail}
        onDetail={onDetail}
        onProgressChanged={onProgressChanged}
      />
    </article>
  );
}
