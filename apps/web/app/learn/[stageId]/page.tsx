import { notFound } from "next/navigation";
import { GuidedStudyWorkspace } from "@/components/GuidedStudyWorkspace";
import { isStageId, isSkill } from "@/lib/domain/registry";
import { studyStep } from "@/lib/client/study";

export default async function LevelPage({
  params,
  searchParams,
}: {
  params: Promise<{ stageId: string }>;
  searchParams: Promise<{
    skill?: string | string[];
    topic?: string | string[];
    section?: string | string[];
    activity?: string | string[];
    part?: string | string[];
    step?: string | string[];
    view?: string | string[];
  }>;
}) {
  const { stageId } = await params;
  const query = await searchParams;
  if (!isStageId(stageId)) notFound();
  const skill = typeof query.skill === "string" && isSkill(query.skill) ? query.skill : "reading";
  const identifier = (value: unknown) =>
    typeof value === "string" && /^[a-z0-9-]{1,100}$/.test(value) ? value : undefined;
  const topic = identifier(query.topic);
  const view =
    query.view === "vocabulary" || query.section === "words"
      ? "vocabulary"
      : query.view === "alphabet" || query.section === "alphabet"
        ? "alphabet"
        : query.section === "grammar"
          ? "grammar"
          : typeof query.view === "string" &&
              ["grammar", "personal-words", "personal-stories"].includes(query.view)
            ? query.view
            : undefined;
  return (
    <GuidedStudyWorkspace
      key={`${stageId}.${skill}.${topic ?? ""}`}
      stageId={stageId}
      skill={skill}
      topicId={topic}
      activityId={identifier(query.activity)}
      initialPart={identifier(query.part)}
      initialStep={studyStep(typeof query.step === "string" ? query.step : undefined)}
      initialView={view}
    />
  );
}
