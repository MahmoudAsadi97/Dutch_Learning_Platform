"use client";

import { useLanguageSupport } from "@/components/LanguageSupport";
import { glossShown, type GlossTier } from "@/lib/client/gloss";
import { persianReviewed } from "@/lib/client/persian-review";
import type { Copy } from "@/lib/ui-copy";
import { Fragment } from "react";

interface Props {
  text: Copy;
  /** `chrome` (labels, one gloss line), `guide` (instructions, every selected language), `always`. */
  tier?: GlossTier;
  className?: string;
  /** Render the gloss on the same line instead of under the Dutch. */
  inline?: boolean;
}

/**
 * Dutch first, always; a short translation under it when the learner's level or preference asks for one.
 * Chrome shows one gloss line (Persian when selected, else English); guides show each selected language.
 * Persian appears only for batches a fluent reader has checked (lib/copy/review.ts, owner decision O2);
 * until then a learner who also chose English sees English.
 */
export function UiText({ text, tier = "chrome", className = "", inline = false }: Props) {
  const { glossLevel, showEnglish, showPersian } = useLanguageSupport();
  const shown = glossShown(tier, glossLevel);
  const persian = showPersian && persianReviewed(text);
  const languages: ("en" | "fa")[] = [];
  if (shown) {
    if (tier === "chrome") {
      if (persian) languages.push("fa");
      else if (showEnglish) languages.push("en");
    } else {
      if (showEnglish) languages.push("en");
      if (persian) languages.push("fa");
    }
  }
  return (
    <span className={`ui-text ${inline ? "is-inline" : ""} ${className}`.trim()}>
      <span lang="nl" className="ui-text-nl">
        {text.nl}
      </span>
      {languages.map((language) => (
        <Fragment key={language}>
          {/* a real space, so an accessible name reads "Volgende stap Next step", not one run-on word */}{" "}
          <span
            lang={language}
            dir={language === "fa" ? "rtl" : undefined}
            className={`ui-gloss ${language === "fa" ? "fa" : ""}`.trim()}
          >
            {text[language]}
          </span>
        </Fragment>
      ))}
    </span>
  );
}
