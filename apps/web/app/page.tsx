import type { Metadata } from "next";
import { StudyDashboard } from "@/components/StudyDashboard";
export const metadata: Metadata = { title: "Dashboard" };
export default function HomePage() {
  return <StudyDashboard />;
}
