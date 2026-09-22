import type { Metadata } from "next";
import { ProgressOverview } from "@/components/ProgressOverview";
export const metadata: Metadata = { title: "Mijn voortgang" };
export default function ProgressPage() {
  return <ProgressOverview />;
}
