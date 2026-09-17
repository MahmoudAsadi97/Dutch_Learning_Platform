"use client";

import { useState } from "react";

import type { HelpRung } from "@/lib/types";

interface Props {
  rungs: HelpRung[];
  idPrefix: string;
  disabled?: boolean;
}

const KIND_LABEL: Record<HelpRung["kind"], { nl: string; fa: string }> = {
  hint_nl: { nl: "Tip in het Nederlands", fa: "راهنمایی به هلندی" },
  gloss_fa: { nl: "Sleutelwoorden", fa: "واژه‌های کلیدی" },
  translation_fa: { nl: "Vertaling", fa: "ترجمه" },
};

/**
 * Persian text-help ladder: the learner reveals one rung at a time, lightest help first.
 * The number of rungs opened is reported to the parent later (M2) as help-usage evidence.
 */
export function HelpLadder({ rungs, idPrefix, disabled = false }: Props) {
  const [revealed, setRevealed] = useState(0);
  const ordered = [...rungs].sort((a, b) => a.level - b.level);
  const next = ordered[revealed];

  if (disabled) {
    return (
      <p className="muted" data-help="disabled">
        Geen hulp beschikbaar in deze stap. <span className="fa" lang="fa" style={{ display: "inline" }}>در این بخش کمکی در دسترس نیست.</span>
      </p>
    );
  }

  return (
    <div className="help-ladder" data-help-revealed={revealed}>
      <ol aria-label="Hulp">
        {ordered.slice(0, revealed).map((rung) => (
          <li key={`${idPrefix}-${rung.level}`}>
            <div className="muted" style={{ fontSize: "0.8rem" }}>
              {KIND_LABEL[rung.kind].nl} · <span className="fa" lang="fa" style={{ display: "inline" }}>{KIND_LABEL[rung.kind].fa}</span>
            </div>
            <div
              className={`rung ${rung.direction === "rtl" ? "fa" : "nl"}`}
              lang={rung.direction === "rtl" ? "fa" : "nl"}
              dir={rung.direction}
            >
              {rung.text}
            </div>
          </li>
        ))}
      </ol>
      {next ? (
        <button type="button" className="button secondary" onClick={() => setRevealed(revealed + 1)}>
          Hulp niveau {next.level} · <span className="fa" lang="fa" style={{ display: "inline" }}>کمک سطح {next.level}</span>
        </button>
      ) : (
        <p className="muted">Alle hulp is getoond.</p>
      )}
    </div>
  );
}
