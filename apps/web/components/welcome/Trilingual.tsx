"use client";

import { useLanguageSupport } from "@/components/LanguageSupport";
import type { Copy } from "@/lib/ui-copy";

/**
 * Welcome copy follows the same Dutch / optional English preference as the learning workspace.
 * The legacy prop shape is retained for callers; source translations are left intact.
 */
export function Trilingual({ text, className = "" }: { text: Copy; autonym?: string; className?: string }) {
  const { showEnglish } = useLanguageSupport();
  return (
    <span className={`trilingual ${className}`.trim()}>
      <span lang="nl" className="trilingual-nl">
        {text.nl}
      </span>
      {showEnglish && (
        <span lang="en" className="trilingual-support">
          {text.en}
        </span>
      )}
    </span>
  );
}
