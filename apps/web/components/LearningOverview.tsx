"use client";

import type { IconName } from "@/components/Icon";
import type { Skill } from "@/lib/types";
import { CurriculumPath } from "@/components/CurriculumPath";
import { skillList } from "@/lib/domain/registry";

export const skills: {
  key: Skill;
  label: string;
  description: string;
  icon: IconName;
  color: string;
}[] = skillList.map((skill) => ({
  key: skill.key,
  label: skill.label.nl,
  description: skill.description,
  icon: skill.icon,
  color: skill.tone,
}));

export function LearningOverview() {
  return <CurriculumPath />;
}
