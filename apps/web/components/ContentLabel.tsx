"use client";

import { LearningText } from "@/components/LanguageSupport";
import type { ReviewStatus } from "@/lib/types";

interface Props {
  status: ReviewStatus;
  labelNl?: string;
  labelFa?: string;
}

/** Every fixed text carries its review state; unreviewed content is labelled in both languages. */
export function ContentLabel({ status, labelNl = "Niet-nagekeken inhoud", labelFa = "محتوای بازبینی‌نشده" }: Props) {
  if (status === "reviewed") {
    return (
      <span className="label ok" data-review="reviewed">
        Nagekeken
      </span>
    );
  }
  return (
    <span className="label warn" data-review={status} title={labelFa}>
      <LearningText text={{nl: labelNl, en: "Content awaiting review", fa: labelFa}} />
    </span>
  );
}
