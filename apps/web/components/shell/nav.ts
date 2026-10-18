import type { IconName } from "@/components/Icon";
import type { Accent } from "@/lib/design/identity";
import type { uiCopy } from "@/lib/ui-copy";

/** A key into the navigation copy; the shell looks the text up, so this table stays free of runtime imports. */
export type NavCopyKey = keyof (typeof uiCopy)["nav"];

/**
 * One learning entrance and the dashboard, with progress and settings beside them. Every entry is a plain
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
  /** Which entry of `uiCopy.nav` holds the label with its glosses. */
  copy: NavCopyKey;
}

export const destinations: NavItem[] = [
  {
    href: "/",
    label: "Dashboard",
    short: "Dashboard",
    icon: "calendar",
    accent: "today",
    copy: "today",
  },
  { href: "/leerpad", label: "Leren", short: "Leren", icon: "flag", accent: "path", copy: "learn" },
];

export const rooms: NavItem[] = [
  {
    href: "/progress",
    label: "Voortgang",
    short: "Voortgang",
    icon: "chart",
    accent: "progress",
    copy: "progress",
  },
  {
    href: "/settings",
    label: "Instellingen",
    short: "Instellingen",
    icon: "settings",
    accent: "neutral",
    copy: "settings",
  },
];

const SECTION_BY_SEGMENT: Record<string, string> = {
  "": "/",
  leerpad: "/leerpad",
  learn: "/leerpad",
  examens: "/leerpad",
  verhalen: "/leerpad",
  videos: "/leerpad",
  spreken: "/leerpad",
  missions: "/leerpad",
  "speech-check": "/leerpad",
  woorden: "/leerpad",
  oefenen: "/leerpad",
  progress: "/progress",
  settings: "/settings",
  // "Over de inhoud" is reached from Instellingen and belongs to that room
  over: "/settings",
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
