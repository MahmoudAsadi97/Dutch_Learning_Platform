import type { Metadata } from "next";
import { EpisodeReader } from "@/components/EpisodeReader";
export const metadata: Metadata = { title: "Aflevering" };
export default async function EpisodePage({ params }: { params: Promise<{ episodeId: string }> }) {
  const { episodeId } = await params;
  return <EpisodeReader key={episodeId} episodeId={episodeId} />;
}
