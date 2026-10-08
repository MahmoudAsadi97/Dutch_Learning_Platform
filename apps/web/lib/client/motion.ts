"use client";

import { useSyncExternalStore } from "react";

const QUERY = "(prefers-reduced-motion: reduce)";

function subscribe(listener: () => void) {
  if (typeof window === "undefined" || !window.matchMedia) return () => undefined;
  const media = window.matchMedia(QUERY);
  media.addEventListener("change", listener);
  return () => media.removeEventListener("change", listener);
}

function read() {
  return typeof window !== "undefined" && !!window.matchMedia && window.matchMedia(QUERY).matches;
}

/** True when the person asked the operating system for less motion; the server render assumes false. */
export function usePrefersReducedMotion(): boolean {
  return useSyncExternalStore(subscribe, read, () => false);
}

/** The animation data attribute for a state, or none when motion is reduced. Pure, so it is unit-tested. */
export function animFor(
  state: "correct" | "incorrect" | "almost" | "reveal" | "celebrate" | "enter" | "none",
  reducedMotion: boolean,
): "pop" | "shake" | "rise" | "burst" | undefined {
  if (reducedMotion || state === "none") return undefined;
  switch (state) {
    case "correct":
      return "pop";
    case "incorrect":
      return "shake";
    case "almost":
    case "reveal":
    case "enter":
      return "rise";
    case "celebrate":
      return "burst";
  }
}

/** Runs `update` inside a view transition when the browser offers one, otherwise directly. */
export function withViewTransition(update: () => void, reducedMotion = false): void {
  const doc = typeof document !== "undefined" ? document : undefined;
  if (!reducedMotion && doc && "startViewTransition" in doc) {
    (doc as Document & { startViewTransition: (cb: () => void) => unknown }).startViewTransition(update);
    return;
  }
  update();
}
