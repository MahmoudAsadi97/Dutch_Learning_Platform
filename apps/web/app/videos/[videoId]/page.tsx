import type { Metadata } from "next";
import { VideoPlayer } from "@/components/VideoPlayer";
export const metadata: Metadata = { title: "Video" };
export default async function VideoPage({ params }: { params: Promise<{ videoId: string }> }) {
  const { videoId } = await params;
  return <VideoPlayer key={videoId} videoId={videoId} />;
}
