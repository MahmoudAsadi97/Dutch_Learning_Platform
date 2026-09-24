import { CurriculumLesson } from "@/components/CurriculumLesson";
import { topicHref } from "@/lib/client/learning-agents";
import type { Skill } from "@/lib/types";

export default async function LevelPage({ params, searchParams }: { params: Promise<{ stageId: string }>; searchParams: Promise<{skill?: string | string[]; topic?: string | string[]}> }) {
  const { stageId } = await params;
  const query = await searchParams;
  const skill = typeof query.skill === "string" && ["reading", "listening", "speaking", "writing"].includes(query.skill) ? query.skill as Skill : undefined;
  const topic = skill && typeof query.topic === "string" && topicHref(stageId, skill, query.topic) ? query.topic : undefined;
  return <CurriculumLesson key={`${stageId}.${skill ?? "words"}.${topic ?? ""}`} stageId={stageId} initialSkill={skill} initialTopic={topic}/>;
}
