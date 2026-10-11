"use client";

import { useId, useState } from "react";

import { Icon } from "@/components/Icon";
import { UiText } from "@/components/ui/UiText";
import { exerciseCopy } from "@/lib/copy/exercise";

import type { BoardProps } from "./boardProps";
import { Dutch } from "./ContentText";
import { ItemHeading } from "./heading";

type Bin = "de" | "het";

/**
 * De or het: each noun (without its article) gets a pair of radio buttons, drawn as a two-part switch. Native
 * radios, so arrow keys and screen readers work as everywhere. Answered (or skipped), the board is read-only and
 * each noun shows its article.
 */
export function SortBinsItem({ prompt, feedback, onDraft, headingRef }: BoardProps<"de_het">) {
  const headingId = useId();
  const group = useId();
  const [bins, setBins] = useState<Record<string, Bin>>({});
  const answered = feedback !== null;
  const results = feedback?.bins ?? null;

  function choose(noun: string, bin: Bin) {
    // in the board's order, so the same choices are the same answer (and a resend keeps its request id)
    const chosen: Record<string, Bin> = { ...bins, [noun]: bin };
    const next = Object.fromEntries(
      prompt.options.filter((option) => option.id in chosen).map((option) => [option.id, chosen[option.id]]),
    ) as Record<string, Bin>;
    setBins(next);
    onDraft(Object.keys(next).length === prompt.options.length ? { bins: next } : null);
  }

  return (
    <div className="exercise-item">
      <ItemHeading className="exercise-question" id={headingId} tabIndex={-1} ref={headingRef}>
        <UiText text={exerciseCopy.askDeHet} tier="guide" />
      </ItemHeading>
      <ul className="sort-list" aria-labelledby={headingId}>
        {prompt.options.map((noun) => {
          const result = results?.[noun.id];
          const chosen = result ? result.given : bins[noun.id];
          return (
            <li
              key={noun.id}
              className="sort-row"
              data-state={result ? (result.ok ? "correct" : "incorrect") : answered ? "shown" : "open"}
            >
              <fieldset className="sort-choice">
                <legend className="sort-noun">
                  <Dutch text={noun.nl} />
                </legend>
                <div className="sort-switch">
                  {prompt.bins.map((bin) => (
                    <label key={bin} className="sort-option">
                      <input
                        type="radio"
                        name={`${group}-${noun.id}`}
                        value={bin}
                        checked={chosen === bin}
                        disabled={answered}
                        onChange={() => choose(noun.id, bin)}
                      />
                      <span lang="nl">{bin}</span>
                    </label>
                  ))}
                </div>
              </fieldset>
              {answered && (
                <span className="sort-result">
                  {result && <Icon name={result.ok ? "check" : "close"} size={16} />}
                  {!result?.ok && (
                    <>
                      <UiText text={exerciseCopy.rightAnswer} inline />
                      {": "}
                    </>
                  )}
                  <Dutch
                    text={
                      feedback.cards?.[noun.id]?.term ?? (result ? `${result.correct} ${noun.nl}` : noun.nl)
                    }
                  />
                </span>
              )}
            </li>
          );
        })}
      </ul>
    </div>
  );
}
