"use client";

import { useEffect } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { useProfile } from "@/lib/client/profile";
import { isStageId, type Skill } from "@/lib/domain/registry";
import { studyHref } from "@/lib/client/study";
import { LearningText } from "@/components/LanguageSupport";
import { uiCopy } from "@/lib/ui-copy";

/** Keep old bookmarks usable while sending learners into the same contextual workspace. */
export function LegacyStudyRedirect({
  skill = "reading",
  vocabulary = false,
}: {
  skill?: Skill;
  vocabulary?: boolean;
}) {
  const router = useRouter();
  const search = useSearchParams();
  const profile = useProfile();
  const requested = search.get("stage") ?? search.get("stage_id") ?? search.get("level");
  const chosen = requested && isStageId(requested) ? requested : profile.data?.profile.stage_id;
  const section = search.get("section");
  const requestedView =
    search.get("view") ?? (section === "grammar" || section === "alphabet" ? section : undefined);
  const personal = requestedView === "personal";
  const view = personal
    ? vocabulary
      ? "personal-words"
      : "personal-stories"
    : vocabulary
      ? "vocabulary"
      : requestedView;
  useEffect(() => {
    if (chosen && isStageId(chosen)) router.replace(studyHref(chosen, skill, view ? { view } : {}));
  }, [router, chosen, skill, view]);
  return (
    <p role="status">
      <LearningText text={uiCopy.state.openingWorkspace} />
    </p>
  );
}
