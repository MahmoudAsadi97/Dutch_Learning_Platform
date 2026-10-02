import type { Metadata } from "next";
import { LearningOverview } from "@/components/LearningOverview";
export const metadata: Metadata = { title: "Mijn leerpad" };
export default function LearningPathPage() {
  return <LearningOverview />;
}
