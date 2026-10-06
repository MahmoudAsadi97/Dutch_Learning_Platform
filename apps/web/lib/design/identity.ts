import type { Skill } from "@/lib/types";

/**
 * One hue per skill and per section, applied as `data-accent` on a container. The tokens behind each
 * name live in app/styles/tokens.css; tests/unit/design-tokens.test.mjs proves every accent keeps its
 * ink readable. Green and red are never accents: they are reserved for feedback.
 */
export const ACCENTS = [
  "today",
  "path",
  "reading",
  "listening",
  "speaking",
  "writing",
  "words",
  "stories",
  "videos",
  "conversations",
  "progress",
  "neutral",
] as const;

export type Accent = (typeof ACCENTS)[number];

export const skillAccent: Record<Skill, Accent> = {
  reading: "reading",
  listening: "listening",
  speaking: "speaking",
  writing: "writing",
};

/** The five learner destinations and the two side rooms, by the first path segment. */
export const sectionAccent: Record<string, Accent> = {
  "": "today",
  leerpad: "path",
  learn: "path",
  verhalen: "stories",
  videos: "videos",
  missions: "conversations",
  woorden: "words",
  progress: "progress",
  "speech-check": "speaking",
  settings: "neutral",
};

export function accentForPath(pathname: string): Accent {
  const [segment = ""] = pathname.replace(/^\//, "").split("/");
  return sectionAccent[segment] ?? "neutral";
}
