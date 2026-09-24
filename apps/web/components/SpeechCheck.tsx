"use client";

import { useEffect, useRef, useState } from "react";
import { Icon } from "@/components/Icon";

import { ApiError, apiFetch, apiJson, newRequestId } from "@/lib/client/api";
import { usePlayback } from "@/lib/client/playback";
import { type Recording, talkButtonHandlers, useRecorder } from "@/lib/client/recorder";

interface TranscriptResponse {
  request_id: string;
  transcript: { text: string; language: string; provider: string; model: string; latency_ms: number };
  audio: {
    asset_id: string;
    source: { container: string; codec: string; duration_seconds: number; sample_rate: number; channels: number };
    canonical: { container: string; codec: string; duration_seconds: number; sample_rate: number; channels: number };
  };
}

type Phase = "idle" | "recording" | "uploading" | "done" | "error" | "unsupported";

/**
 * Push-to-talk microphone check: MediaRecorder → upload → ffmpeg → transcription, plus synthetic playback.
 * Hold the button (mouse, touch or the space bar) while speaking a Dutch sentence.
 */
export function SpeechCheck() {
  const [uploadPhase, setUploadPhase] = useState<"idle" | "uploading" | "done" | "error">("idle");
  const [result, setResult] = useState<TranscriptResponse | null>(null);
  const [error, setError] = useState<string>("");
  const [ttsText, setTtsText] = useState("Goeiedag, ik wil graag Nederlands oefenen.");
  const [ttsLabel, setTtsLabel] = useState<string>("");
  const [ttsBusy, setTtsBusy] = useState(false);
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const recordingUrlRef = useRef("");
  const [recordingUrl, setRecordingUrl] = useState("");
  useEffect(() => () => { if (recordingUrlRef.current) URL.revokeObjectURL(recordingUrlRef.current); }, []);
  const playback = usePlayback();

  async function upload(recording: Recording) {
    setUploadPhase("uploading");
    setError("");
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
      setError(cause instanceof ApiError ? "Uw opname kon niet worden verwerkt. Probeer opnieuw." : "Upload mislukt.");
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
    setError("");
    try {
      const response = await apiFetch("speech/synthesize", { method: "POST", body: { text: ttsText } });
      if (!response.ok) {
        const payload = (await response.json().catch(() => ({}))) as { detail?: string };
        throw new ApiError(response.status, payload.detail ?? response.statusText, response.headers.get("x-request-id") ?? "");
      }
      setTtsLabel(response.headers.get("x-audio-label") ?? "unknown");
      const wav = await response.blob();
      const outcome = await playback.play(wav);
      if (audioRef.current) audioRef.current.src = outcome.url;
      if (outcome.failed) setError("Afspelen mislukt; gebruik de afspeelknop van de speler.");
      else if (outcome.blocked) setError("Automatisch afspelen is geblokkeerd; gebruik de afspeelknop van de speler.");
    } catch (cause) {
      setError(cause instanceof ApiError ? `Synthese mislukt: ${cause.detail}` : "Afspelen mislukt; gebruik de afspeelknop van de speler.");
    } finally {
      setTtsBusy(false);
    }
  }

  const mimeType = recorder.mimeType;
  const effectivePhase: Phase =
    recorder.phase === "unsupported" ? "unsupported" : recorder.phase === "recording" ? "recording" : uploadPhase;
  const recording = effectivePhase === "recording";
  const shownError = error || recorder.error;

  return (
    <div className="grid two speech-studio">
      <section className="card" aria-labelledby="record-heading">
        <span className="eyebrow">01 · JOUW STEM</span>
        <h2 id="record-heading">Opnemen en transcriberen</h2>
        <p className="muted">
          Houd de knop ingedrukt en zeg een Nederlandse zin, bijvoorbeeld: <em lang="nl">Ik wil mijn afspraak verzetten.</em>
        </p>
        <div className={`mic-orbit ${recording ? "recording" : ""}`} aria-hidden="true"><Icon name="mic" size={32} /></div>
        <details className="lesson-details"><summary>Opnameformaat</summary><p className="mono" data-testid="mime-type">
          MediaRecorder: {mimeType === undefined ? "controleren…" : mimeType === null ? "niet ondersteund" : mimeType || "standaardformaat van de browser"}
        </p></details>
        <button
          type="button"
          className="button talk"
          aria-pressed={recording}
          disabled={effectivePhase === "unsupported" || effectivePhase === "uploading"}
          {...talkButtonHandlers(() => void recorder.start(), recorder.stop)}
          data-testid="talk-button"
        >
          {recording ? "Opname loopt… laat los om te stoppen" : effectivePhase === "uploading" ? "Verwerken…" : "Houd ingedrukt om te spreken"}
        </button>
        <p role="status" aria-live="polite" data-testid="phase">
          {effectivePhase === "idle" && "Klaar om op te nemen."}
          {effectivePhase === "recording" && "Opname loopt."}
          {effectivePhase === "uploading" && "Uploaden, converteren en transcriberen…"}
          {effectivePhase === "done" && "Klaar."}
          {effectivePhase === "unsupported" && "Deze browser ondersteunt MediaRecorder niet."}
          {effectivePhase === "error" && "Er ging iets mis."}
        </p>
        {recordingUrl && <div className="record-playback"><h3>Jouw opname</h3><audio controls src={recordingUrl} aria-label="Luister naar je eigen opname" style={{ width: "100%" }} /><p className="small-text muted">Alleen in dit tabblad beschikbaar. De opname wordt voor deze microfoontest niet in de opslag bewaard.</p></div>}
        {shownError && (
          <p className="error" role="alert">
            {shownError}
          </p>
        )}
        {result && (
          <div data-testid="transcript-result">
            <h3>Transcriptie</h3>
            <p className="dutch-text" lang="nl" data-testid="transcript-text">
              {result.transcript.text || "(leeg)"}
            </p>
            <p className="muted">Vergelijk de tekst met wat u zei. Een transcriptie kan fouten bevatten.</p>
          </div>
        )}
      </section>

      <section className="card" aria-labelledby="tts-heading">
        <span className="eyebrow">02 · LUISTER EN VERGELIJK</span>
        <h2 id="tts-heading">Synthetische stem</h2>
        <p className="muted">Een kunstmatige stem als luistervoorbeeld, altijd gelabeld. Geen menselijke opname of uitspraakbeoordeling.</p>
        <label htmlFor="tts-text" className="visually-hidden">
          Tekst om uit te spreken
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
          <button type="button" className="button" onClick={() => void playSynthesis()} disabled={ttsBusy} data-testid="tts-button">
            {ttsBusy ? "Bezig…" : "Speel af"}
          </button>
        </p>
        {ttsLabel && (
          <p>
            <span className="label warn" data-testid="tts-label">
              audio: {ttsLabel}
            </span>
          </p>
        )}
        <audio ref={audioRef} controls data-testid="tts-audio" style={{ width: "100%" }} />
      </section>
    </div>
  );
}
