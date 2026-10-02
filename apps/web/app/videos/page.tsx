import type { Metadata } from "next";
import { VideoLibrary } from "@/components/VideoLibrary";
export const metadata: Metadata = { title: "Video's" };
export default function VideosPage() {
  return <VideoLibrary />;
}
