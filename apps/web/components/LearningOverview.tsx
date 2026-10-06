"use client";

import type { IconName } from "@/components/Icon";
import type { Skill } from "@/lib/types";
import { CurriculumPath } from "@/components/CurriculumPath";
import { skillAccent, type Accent } from "@/lib/design/identity";
import { skillList } from "@/lib/domain/registry";

export const skills: {
  key: Skill;
  label: string;
  description: string;
  icon: IconName;
  accent: Accent;
}[] = skillList.map((skill) => ({
  key: skill.key,
  label: skill.label.nl,
  description: skill.description,
  icon: skill.icon,
  accent: skillAccent[skill.key],
}));

export function LearningOverview() {
  return <CurriculumPath />;
}
