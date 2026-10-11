"use client";

import { useLanguageSupport } from "@/components/LanguageSupport";
import type { Text } from "@/lib/client/exercises";

/**
 * Practice content from the API, which is not catalogue copy: Dutch in its own `lang` span, and meanings in
 * the learner's support languages. API texts may lack a language; a meaning always shows in at least one.
 */
export function Dutch({ text, className = "" }: { text?: string | null; className?: string }) {
  if (!text) return null;
  return (
    <span lang="nl" className={className || undefined}>
      {text}
    </span>
  );
}

/** A meaning or translation in the support languages (English, Persian or both, as the learner chose). */
export function Meaning({ text, className = "" }: { text?: Text | null; className?: string }) {
  const { showEnglish, showPersian } = useLanguageSupport();
  if (!text) return null;
  let english = showEnglish && text.en ? text.en : null;
  const persian = showPersian && text.fa ? text.fa : null;
  // a learner who reads only Persian still sees a meaning when the Persian is missing
  if (!english && !persian) english = text.en || null;
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

/** A meaning as plain text in the learner's first support language, for an accessible name. */
export function useMeaningText(): (text?: Text | null) => string {
  const { showEnglish, showPersian } = useLanguageSupport();
  return (text) =>
    (text && ((showEnglish && text.en) || (showPersian && text.fa) || text.en || text.fa)) || "";
}
