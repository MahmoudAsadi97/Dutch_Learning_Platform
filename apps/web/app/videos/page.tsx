import type { Metadata } from "next";
import { VideoLibrary } from "@/components/VideoLibrary";
import { MediaTabs } from "@/components/shell/SectionTabs";
export const metadata: Metadata = { title: "Video's" };
/** The tabs sit outside the library so they show while it loads and when it fails. */
export default function VideosPage() {
  return (
    <>
      <MediaTabs />
      <VideoLibrary />
    </>
  );
}
