import assert from "node:assert/strict";
import { test } from "node:test";
import {
  STAGE_IDS,
  SKILLS,
  isSkill,
  isStageId,
  skillNames,
  skillOrder,
  skills,
  stageLabel,
  stageLabels,
} from "../../lib/domain/registry.ts";

test("twelve stages in course order with display labels", () => {
  assert.equal(STAGE_IDS.length, 12);
  assert.deepEqual(STAGE_IDS.slice(0, 4), ["pre-a1", "a1", "pre-a2", "a2"]);
  assert.equal(STAGE_IDS.at(-1), "c2");
  assert.equal(stageLabel("pre-a1"), "pre-A1");
  assert.equal(stageLabel("b2"), "B2");
  assert.equal(stageLabel("unknown"), "unknown");
  assert.equal(stageLabels["pre-c2"], "pre-C2");
  assert.ok(isStageId("a1") && !isStageId("a3"));
});

test("four skills with trilingual labels, an icon and a description", () => {
  assert.deepEqual([...SKILLS], ["reading", "listening", "speaking", "writing"]);
  assert.deepEqual(skillOrder, [...SKILLS]);
  for (const key of SKILLS) {
    const info = skills[key];
    assert.equal(info.key, key);
    for (const language of ["nl", "en", "fa"])
      assert.ok(info.label[language].length > 0, `${key} ${language}`);
    assert.ok(info.icon && info.description);
  }
  assert.deepEqual(skillNames, {
    reading: "Lezen",
    listening: "Luisteren",
    speaking: "Spreken",
    writing: "Schrijven",
  });
  assert.ok(isSkill("writing") && !isSkill("grammar"));
});
