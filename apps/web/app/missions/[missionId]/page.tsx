import { LessonShell } from "@/components/LessonShell";

export default async function MissionPage({ params }: { params: Promise<{ missionId: string }> }) {
  const { missionId } = await params;
  return <LessonShell missionId={missionId} />;
}
