"use client";

import { StoryLibrary } from "@/components/StoryLibrary";
import { WordReview } from "@/components/WordReview";

/** Saved work remains available inside learning rather than competing with the four skills. */
export function StudyPersonalLibrary({ kind }: { kind: "words" | "stories" }) {
  return (
    <section className="study-personal-library" data-testid={`study-personal-${kind}`}>
      {kind === "words" ? <WordReview embedded /> : <StoryLibrary embedded />}
    </section>
  );
}
