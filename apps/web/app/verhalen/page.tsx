import type { Metadata } from "next";
import { StoryLibrary } from "@/components/StoryLibrary";
import { MediaTabs } from "@/components/shell/SectionTabs";
export const metadata: Metadata = { title: "Verhalen" };
/** The tabs sit outside the library so they show while it loads and when it fails. */
export default function StoriesPage() {
  return (
    <>
      <MediaTabs />
      <StoryLibrary />
    </>
  );
}
