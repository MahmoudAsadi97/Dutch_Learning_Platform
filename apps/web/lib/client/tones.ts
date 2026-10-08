"use client";

import { useSyncExternalStore } from "react";

import { storageKeys } from "@/lib/client/storage";

/**
 * Short synthesised tones for answers and the daily goal: two or three sine notes through Web Audio, no
 * asset files. Off by default, a device preference, and silent when the system asks for less motion.
 */

export type Tone = "correct" | "almost" | "incorrect" | "goal";

const NOTES: Record<Tone, { frequencies: number[]; step: number; gain: number }> = {
  correct: { frequencies: [523.25, 659.25], step: 0.09, gain: 0.08 },
  almost: { frequencies: [523.25, 587.33], step: 0.1, gain: 0.06 },
  incorrect: { frequencies: [392], step: 0.12, gain: 0.05 },
  goal: { frequencies: [523.25, 659.25, 783.99, 1046.5], step: 0.11, gain: 0.08 },
};

const changeEvent = "taalstudio:tones";
let volatile = false;

export function readTonesEnabled(): boolean {
  try {
    return localStorage.getItem(storageKeys.tones) === "on";
  } catch {
    return volatile;
  }
}

export function setTonesEnabled(enabled: boolean): void {
  volatile = enabled;
  try {
    localStorage.setItem(storageKeys.tones, enabled ? "on" : "off");
  } catch {
    /* Storage may be disabled. */
  }
  window.dispatchEvent(new Event(changeEvent));
}

function subscribe(listener: () => void) {
  window.addEventListener(changeEvent, listener);
  window.addEventListener("storage", listener);
  return () => {
    window.removeEventListener(changeEvent, listener);
    window.removeEventListener("storage", listener);
  };
}

export function useTonesEnabled(): boolean {
  return useSyncExternalStore(subscribe, readTonesEnabled, () => false);
}

type AudioContextCtor = typeof AudioContext;
let context: AudioContext | null = null;

function audioContext(): AudioContext | null {
  if (typeof window === "undefined") return null;
  const Ctor: AudioContextCtor | undefined =
    window.AudioContext ?? (window as Window & { webkitAudioContext?: AudioContextCtor }).webkitAudioContext;
  if (!Ctor) return null;
  context ??= new Ctor();
  return context;
}

function reducedMotion(): boolean {
  return typeof window !== "undefined" && !!window.matchMedia?.("(prefers-reduced-motion: reduce)").matches;
}

/** Plays a tone when tones are on and motion is not reduced; never throws. */
export function playTone(tone: Tone): void {
  if (!readTonesEnabled() || reducedMotion()) return;
  try {
    const ctx = audioContext();
    if (!ctx) return;
    if (ctx.state === "suspended") void ctx.resume();
    const { frequencies, step, gain } = NOTES[tone];
    const start = ctx.currentTime + 0.01;
    frequencies.forEach((frequency, index) => {
      const oscillator = ctx.createOscillator();
      const volume = ctx.createGain();
      oscillator.type = "sine";
      oscillator.frequency.value = frequency;
      const at = start + index * step;
      volume.gain.setValueAtTime(0, at);
      volume.gain.linearRampToValueAtTime(gain, at + 0.015);
      volume.gain.exponentialRampToValueAtTime(0.0001, at + step * 1.6);
      oscillator.connect(volume).connect(ctx.destination);
      oscillator.start(at);
      oscillator.stop(at + step * 1.7);
    });
  } catch {
    /* Audio is optional. */
  }
}
