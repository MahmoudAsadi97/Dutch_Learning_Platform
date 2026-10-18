import type { Metadata } from "next";
import { StudyLevelDirectory } from "@/components/StudyLevelDirectory";
export const metadata: Metadata = { title: "Mijn leerpad" };
export default function LearningPathPage() {
  return <StudyLevelDirectory />;
}
