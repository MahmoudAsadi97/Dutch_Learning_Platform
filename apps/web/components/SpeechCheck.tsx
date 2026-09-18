"use client";

import { useEffect, useRef, useState } from "react";

import { ApiError, apiFetch, apiJson, newRequestId } from "@/lib/client/api";
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
  const [ttsText, setTtsText] = useState("Goeiedag, u spreekt met Tandartspraktijk Molenstraat.");
  const [ttsLabel, setTtsLabel] = useState<string>("");
  const [ttsBusy, setTtsBusy] = useState(false);
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const objectUrlRef = useRef<string | null>(null);

  // Release the playback buffer when the page goes away (navigation, hot reload).
  useEffect(() => {
    return () => {
      if (objectUrlRef.current) {
        URL.revokeObjectURL(objectUrlRef.current);
        objectUrlRef.current = null;
      }
    };
  }, []);

  async function upload(recording: Recording) {
    setUploadPhase("uploading");
    setError("");
    setResult(null);
    const form = new FormData();
    form.append("audio", recording.blob, recording.fileName);
    form.append("keep_recording", "true");
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
      setError(cause instanceof ApiError ? `${cause.detail} (request ${cause.requestId})` : "Upload mislukt.");
    }
  }

  const recorder = useRecorder((recording) => void upload(recording));

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
      const audio = audioRef.current;
      if (audio) {
        // Replacing the source while a previous load is pending makes the browser abort that load;
        // pause first and drop the old buffer so the abort is expected and never surfaces as an error.
        audio.pause();
        if (objectUrlRef.current) URL.revokeObjectURL(objectUrlRef.current);
        const url = URL.createObjectURL(wav);
        objectUrlRef.current = url;
        audio.src = url;
        try {
          await audio.play();
        } catch (cause) {
          const name = cause instanceof DOMException ? cause.name : "";
          // AbortError: load interrupted (new source, page change). NotAllowedError: autoplay policy; the controls still work.
          if (name !== "AbortError" && name !== "NotAllowedError") throw cause;
        }
      }
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
    <div className="grid two">
      <section className="card" aria-labelledby="record-heading">
        <h2 id="record-heading">Opnemen en transcriberen</h2>
        <p className="muted">
          Houd de knop ingedrukt en zeg een Nederlandse zin, bijvoorbeeld: <em lang="nl">Ik wil mijn afspraak verzetten.</em>
        </p>
        <p className="mono" data-testid="mime-type">
          MediaRecorder: {mimeType === undefined ? "controleren…" : mimeType === null ? "niet ondersteund" : mimeType || "standaardformaat van de browser"}
        </p>
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
            <table className="plain">
              <tbody>
                <tr>
                  <th scope="row">Provider</th>
                  <td>
                    {result.transcript.provider} · {result.transcript.model} · {result.transcript.latency_ms} ms
                  </td>
                </tr>
                <tr>
                  <th scope="row">Upload</th>
                  <td>
                    {result.audio.source.container} / {result.audio.source.codec} · {result.audio.source.sample_rate} Hz ·{" "}
                    {result.audio.source.channels} kanaal/kanalen · {result.audio.source.duration_seconds.toFixed(2)} s
                  </td>
                </tr>
                <tr>
                  <th scope="row">Canoniek</th>
                  <td>
                    {result.audio.canonical.container} / {result.audio.canonical.codec} · {result.audio.canonical.sample_rate} Hz ·{" "}
                    {result.audio.canonical.channels} kanaal · {result.audio.canonical.duration_seconds.toFixed(2)} s
                  </td>
                </tr>
                <tr>
                  <th scope="row">Request</th>
                  <td className="mono">{result.request_id}</td>
                </tr>
              </tbody>
            </table>
          </div>
        )}
      </section>

      <section className="card" aria-labelledby="tts-heading">
        <h2 id="tts-heading">Synthetische stem</h2>
        <p className="muted">Ontwikkelaudio, altijd gelabeld. Geen menselijke opname.</p>
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
