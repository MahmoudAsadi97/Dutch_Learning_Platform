"use client";

import { useRef, useState } from "react";

import { useLanguageSupport } from "@/components/LanguageSupport";
import { UiText } from "@/components/ui/UiText";
import { missionsCopy } from "@/lib/copy/missions";
import type { HelpRung } from "@/lib/types";
import { fill, type Copy } from "@/lib/ui-copy";

interface Props {
  rungs: HelpRung[];
  idPrefix: string;
  disabled?: boolean;
  /** Called when a rung is opened; the parent records it as help-usage evidence. */
  onReveal: (rung: HelpRung) => Promise<void>;
}

const KIND_LABEL: Record<HelpRung["kind"], Copy> = {
  hint_nl: missionsCopy.rungHint,
  gloss_fa: missionsCopy.rungKeywords,
  translation_fa: missionsCopy.rungTranslation,
};

/**
 * Persian text-help ladder: the learner reveals one rung at a time, lightest help first.
 * Every rung opened is reported to the parent, which records it as help-usage evidence.
 */
export function HelpLadder({ rungs, idPrefix, disabled = false, onReveal }: Props) {
  const { showEnglish, showPersian } = useLanguageSupport();
  const [revealed, setRevealed] = useState(0);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<Copy | null>(null);
  const pending = useRef(false);
  const ordered = [...rungs].sort((a, b) => a.level - b.level);
  const next = ordered[revealed];

  async function reveal() {
    if (!next || pending.current) return;
    pending.current = true;
    setBusy(true);
    setError(null);
    try {
      await onReveal(next);
      setRevealed((value) => value + 1);
    } catch {
      setError(missionsCopy.helpSaveFailed);
    } finally {
      pending.current = false;
      setBusy(false);
    }
  }

  if (disabled) {
    return (
      <p className="muted" data-help="disabled">
        <UiText text={missionsCopy.helpDisabled} tier="guide" />
      </p>
    );
  }

  return (
    <div className="help-ladder" data-help-revealed={revealed}>
      <ol aria-label={missionsCopy.help.nl}>
        {ordered.slice(0, revealed).map((rung) => (
          <li key={`${idPrefix}-${rung.level}`}>
            <div className="muted" style={{ fontSize: "0.8rem" }}>
              <UiText text={KIND_LABEL[rung.kind]} />
            </div>
            {/* Glosses mix "Dutch = Persian" pairs: dir=auto keeps the pair order readable while each Persian run stays RTL. */}
            {(rung.direction === "ltr" || showPersian) && (
              <div
                className={`rung ${rung.direction === "rtl" ? "fa" : "nl"}`}
                lang={rung.direction === "rtl" ? "fa" : "nl"}
                dir={rung.kind === "gloss_fa" ? "auto" : rung.direction}
                style={rung.kind === "gloss_fa" ? { textAlign: "start" } : undefined}
              >
                {rung.text}
              </div>
            )}
            {showEnglish && rung.en && (
              <div className="rung" lang="en">
                {rung.en}
              </div>
            )}
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
          <UiText text={fill(missionsCopy.helpLevel, { level: next.level })} inline />
        </button>
      ) : (
        <p className="muted">
          <UiText text={missionsCopy.helpAllShown} tier="guide" />
        </p>
      )}
      {error && (
        <p className="error" role="alert">
          <UiText text={error} tier="guide" />
        </p>
      )}
    </div>
  );
}
