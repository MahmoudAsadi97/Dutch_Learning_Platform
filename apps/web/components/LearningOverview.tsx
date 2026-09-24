"use client";

import type { IconName } from "@/components/Icon";
import type { Skill } from "@/lib/types";
import { CurriculumPath } from "@/components/CurriculumPath";

export const skills: {
  key: Skill;
  label: string;
  description: string;
  icon: IconName;
  color: string;
}[] = [
  {
    key: "reading",
    label: "Lezen",
    description: "Begrijp wat er staat.",
    icon: "book",
    color: "sage",
  },
  {
    key: "listening",
    label: "Luisteren",
    description: "Hoor wat ertoe doet.",
    icon: "headphones",
    color: "sand",
  },
  {
    key: "speaking",
    label: "Spreken",
    description: "Vind de juiste woorden.",
    icon: "mic",
    color: "lilac",
  },
  {
    key: "writing",
    label: "Schrijven",
    description: "Maak je boodschap duidelijk.",
    icon: "pen",
    color: "peach",
  },
];


export function LearningOverview() { return <CurriculumPath />; }
