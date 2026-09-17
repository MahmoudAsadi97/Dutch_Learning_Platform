"use client";

import { useRef, useState, useSyncExternalStore } from "react";

import { ApiError, apiFetch, apiJson, newRequestId } from "@/lib/client/api";

const MIME_CANDIDATES = ["audio/webm;codecs=opus", "audio/webm", "audio/ogg;codecs=opus", "audio/mp4", "audio/mpeg"];

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

export function pickMimeType(): string | null {
  if (typeof MediaRecorder === "undefined") return null;
  for (const candidate of MIME_CANDIDATES) {
    if (MediaRecorder.isTypeSupported(candidate)) return candidate;
  }
  return "";
}

const noSubscription = () => () => {};
/** Browser capability, read once on the client; the server renders "unknown" until hydration. */
function useMimeType(): string | null | undefined {
  return useSyncExternalStore(noSubscription, pickMimeType, () => undefined);
}

/**
 * Push-to-talk microphone check: MediaRecorder → upload → ffmpeg → transcription, plus synthetic playback.
 * Hold the button (mouse, touch or the space bar) while speaking a Dutch sentence.
 */
export function SpeechCheck() {
  const mimeType = useMimeType();
  const [phase, setPhase] = useState<Phase>("idle");
  const [result, setResult] = useState<TranscriptResponse | null>(null);
  const [error, setError] = useState<string>("");
  const [ttsText, setTtsText] = useState("Goeiedag, u spreekt met Tandartspraktijk Molenstraat.");
  const [ttsLabel, setTtsLabel] = useState<string>("");
  const [ttsBusy, setTtsBusy] = useState(false);
  const recorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const streamRef = useRef<MediaStream | null>(null);
  const audioRef = useRef<HTMLAudioElement | null>(null);

  async function startRecording() {
    if (phase === "recording" || phase === "uploading") return;
    setError("");
    setResult(null);
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      streamRef.current = stream;
      const recorder = mimeType ? new MediaRecorder(stream, { mimeType }) : new MediaRecorder(stream);
      chunksRef.current = [];
      recorder.ondataavailable = (event) => {
        if (event.data.size > 0) chunksRef.current.push(event.data);
      };
      recorder.onstop = () => void upload(recorder.mimeType);
      recorder.start(250);
      recorderRef.current = recorder;
      setPhase("recording");
    } catch (cause) {
      setPhase("error");
      setError(cause instanceof Error ? `Microfoon niet beschikbaar: ${cause.message}` : "Microfoon niet beschikbaar.");
    }
  }

  function stopRecording() {
    const recorder = recorderRef.current;
    if (!recorder || recorder.state !== "recording") return;
    recorder.stop();
    streamRef.current?.getTracks().forEach((track) => track.stop());
    streamRef.current = null;
  }

  async function upload(actualMime: string) {
    setPhase("uploading");
    const blob = new Blob(chunksRef.current, { type: actualMime || "application/octet-stream" });
    const extension = actualMime.includes("webm") ? "webm" : actualMime.includes("ogg") ? "ogg" : actualMime.includes("mp4") ? "m4a" : "bin";
    const form = new FormData();
    form.append("audio", blob, `recording.${extension}`);
    form.append("keep_recording", "true");
    try {
      const response = await apiJson<TranscriptResponse>("speech/transcribe", {
        method: "POST",
        formData: form,
        requestId: newRequestId(),
      });
      setResult(response);
      setPhase("done");
    } catch (cause) {
      setPhase("error");
      setError(cause instanceof ApiError ? `${cause.detail} (request ${cause.requestId})` : "Upload mislukt.");
    }
  }

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
      const url = URL.createObjectURL(wav);
      if (audioRef.current) {
        audioRef.current.src = url;
        await audioRef.current.play().catch(() => undefined);
      }
    } catch (cause) {
      setError(cause instanceof ApiError ? `Synthese mislukt: ${cause.detail}` : "Synthese mislukt.");
    } finally {
      setTtsBusy(false);
    }
  }

  const effectivePhase: Phase = mimeType === null ? "unsupported" : phase;
  const recording = effectivePhase === "recording";

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
          onPointerDown={(event) => {
            event.preventDefault();
            void startRecording();
          }}
          onPointerUp={stopRecording}
          onPointerLeave={stopRecording}
          onPointerCancel={stopRecording}
          onKeyDown={(event) => {
            if (event.key === " " && !event.repeat) {
              event.preventDefault();
              void startRecording();
            }
          }}
          onKeyUp={(event) => {
            if (event.key === " ") {
              event.preventDefault();
              stopRecording();
            }
          }}
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
        {error && (
          <p className="error" role="alert">
            {error}
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
