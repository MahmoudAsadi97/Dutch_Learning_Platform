"use client";

import { useId, useState } from "react";

import { Icon } from "@/components/Icon";
import { UiText } from "@/components/ui/UiText";
import { exerciseCopy } from "@/lib/copy/exercise";

import type { BoardProps } from "./boardProps";
import { Dutch, Meaning } from "./ContentText";
import { ItemHeading } from "./heading";

/**
 * Match pairs: Dutch words on one side, meanings on the other. Choose a word, then its meaning; a pair shows
 * the same number on both sides, and choosing either side again changes it. Every control is a button whose
 * name says what it is paired with, so it works by keyboard and screen reader as well as by touch. Answered,
 * each word shows whether its pair was right and, when it was not (or the board was skipped), its meaning.
 */
export function MatchPairsItem({ prompt, feedback, onDraft, headingRef }: BoardProps<"match_pairs">) {
  const headingId = useId();
  const [pairs, setPairs] = useState<Record<string, string>>({});
  const [active, setActive] = useState<string | null>(null);
  const answered = feedback !== null;
  const given = feedback?.pairs ?? null;
  const shown: Record<string, string> = given
    ? Object.fromEntries(Object.entries(given).map(([left, result]) => [left, result.given]))
    : pairs;
  const number = (left: string) => prompt.left.findIndex((entry) => entry.id === left) + 1;
  const leftOf = (right: string) => Object.keys(shown).find((left) => shown[left] === right) ?? null;
  const meaningOf = (right: string | undefined) => prompt.right.find((entry) => entry.id === right);

  function update(next: Record<string, string>) {
    // always in the board's order, so the same pairs are the same answer (and a resend keeps its request id)
    const ordered = Object.fromEntries(
      prompt.left.filter((entry) => entry.id in next).map((entry) => [entry.id, next[entry.id]]),
    );
    setPairs(ordered);
    onDraft(Object.keys(ordered).length === prompt.left.length ? { pairs: ordered } : null);
  }

  function chooseLeft(left: string) {
    setActive((current) => (current === left ? null : left));
  }

  function chooseRight(right: string) {
    const owner = leftOf(right);
    if (!active) {
      // a meaning chosen on its own undoes its pair
      if (owner) {
        const next = { ...pairs };
        delete next[owner];
        update(next);
      }
      return;
    }
    const next = Object.fromEntries(Object.entries(pairs).filter(([, value]) => value !== right));
    next[active] = right;
    setActive(null);
    update(next);
  }

  return (
    <div className="exercise-item">
      <ItemHeading className="exercise-question" id={headingId} tabIndex={-1} ref={headingRef}>
        <UiText text={exerciseCopy.askPairs} tier="guide" />
      </ItemHeading>
      {!answered && (
        <p className="exercise-lead">
          <UiText text={exerciseCopy.pairsHint} tier="guide" />
        </p>
      )}
      <div className="pairs-board" role="group" aria-labelledby={headingId}>
        <ul className="pairs-column" aria-label={exerciseCopy.words.nl}>
          {prompt.left.map((entry) => {
            const result = given?.[entry.id];
            const meaning = meaningOf(shown[entry.id]);
            return (
              <li key={entry.id}>
                <button
                  type="button"
                  className="pair-tile"
                  data-state={
                    result ? (result.ok ? "correct" : "incorrect") : active === entry.id ? "active" : "idle"
                  }
                  aria-pressed={answered ? undefined : active === entry.id}
                  disabled={answered}
                  onClick={() => chooseLeft(entry.id)}
                >
                  <span className="pair-mark" aria-hidden="true">
                    {shown[entry.id] ? number(entry.id) : ""}
                  </span>
                  <Dutch text={entry.nl} className="pair-text" />
                  {meaning && (
                    <span className="visually-hidden">
                      {", "}
                      <span lang="nl">{exerciseCopy.goesWith.nl}</span> <Meaning text={meaning} />
                    </span>
                  )}
                  {result && <Icon name={result.ok ? "check" : "close"} size={16} />}
                </button>
                {answered && (!result || !result.ok) && (
                  <span className="pair-correction">
                    <UiText text={exerciseCopy.rightAnswer} inline />
                    {": "}
                    {/* a skipped board has no results: the word's own meaning shows what it goes with */}
                    <Meaning
                      text={result ? meaningOf(result.correct) : feedback?.cards?.[entry.id]?.meaning}
                    />
                  </span>
                )}
              </li>
            );
          })}
        </ul>
        <ul className="pairs-column" aria-label={exerciseCopy.meanings.nl}>
          {prompt.right.map((entry) => {
            const owner = leftOf(entry.id);
            const ownerText = prompt.left.find((left) => left.id === owner)?.nl;
            return (
              <li key={entry.id}>
                <button
                  type="button"
                  className="pair-tile"
                  data-state={owner ? "paired" : "idle"}
                  disabled={answered}
                  onClick={() => chooseRight(entry.id)}
                >
                  <span className="pair-mark" aria-hidden="true">
                    {owner ? number(owner) : ""}
                  </span>
                  <Meaning text={entry} className="pair-text" />
                  {ownerText && (
                    <span className="visually-hidden">
                      {", "}
                      <span lang="nl">{exerciseCopy.goesWith.nl}</span> <Dutch text={ownerText} />
                    </span>
                  )}
                </button>
              </li>
            );
          })}
        </ul>
      </div>
    </div>
  );
}
