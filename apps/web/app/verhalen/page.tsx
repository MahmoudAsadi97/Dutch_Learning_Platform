import type { Metadata } from "next";
import { StoryLibrary } from "@/components/StoryLibrary";
export const metadata: Metadata = { title: "Verhalen" };
export default function StoriesPage() {
  return <StoryLibrary />;
}
