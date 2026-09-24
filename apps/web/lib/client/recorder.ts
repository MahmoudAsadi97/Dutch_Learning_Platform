"use client";

import { useCallback, useEffect, useRef, useState, useSyncExternalStore } from "react";
import { observeNativeAudioFocus, suspendAudioForRecording } from "@/lib/client/audio-focus";
import { MicrophoneRequestGate } from "@/lib/client/microphone-request";

const MIME_CANDIDATES = ["audio/webm;codecs=opus", "audio/webm", "audio/ogg;codecs=opus", "audio/mp4", "audio/mpeg"];

export type RecorderPhase = "idle" | "recording" | "unsupported";

/** People release the button on the last syllable; this tail keeps the final word from being cut. */
export const STOP_TAIL_MS = 400;

export interface Recording {
  blob: Blob;
  mimeType: string;
  /** File name with the extension ffmpeg expects for this container. */
  fileName: string;
}

/** The MediaRecorder container this browser can produce: `null` when unsupported, `""` for the browser default. */
export function pickMimeType(): string | null {
  if (typeof MediaRecorder === "undefined") return null;
  for (const candidate of MIME_CANDIDATES) {
    if (MediaRecorder.isTypeSupported(candidate)) return candidate;
  }
  return "";
}

export function fileNameFor(mimeType: string): string {
  const extension = mimeType.includes("webm") ? "webm" : mimeType.includes("ogg") ? "ogg" : mimeType.includes("mp4") ? "m4a" : "bin";
  return `recording.${extension}`;
}

const noSubscription = () => () => {};
/** Browser capability, read once on the client; the server renders "unknown" (undefined) until hydration. */
export function useMimeType(): string | null | undefined {
  return useSyncExternalStore(noSubscription, pickMimeType, () => undefined);
}

/**
 * Push-to-talk recorder: `start()` asks for the microphone and records, `stop()` ends the recording and
 * hands the blob to `onRecording`. The microphone is released after every recording and on unmount.
 */
export function useRecorder(onRecording: (recording: Recording) => void) {
  useEffect(observeNativeAudioFocus, []);
  const mimeType = useMimeType();
  const [phase, setPhase] = useState<RecorderPhase>("idle");
  const [error, setError] = useState<string>("");
  const recorderRef = useRef<MediaRecorder | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const stopTimerRef = useRef<number | null>(null);
  const callbackRef = useRef(onRecording);
  const requestGate = useRef(new MicrophoneRequestGate());
  const releaseAudioRef = useRef<(() => void) | null>(null);
  const mounted = useRef(false);

  useEffect(() => {
    callbackRef.current = onRecording;
  });

  useEffect(() => {
    mounted.current = true;
    const gate = requestGate.current;
    return () => {
      mounted.current = false;
      gate.cancel();
      if (stopTimerRef.current !== null) window.clearTimeout(stopTimerRef.current);
      const recorder = recorderRef.current;
      if (recorder && recorder.state !== "inactive") {
        recorder.onstop = null;
        recorder.stop();
      }
      streamRef.current?.getTracks().forEach((track) => track.stop());
      streamRef.current = null;
      releaseAudioRef.current?.(); releaseAudioRef.current = null;
    };
  }, []);

  const start = useCallback(async () => {
    if (requestGate.current.isPending() || (recorderRef.current && recorderRef.current.state === "recording")) return;
    setError("");
    const releaseAudio = suspendAudioForRecording();
    releaseAudioRef.current = releaseAudio;
    const release = () => { releaseAudio(); if (releaseAudioRef.current === releaseAudio) releaseAudioRef.current = null; };
    try {
      const stream = await requestGate.current.open(() => navigator.mediaDevices.getUserMedia({ audio: true }));
      if (!stream) { release(); return; }
      if (!mounted.current) { stream.getTracks().forEach(track => track.stop()); release(); return; }
      streamRef.current = stream;
      const recorder = mimeType ? new MediaRecorder(stream, { mimeType }) : new MediaRecorder(stream);
      const chunks: Blob[] = [];
      recorder.ondataavailable = (event) => {
        if (event.data.size > 0) chunks.push(event.data);
      };
      recorder.onstop = () => {
        stream.getTracks().forEach(track => track.stop());
        if (streamRef.current === stream) streamRef.current = null;
        release();
        if (!mounted.current || recorderRef.current !== recorder) return;
        const actualMime = recorder.mimeType || mimeType || "application/octet-stream";
        const blob = new Blob(chunks, { type: actualMime });
        setPhase("idle");
        callbackRef.current({ blob, mimeType: actualMime, fileName: fileNameFor(actualMime) });
      };
      recorder.start(250);
      recorderRef.current = recorder;
      setPhase("recording");
    } catch (cause) {
      streamRef.current?.getTracks().forEach(track => track.stop()); streamRef.current = null;
      release();
      if (!mounted.current) return;
      setPhase("idle");
      setError(cause instanceof Error ? `Microfoon niet beschikbaar: ${cause.message}` : "Microfoon niet beschikbaar.");
    }
  }, [mimeType]);

  const stop = useCallback(() => {
    if (requestGate.current.isPending()) {
      requestGate.current.cancel();
      releaseAudioRef.current?.(); releaseAudioRef.current = null;
      return;
    }
    const recorder = recorderRef.current;
    if (!recorder || recorder.state !== "recording" || stopTimerRef.current !== null) return;
    stopTimerRef.current = window.setTimeout(() => {
      stopTimerRef.current = null;
      if (recorder.state === "recording") recorder.stop();
      streamRef.current?.getTracks().forEach((track) => track.stop());
      streamRef.current = null;
    }, STOP_TAIL_MS);
  }, []);

  const effectivePhase: RecorderPhase = mimeType === null ? "unsupported" : phase;
  return { mimeType, phase: effectivePhase, error, start, stop };
}

/** Event handlers for a hold-to-talk button: pointer down/up and the space bar. */
export function talkButtonHandlers(start: () => void, stop: () => void) {
  return {
    onPointerDown: (event: { preventDefault(): void }) => {
      event.preventDefault();
      start();
    },
    onPointerUp: stop,
    onPointerLeave: stop,
    onPointerCancel: stop,
    onKeyDown: (event: { key: string; repeat: boolean; preventDefault(): void }) => {
      if (event.key === " " && !event.repeat) {
        event.preventDefault();
        start();
      }
    },
    onKeyUp: (event: { key: string; preventDefault(): void }) => {
      if (event.key === " ") {
        event.preventDefault();
        stop();
      }
    },
  };
}
