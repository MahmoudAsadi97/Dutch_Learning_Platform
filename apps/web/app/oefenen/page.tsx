import type { Metadata } from "next";

import { ExerciseSession } from "@/components/exercise/ExerciseSession";
import { exerciseCopy } from "@/lib/copy/exercise";

export const metadata: Metadata = { title: exerciseCopy.pageTitle.nl };

/**
 * A practice session in focus mode (no sidebar or tabs). `?bron=wachten` is the short, tap-only session
 * offered on Today while an episode is being written.
 */
export default async function PracticePage({ searchParams }: { searchParams: Promise<{ bron?: string }> }) {
  const { bron } = await searchParams;
  const source = bron === "wachten" ? "while_you_wait" : "stage_skill";
  return <ExerciseSession key={source} source={source} />;
}
