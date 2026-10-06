/**
 * The twelve stages and the four skills, in one place.
 *
 * Pure data: no React or Next imports, so the node:test suite can load it directly. Components and
 * client modules import labels, order and tones from here instead of keeping their own copies.
 */

export const STAGE_IDS = [
  "pre-a1",
  "a1",
  "pre-a2",
  "a2",
  "pre-b1",
  "b1",
  "pre-b2",
  "b2",
  "pre-c1",
  "c1",
  "pre-c2",
  "c2",
] as const;
export type StageId = (typeof STAGE_IDS)[number];

export function isStageId(value: string): value is StageId {
  return (STAGE_IDS as readonly string[]).includes(value);
}

/** "pre-a1" -> "pre-A1", "b2" -> "B2". Unknown ids are returned unchanged. */
export function stageLabel(id: string): string {
  return id.replace(
    /([abc])([12])$/,
    (_, letter: string, number: string) => `${letter.toUpperCase()}${number}`,
  );
}

/** Keyed by string because stage ids arrive from API payloads; unknown ids read as undefined. */
export const stageLabels: Record<string, string> = Object.fromEntries(
  STAGE_IDS.map((id) => [id, stageLabel(id)]),
);

export const SKILLS = ["reading", "listening", "speaking", "writing"] as const;
export type Skill = (typeof SKILLS)[number];

export function isSkill(value: string): value is Skill {
  return (SKILLS as readonly string[]).includes(value);
}

export interface SkillInfo {
  key: Skill;
  label: { nl: string; en: string; fa: string };
  /** One line under the label on the overview cards. */
  description: string;
  /** Name in components/Icon.tsx. */
  icon: "book" | "headphones" | "mic" | "pen";
  /** Legacy colour class on `.icon-tile` until the token-driven accents land (roadmap P1). */
  tone: "sage" | "sand" | "lilac" | "peach";
}

export const skills: Record<Skill, SkillInfo> = {
  reading: {
    key: "reading",
    label: { nl: "Lezen", en: "Reading", fa: "خواندن" },
    description: "Begrijp wat er staat.",
    icon: "book",
    tone: "sage",
  },
  listening: {
    key: "listening",
    label: { nl: "Luisteren", en: "Listening", fa: "شنیدن" },
    description: "Hoor wat ertoe doet.",
    icon: "headphones",
    tone: "sand",
  },
  speaking: {
    key: "speaking",
    label: { nl: "Spreken", en: "Speaking", fa: "گفتن" },
    description: "Vind de juiste woorden.",
    icon: "mic",
    tone: "lilac",
  },
  writing: {
    key: "writing",
    label: { nl: "Schrijven", en: "Writing", fa: "نوشتن" },
    description: "Maak je boodschap duidelijk.",
    icon: "pen",
    tone: "peach",
  },
};

export const skillOrder: Skill[] = [...SKILLS];

/** Dutch skill names, the shape most components expect. */
export const skillNames: Record<Skill, string> = Object.fromEntries(
  SKILLS.map((key) => [key, skills[key].label.nl]),
) as Record<Skill, string>;

export const skillList: SkillInfo[] = SKILLS.map((key) => skills[key]);
