import type { IconName } from "@/components/Icon";
import type { Accent } from "@/lib/design/identity";

/**
 * The five destinations a learner moves between, and the two rooms beside them. Every entry is a plain
 * link rendered inside `.app-frame`, so the navigation guard that waits for a draft to save still sees
 * each click. Labels are plain Dutch until the gloss layer lands (roadmap P2).
 */
export interface NavItem {
  href: string;
  label: string;
  /** The word under the icon in the bottom tabs. */
  short: string;
  icon: IconName;
  accent: Accent;
}

export const destinations: NavItem[] = [
  { href: "/", label: "Vandaag", short: "Vandaag", icon: "calendar", accent: "today" },
  { href: "/leerpad", label: "Leren", short: "Leren", icon: "flag", accent: "path" },
  { href: "/verhalen", label: "Verhalen", short: "Verhalen", icon: "book", accent: "stories" },
  { href: "/spreken", label: "Spreken", short: "Spreken", icon: "message", accent: "conversations" },
  { href: "/woorden", label: "Woorden", short: "Woorden", icon: "star", accent: "words" },
];

export const rooms: NavItem[] = [
  { href: "/progress", label: "Voortgang", short: "Voortgang", icon: "chart", accent: "progress" },
  { href: "/settings", label: "Instellingen", short: "Instellingen", icon: "settings", accent: "neutral" },
];

const SECTION_BY_SEGMENT: Record<string, string> = {
  "": "/",
  leerpad: "/leerpad",
  learn: "/leerpad",
  verhalen: "/verhalen",
  videos: "/verhalen",
  spreken: "/spreken",
  missions: "/spreken",
  "speech-check": "/spreken",
  woorden: "/woorden",
  progress: "/progress",
  settings: "/settings",
};

/** The destination (or room) a path belongs to, or null for a path the shell does not know. */
export function navSection(path: string): string | null {
  const segment = path.replace(/^\/+/, "").split(/[/?#]/)[0] ?? "";
  return SECTION_BY_SEGMENT[segment] ?? null;
}

/** The nav item a path belongs to; the first destination when the path is unknown. */
export function navItemFor(path: string): NavItem {
  const section = navSection(path);
  return [...destinations, ...rooms].find((item) => item.href === section) ?? destinations[0];
}
