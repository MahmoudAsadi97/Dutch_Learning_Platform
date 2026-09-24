import { CurriculumLesson } from "@/components/CurriculumLesson";

export default async function LevelPage({ params }: { params: Promise<{ stageId: string }> }) {
  const { stageId } = await params;
  return <CurriculumLesson key={stageId} stageId={stageId}/>;
}
