"use client";

import { useLanguageSupport } from "@/components/LanguageSupport";
import type { Text } from "@/lib/client/exercises";

/**
 * Practice content from the API, which is not catalogue copy: Dutch in its own `lang` span, and meanings in
 * the learner's selected support language. Dutch-only practice does not expose translations.
 */
export function Dutch({
  text,
  className = "",
  id,
}: {
  text?: string | null;
  className?: string;
  id?: string;
}) {
  if (!text) return null;
  return (
    <span lang="nl" className={className || undefined} id={id}>
      {text}
    </span>
  );
}

/** Meanings follow the same language preference as the rest of the workspace. */
export function Meaning({ text, className = "" }: { text?: Text | null; className?: string }) {
  const { showEnglish, showPersian } = useLanguageSupport();
  if (!text) return null;
  const english = showEnglish && text.en ? text.en : null;
  const persian = showPersian && text.fa ? text.fa : null;
  if (!english && !persian) return null;
  return (
    <span className={`exercise-meaning ${className}`.trim()}>
      {english && <span lang="en">{english}</span>}
      {english && persian && " "}
      {persian && (
        <span lang="fa" dir="rtl">
          {persian}
        </span>
      )}
    </span>
  );
}
