"use client";

import { useRef, useState } from "react";

import { LearningText, useLanguageSupport } from "@/components/LanguageSupport";
import type { HelpRung } from "@/lib/types";

interface Props {
  rungs: HelpRung[];
  idPrefix: string;
  disabled?: boolean;
  /** Called when a rung is opened; the parent records it as help-usage evidence. */
  onReveal: (rung: HelpRung) => Promise<void>;
}

const KIND_LABEL: Record<HelpRung["kind"], { nl: string; fa: string }> = {
  hint_nl: { nl: "Tip in het Nederlands", fa: "راهنمایی به هلندی" },
  gloss_fa: { nl: "Sleutelwoorden", fa: "واژه‌های کلیدی" },
  translation_fa: { nl: "Vertaling", fa: "ترجمه" },
};

/**
 * Persian text-help ladder: the learner reveals one rung at a time, lightest help first.
 * Every rung opened is reported to the parent, which records it as help-usage evidence.
 */
export function HelpLadder({ rungs, idPrefix, disabled = false, onReveal }: Props) {
  const { showEnglish, showPersian } = useLanguageSupport();
  const [revealed, setRevealed] = useState(0);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const pending = useRef(false);
  const ordered = [...rungs].sort((a, b) => a.level - b.level);
  const next = ordered[revealed];

  async function reveal() {
    if (!next || pending.current) return;
    pending.current = true;
    setBusy(true);
    setError("");
    try {
      await onReveal(next);
      setRevealed((value) => value + 1);
    } catch {
      setError("Hulp kon niet worden opgeslagen. Probeer opnieuw; de tip is nog niet getoond.");
    } finally {
      pending.current = false;
      setBusy(false);
    }
  }

  if (disabled) {
    return (
      <p className="muted" data-help="disabled">
        <LearningText text={{nl: "Geen hulp beschikbaar in deze stap.", en: "Help is not available in this independent step.", fa: "در این بخش کمکی در دسترس نیست."}} />
      </p>
    );
  }

  return (
    <div className="help-ladder" data-help-revealed={revealed}>
      <ol aria-label="Hulp">
        {ordered.slice(0, revealed).map((rung) => (
          <li key={`${idPrefix}-${rung.level}`}>
            <div className="muted" style={{ fontSize: "0.8rem" }}>
              <LearningText text={KIND_LABEL[rung.kind]} />
            </div>
            {/* Glosses mix "Dutch = Persian" pairs: dir=auto keeps the pair order readable while each Persian run stays RTL. */}
            {(rung.direction === "ltr" || showPersian) && <div
              className={`rung ${rung.direction === "rtl" ? "fa" : "nl"}`}
              lang={rung.direction === "rtl" ? "fa" : "nl"}
              dir={rung.kind === "gloss_fa" ? "auto" : rung.direction}
              style={rung.kind === "gloss_fa" ? { textAlign: "start" } : undefined}
            >
              {rung.text}
            </div>}
            {showEnglish && rung.en && <div className="rung" lang="en">{rung.en}</div>}
          </li>
        ))}
      </ol>
      {next ? (
        <button
          type="button"
          className="button secondary"
          disabled={busy}
          aria-busy={busy}
          onClick={() => void reveal()}
        >
          <LearningText text={{nl: `Hulp niveau ${next.level}`, en: `Hint ${next.level}`, fa: `کمک سطح ${next.level}`}} />
        </button>
      ) : (
        <p className="muted">Alle hulp is getoond.</p>
      )}
      {error && <p className="error" role="alert">{error}</p>}
    </div>
  );
}
