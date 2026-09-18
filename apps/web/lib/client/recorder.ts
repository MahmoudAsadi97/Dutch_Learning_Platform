"use client";

import { useCallback, useEffect, useRef, useState, useSyncExternalStore } from "react";

const MIME_CANDIDATES = ["audio/webm;codecs=opus", "audio/webm", "audio/ogg;codecs=opus", "audio/mp4", "audio/mpeg"];

export type RecorderPhase = "idle" | "recording" | "unsupported";

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
  const mimeType = useMimeType();
  const [phase, setPhase] = useState<RecorderPhase>("idle");
  const [error, setError] = useState<string>("");
  const recorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const streamRef = useRef<MediaStream | null>(null);
  const callbackRef = useRef(onRecording);

  useEffect(() => {
    callbackRef.current = onRecording;
  });

  useEffect(() => {
    return () => {
      const recorder = recorderRef.current;
      if (recorder && recorder.state !== "inactive") {
        recorder.onstop = null;
        recorder.stop();
      }
      streamRef.current?.getTracks().forEach((track) => track.stop());
      streamRef.current = null;
    };
  }, []);

  const start = useCallback(async () => {
    if (recorderRef.current && recorderRef.current.state === "recording") return;
    setError("");
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      streamRef.current = stream;
      const recorder = mimeType ? new MediaRecorder(stream, { mimeType }) : new MediaRecorder(stream);
      chunksRef.current = [];
      recorder.ondataavailable = (event) => {
        if (event.data.size > 0) chunksRef.current.push(event.data);
      };
      recorder.onstop = () => {
        const actualMime = recorder.mimeType || mimeType || "application/octet-stream";
        const blob = new Blob(chunksRef.current, { type: actualMime });
        chunksRef.current = [];
        setPhase("idle");
        callbackRef.current({ blob, mimeType: actualMime, fileName: fileNameFor(actualMime) });
      };
      recorder.start(250);
      recorderRef.current = recorder;
      setPhase("recording");
    } catch (cause) {
      setPhase("idle");
      setError(cause instanceof Error ? `Microfoon niet beschikbaar: ${cause.message}` : "Microfoon niet beschikbaar.");
    }
  }, [mimeType]);

  const stop = useCallback(() => {
    const recorder = recorderRef.current;
    if (!recorder || recorder.state !== "recording") return;
    recorder.stop();
    streamRef.current?.getTracks().forEach((track) => track.stop());
    streamRef.current = null;
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
