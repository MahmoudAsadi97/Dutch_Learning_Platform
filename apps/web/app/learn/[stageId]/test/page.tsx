import { CurriculumTest } from "@/components/CurriculumTest";

export default async function LevelTestPage({ params }: { params: Promise<{ stageId: string }> }) {
  const { stageId } = await params;
  return <CurriculumTest key={stageId} stageId={stageId}/>;
}
