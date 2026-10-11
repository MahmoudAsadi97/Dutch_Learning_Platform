"use client";

import { useId, type Ref } from "react";

import { Button } from "@/components/ui/Button";
import { UiText } from "@/components/ui/UiText";
import { exerciseCopy } from "@/lib/copy/exercise";
import type { Feedback, Prompt } from "@/lib/client/exercises";
import { useRecorder, type Recording } from "@/lib/client/recorder";

import { Dutch } from "./ContentText";
import { ItemAudio } from "./ItemAudio";

interface Props {
  prompt: Extract<Prompt, { kind: "shadow" }>;
  sessionId: string;
  itemId: string;
  feedback: Feedback | null;
  /** Sending: the recording is on its way to be heard. */
  busy: boolean;
  onRecording: (recording: Recording) => void;
  headingRef?: Ref<HTMLHeadingElement>;
}

/**
 * Shadowing ("zeg het na"): hear the sentence, then say it after the voice. One press starts the recording and
 * another stops it (no holding down, so it works the same by touch, keyboard and switch). The recording goes to
 * the speech service and is not kept; the outcome is heard or not heard, never a score (D-30), and the words it
 * heard are shown as they are.
 */
export function ShadowItem({ prompt, sessionId, itemId, feedback, busy, onRecording, headingRef }: Props) {
  const headingId = useId();
  const recorder = useRecorder(onRecording);
  const recording = recorder.phase === "recording";
  const answered = feedback !== null;

  return (
    <div className="exercise-item">
      <h2 className="exercise-question" id={headingId} tabIndex={-1} ref={headingRef}>
        <UiText text={exerciseCopy.askShadow} tier="guide" />
      </h2>
      <div className="exercise-stem">
        <p className="exercise-prompt shadow-sentence">
          <Dutch text={prompt.sentence} />
        </p>
        <ItemAudio sessionId={sessionId} itemId={itemId} disabled={recording} />
      </div>
      {!answered && (
        <div className="shadow-record">
          {recorder.phase === "unsupported" ? (
            <p className="exercise-lead">
              <UiText text={exerciseCopy.recordUnsupported} tier="guide" />
            </p>
          ) : (
            <Button
              variant="talk"
              icon="mic"
              aria-pressed={recording}
              disabled={busy}
              onClick={() => {
                if (recording) recorder.stop();
                else void recorder.start();
              }}
            >
              <UiText
                text={
                  recording
                    ? exerciseCopy.recordStop
                    : busy
                      ? exerciseCopy.recordListening
                      : exerciseCopy.recordStart
                }
                inline
              />
            </Button>
          )}
          <p className="shadow-status" role="status">
            {recording && <UiText text={exerciseCopy.recordOn} tier="guide" />}
            {recorder.error && <UiText text={exerciseCopy.recordFailed} tier="guide" />}
          </p>
        </div>
      )}
      {answered && feedback.transcript !== undefined && (
        <p className="feedback-line">
          <UiText text={exerciseCopy.weHeard} inline />
          {": "}
          {feedback.transcript ? (
            <Dutch text={feedback.transcript} />
          ) : (
            <UiText text={exerciseCopy.heardNothing} inline />
          )}
        </p>
      )}
    </div>
  );
}
