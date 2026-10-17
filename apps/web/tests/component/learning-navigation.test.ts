import { expect, test } from "vitest";
import { ACTIVITIES, activityHref, activityLabel, isActivity } from "@/lib/client/learning-navigation";
import { STAGE_IDS, stageLabel } from "@/lib/domain/registry";

test("each of the twelve stages opens its four skills, words, grammar and stories directly", () => {
  expect(STAGE_IDS).toHaveLength(12);
  for (const stage of STAGE_IDS) {
    for (const skill of ["reading", "listening", "speaking", "writing"] as const) {
      expect(activityHref(stage, skill)).toBe(`/learn/${stage}?skill=${skill}`);
    }
    for (const section of ["words", "grammar", "stories"] as const) {
      expect(activityHref(stage, section)).toBe(`/learn/${stage}?section=${section}`);
    }
    expect(activityLabel(stage, "stories")).toBe(`${stageLabel(stage)} · stories`);
  }
});

test("alphabet is specific to pre-A1 and falls back to words at higher stages", () => {
  expect(activityHref("pre-a1", "alphabet")).toBe("/learn/pre-a1?section=alphabet");
  for (const stage of STAGE_IDS.filter((id) => id !== "pre-a1")) {
    expect(activityHref(stage, "alphabet")).toBe(`/learn/${stage}?section=words`);
  }
});

test("activity input is validated and an unknown stage returns to the level directory", () => {
  expect(ACTIVITIES).toHaveLength(8);
  for (const activity of ACTIVITIES) expect(isActivity(activity)).toBe(true);
  for (const value of [undefined, null, 1, {}, "", "videos", "A3", "Reading", "../grammar"]) {
    expect(isActivity(value)).toBe(false);
  }
  for (const stage of ["a3", "pre-a3", "../a1", "A1", ""]) {
    expect(activityHref(stage, "stories")).toBe("/leerpad");
  }
});
