"use client";

import { useId, useState } from "react";

import { Icon } from "@/components/Icon";
import { UiText } from "@/components/ui/UiText";
import { exerciseCopy } from "@/lib/copy/exercise";

import type { BoardProps } from "./boardProps";
import { Dutch } from "./ContentText";

type Bin = "de" | "het";

/**
 * De or het: each noun (without its article) gets a pair of radio buttons, drawn as a two-part switch. Native
 * radios, so arrow keys and screen readers work as everywhere. Answered, each noun shows its article.
 */
export function SortBinsItem({ prompt, feedback, onDraft, headingRef }: BoardProps<"de_het">) {
  const headingId = useId();
  const group = useId();
  const [bins, setBins] = useState<Record<string, Bin>>({});
  const results = feedback?.bins ?? null;

  function choose(noun: string, bin: Bin) {
    const next = { ...bins, [noun]: bin };
    setBins(next);
    onDraft(Object.keys(next).length === prompt.options.length ? { bins: next } : null);
  }

  return (
    <div className="exercise-item">
      <h2 className="exercise-question" id={headingId} tabIndex={-1} ref={headingRef}>
        <UiText text={exerciseCopy.askDeHet} tier="guide" />
      </h2>
      <ul className="sort-list" aria-labelledby={headingId}>
        {prompt.options.map((noun) => {
          const result = results?.[noun.id];
          const chosen = result ? result.given : bins[noun.id];
          return (
            <li
              key={noun.id}
              className="sort-row"
              data-state={result ? (result.ok ? "correct" : "incorrect") : "open"}
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
                        disabled={results !== null}
                        onChange={() => choose(noun.id, bin)}
                      />
                      <span lang="nl">{bin}</span>
                    </label>
                  ))}
                </div>
              </fieldset>
              {result && (
                <span className="sort-result">
                  <Icon name={result.ok ? "check" : "close"} size={16} />
                  {!result.ok && (
                    <>
                      <UiText text={exerciseCopy.rightAnswer} inline />
                      {": "}
                    </>
                  )}
                  <Dutch text={feedback?.cards?.[noun.id]?.term ?? `${result.correct} ${noun.nl}`} />
                </span>
              )}
            </li>
          );
        })}
      </ul>
    </div>
  );
}
