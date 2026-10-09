"use client";

import { useEffect, useRef, useState } from "react";
import { Icon } from "@/components/Icon";
import { UiText } from "@/components/ui/UiText";

import { ApiError, apiFetch, apiJson, newRequestId } from "@/lib/client/api";
import { errorCopy } from "@/lib/client/error-copy";
import { usePlayback } from "@/lib/client/playback";
import { type Recording, talkButtonHandlers, useRecorder } from "@/lib/client/recorder";
import { useDeveloperDetails } from "@/components/shell/EnvContext";
import { speechCopy } from "@/lib/copy/speech";
import { uiCopy, type Copy } from "@/lib/ui-copy";

interface TranscriptResponse {
  request_id: string;
  transcript: { text: string; language: string; provider: string; model: string; latency_ms: number };
  audio: {
    asset_id: string;
    source: {
      container: string;
      codec: string;
      duration_seconds: number;
      sample_rate: number;
      channels: number;
    };
    canonical: {
      container: string;
      codec: string;
      duration_seconds: number;
      sample_rate: number;
      channels: number;
    };
  };
}

type Phase = "idle" | "recording" | "uploading" | "done" | "error" | "unsupported";

const PHASE_TEXT: Record<Phase, Copy> = {
  idle: speechCopy.phaseIdle,
  recording: speechCopy.phaseRecording,
  uploading: speechCopy.phaseUploading,
  done: speechCopy.phaseDone,
  unsupported: speechCopy.phaseUnsupported,
  error: speechCopy.phaseError,
};

/**
 * Push-to-talk microphone check: MediaRecorder → upload → ffmpeg → transcription, plus synthetic playback.
 * Hold the button (mouse, touch or the space bar) while speaking a Dutch sentence.
 */
export function SpeechCheck() {
  const developer = useDeveloperDetails();
  const [uploadPhase, setUploadPhase] = useState<"idle" | "uploading" | "done" | "error">("idle");
  const [result, setResult] = useState<TranscriptResponse | null>(null);
  const [error, setError] = useState<Copy | null>(null);
  const [ttsText, setTtsText] = useState("Goeiedag, ik wil graag Nederlands oefenen.");
  const [ttsLabel, setTtsLabel] = useState<string>("");
  const [ttsBusy, setTtsBusy] = useState(false);
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const recordingUrlRef = useRef("");
  const [recordingUrl, setRecordingUrl] = useState("");
  useEffect(
    () => () => {
      if (recordingUrlRef.current) URL.revokeObjectURL(recordingUrlRef.current);
    },
    [],
  );
  const playback = usePlayback();

  async function upload(recording: Recording) {
    setUploadPhase("uploading");
    setError(null);
    setResult(null);
    const form = new FormData();
    form.append("audio", recording.blob, recording.fileName);
    // A microphone check is not a practice attempt. Keep playback only in this browser tab.
    form.append("keep_recording", "false");
    try {
      const response = await apiJson<TranscriptResponse>("speech/transcribe", {
        method: "POST",
        formData: form,
        requestId: newRequestId(),
      });
      setResult(response);
      setUploadPhase("done");
    } catch (cause) {
      setUploadPhase("error");
      setError(
        errorCopy(cause, speechCopy.uploadFailed, {
          422: speechCopy.uploadFailed,
          502: speechCopy.uploadFailed,
          503: speechCopy.uploadFailed,
        }),
      );
    }
  }

  const recorder = useRecorder((recording) => {
    if (recordingUrlRef.current) URL.revokeObjectURL(recordingUrlRef.current);
    recordingUrlRef.current = URL.createObjectURL(recording.blob);
    setRecordingUrl(recordingUrlRef.current);
    void upload(recording);
  });

  async function playSynthesis() {
    setTtsBusy(true);
    setTtsLabel("");
    setError(null);
    try {
      const response = await apiFetch("speech/synthesize", { method: "POST", body: { text: ttsText } });
      if (!response.ok) {
        const payload = (await response.json().catch(() => ({}))) as { detail?: string; code?: string };
        throw new ApiError(
          response.status,
          payload.detail ?? response.statusText,
          response.headers.get("x-request-id") ?? "",
          payload.code ?? "",
        );
      }
      setTtsLabel(response.headers.get("x-audio-label") ?? "unknown");
      const wav = await response.blob();
      const outcome = await playback.play(wav);
      if (audioRef.current) audioRef.current.src = outcome.url;
      if (outcome.failed) setError(speechCopy.playbackFailed);
      else if (outcome.blocked) setError(speechCopy.playbackBlocked);
    } catch (cause) {
      // a failed request has catalogue copy; anything else went wrong while playing
      setError(
        cause instanceof ApiError || cause instanceof TypeError
          ? errorCopy(cause, speechCopy.synthesisFailed, {
              502: speechCopy.synthesisFailed,
              503: speechCopy.synthesisFailed,
            })
          : speechCopy.playbackFailed,
      );
    } finally {
      setTtsBusy(false);
    }
  }

  const mimeType = recorder.mimeType;
  const effectivePhase: Phase =
    recorder.phase === "unsupported"
      ? "unsupported"
      : recorder.phase === "recording"
        ? "recording"
        : uploadPhase;
  const recording = effectivePhase === "recording";
  const shownError = error || recorder.error;

  return (
    <div className="grid two speech-studio">
      <section className="card" aria-labelledby="record-heading">
        <span className="eyebrow">
          <UiText text={speechCopy.recordEyebrow} />
        </span>
        <h2 id="record-heading">
          <UiText text={speechCopy.recordTitle} />
        </h2>
        <p className="muted">
          <UiText text={speechCopy.recordIntro} tier="guide" inline />{" "}
          <em lang="nl">Ik wil mijn afspraak verzetten.</em>
        </p>
        <div
          className={`mic-orbit ${recording ? "recording" : ""}`}
          data-anim={recording ? "pulse" : undefined}
          aria-hidden="true"
        >
          <Icon name="mic" size={32} />
        </div>
        {developer && (
          <details className="lesson-details">
            <summary>
              <UiText text={speechCopy.formatTitle} inline />
            </summary>
            <p className="mono" data-testid="mime-type">
              MediaRecorder:{" "}
              {mimeType || (
                <UiText
                  text={
                    mimeType === undefined
                      ? speechCopy.formatChecking
                      : mimeType === null
                        ? speechCopy.formatUnsupported
                        : speechCopy.formatDefault
                  }
                  inline
                />
              )}
            </p>
          </details>
        )}
        <button
          type="button"
          className="button talk"
          aria-pressed={recording}
          disabled={effectivePhase === "unsupported" || effectivePhase === "uploading"}
          {...talkButtonHandlers(() => void recorder.start(), recorder.stop)}
          data-testid="talk-button"
        >
          <UiText
            text={
              recording
                ? speechCopy.talkRecording
                : effectivePhase === "uploading"
                  ? speechCopy.talkProcessing
                  : speechCopy.talkHold
            }
            inline
          />
        </button>
        <p role="status" aria-live="polite" data-testid="phase">
          <UiText text={PHASE_TEXT[effectivePhase]} />
        </p>
        {recordingUrl && (
          <div className="record-playback">
            <h3>
              <UiText text={speechCopy.ownRecordingTitle} />
            </h3>
            <audio
              controls
              src={recordingUrl}
              aria-label={speechCopy.ownRecordingListen.nl}
              style={{ width: "100%" }}
            />
            <p className="small-text muted">
              <UiText text={speechCopy.ownRecordingNote} tier="guide" />
            </p>
          </div>
        )}
        {shownError && (
          <p className="error" role="alert">
            {error ? <UiText text={error} tier="guide" /> : recorder.error}
          </p>
        )}
        {result && (
          <div data-testid="transcript-result">
            <h3>
              <UiText text={speechCopy.transcriptTitle} />
            </h3>
            <p className="dutch-text" lang="nl" data-testid="transcript-text">
              {result.transcript.text || <UiText text={speechCopy.transcriptEmpty} inline />}
            </p>
            <p className="muted">
              <UiText text={speechCopy.transcriptCompare} tier="guide" />
            </p>
          </div>
        )}
      </section>

      <section className="card" aria-labelledby="tts-heading">
        <span className="eyebrow">
          <UiText text={speechCopy.synthesisEyebrow} />
        </span>
        <h2 id="tts-heading">
          <UiText text={speechCopy.synthesisTitle} />
        </h2>
        <p className="muted">
          <UiText text={speechCopy.synthesisIntro} tier="guide" />
        </p>
        <label htmlFor="tts-text" className="visually-hidden">
          <UiText text={speechCopy.synthesisTextLabel} />
        </label>
        <textarea
          id="tts-text"
          value={ttsText}
          onChange={(event) => setTtsText(event.target.value)}
          rows={3}
          style={{ width: "100%", font: "inherit", padding: "0.5rem" }}
          maxLength={600}
        />
        <p>
          <button
            type="button"
            className="button"
            onClick={() => void playSynthesis()}
            disabled={ttsBusy}
            data-testid="tts-button"
          >
            <UiText text={ttsBusy ? speechCopy.synthesisBusy : speechCopy.synthesisPlay} inline />
          </button>
        </p>
        {ttsLabel && (
          <p>
            <span className="label warn" data-testid="tts-label">
              <UiText text={uiCopy.chip.voiceLabel} inline />
              {developer && <> · {ttsLabel}</>}
            </span>
          </p>
        )}
        <audio ref={audioRef} controls data-testid="tts-audio" style={{ width: "100%" }} />
      </section>
    </div>
  );
}
