"use client";

import { ButtonLink } from "@/components/ui/Button";
import { UiText } from "@/components/ui/UiText";
import { exerciseCopy } from "@/lib/copy/exercise";

/** The way into a short, tap-only practice session while an episode is written (Today's pending card). */
export function WaitPracticeCard() {
  return (
    <div className="wait-practice">
      <p className="wait-practice-lead">
        <UiText text={exerciseCopy.waitLead} tier="guide" />
      </p>
      <ButtonLink href="/oefenen?bron=wachten" variant="secondary" icon="zap">
        <UiText text={exerciseCopy.waitTitle} inline />
      </ButtonLink>
    </div>
  );
}
