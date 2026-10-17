import { isSkill, isStageId, stageLabel } from "../domain/registry";
export const ACTIVITIES = [
  "reading",
  "listening",
  "speaking",
  "writing",
  "words",
  "grammar",
  "stories",
  "alphabet",
] as const;
export type LearningActivity = (typeof ACTIVITIES)[number];
export function isActivity(value: unknown): value is LearningActivity {
  return typeof value === "string" && (ACTIVITIES as readonly string[]).includes(value);
}
export function activityHref(stage: string, activity: LearningActivity): string {
  if (!isStageId(stage)) return "/leerpad";
  const chosen = activity === "alphabet" && stage !== "pre-a1" ? "words" : activity;
  return `/learn/${stage}?${isSkill(chosen) ? "skill" : "section"}=${chosen}`;
}
export function activityLabel(stage: string, activity: LearningActivity): string {
  return `${stageLabel(stage)} · ${activity}`;
}
