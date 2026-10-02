import type { Metadata } from "next";
import { TodayHome } from "@/components/TodayHome";
export const metadata: Metadata = { title: "Vandaag" };
export default function HomePage() {
  return <TodayHome />;
}
