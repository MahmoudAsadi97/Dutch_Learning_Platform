import type { Metadata } from "next";
import { CurriculumProgress } from "@/components/CurriculumProgress";
import { ProgressOverview } from "@/components/ProgressOverview";
export const metadata: Metadata = { title: "Mijn voortgang" };
export default function ProgressPage() {
  return <><CurriculumProgress /><details className="card" style={{ marginTop: "2rem" }}><summary>Voortgang in praktijkgesprekken</summary><ProgressOverview nested /></details></>;
}
