"use client";

import { useEffect, useId, useRef, useState } from "react";

import { Icon } from "@/components/Icon";
import { UiText } from "@/components/ui/UiText";
import { exerciseCopy } from "@/lib/copy/exercise";
import { fill } from "@/lib/ui-copy";

import type { BoardProps } from "./boardProps";
import { Dutch, Meaning } from "./ContentText";

/**
 * The sentence builder: word tiles (or chunks of a long sentence) to put in order. Choosing a tile adds it to
 * the sentence; choosing a tile in the sentence puts it back. No dragging, so it works the same by touch,
 * keyboard and screen reader. Answered, it shows the sentence as built, where it first went another way (with
 * an icon and words, not colour alone), and the right sentence; skipped, the right sentence only.
 */
export function TilesItem({ prompt, feedback, onDraft, headingRef }: BoardProps<"sentence_builder">) {
  const headingId = useId();
  const [placed, setPlaced] = useState<string[]>([]);
  const textOf = new Map(prompt.tiles.map((tile) => [tile.id, tile.nl ?? ""]));
  const answered = feedback !== null;
  const built = answered ? (feedback.given_order ?? []) : placed;
  const loose = prompt.tiles.filter((tile) => !built.includes(tile.id));
  const first = feedback?.first_difference ?? null;
  const skipped = answered && !feedback.given_order;

  // a chosen tile leaves its row: focus goes to the tile now in its place (or the other row when it emptied)
  const line = useRef<HTMLDivElement>(null);
  const pool = useRef<HTMLDivElement>(null);
  const focusNext = useRef<{ row: "line" | "pool"; index: number } | null>(null);
  useEffect(() => {
    const wanted = focusNext.current;
    if (!wanted) return;
    focusNext.current = null;
    const pick = (row: HTMLDivElement | null, index: number) => {
      const buttons = Array.from(row?.querySelectorAll<HTMLButtonElement>("button") ?? []);
      return buttons[Math.min(index, buttons.length - 1)];
    };
    const [here, there] = wanted.row === "pool" ? [pool.current, line.current] : [line.current, pool.current];
    (pick(here, wanted.index) ?? pick(there, Number.MAX_SAFE_INTEGER))?.focus();
  }, [placed]);

  function update(next: string[], row: "line" | "pool", index: number) {
    focusNext.current = { row, index };
    setPlaced(next);
    onDraft(next.length === prompt.tiles.length ? { order: next } : null);
  }

  return (
    <div className="exercise-item">
      <h2 className="exercise-question" id={headingId} tabIndex={-1} ref={headingRef}>
        <UiText text={exerciseCopy.askBuild} tier="guide" />
      </h2>
      <Meaning text={prompt.cue} className="exercise-cue" />
      {!answered && (
        <p className="exercise-lead">
          <UiText text={exerciseCopy.buildHint} tier="guide" />
        </p>
      )}
      {!skipped && (
        <div className="tiles-line" role="group" aria-label={exerciseCopy.yourSentence.nl} ref={line}>
          {built.map((id, index) => {
            const off = answered && first !== null && index >= first;
            return (
              <button
                key={id}
                type="button"
                className="tile"
                data-state={answered ? (off ? "incorrect" : "correct") : "placed"}
                disabled={answered}
                aria-label={
                  answered ? undefined : fill(exerciseCopy.removePiece, { piece: textOf.get(id) ?? "" }).nl
                }
                onClick={() =>
                  update(
                    placed.filter((entry) => entry !== id),
                    "line",
                    index,
                  )
                }
              >
                {answered && index === first && (
                  <span className="visually-hidden">
                    <UiText text={exerciseCopy.tilesDiffer} inline />{" "}
                  </span>
                )}
                {answered && <Icon name={off ? "close" : "check"} size={14} />}
                <Dutch text={textOf.get(id)} />
              </button>
            );
          })}
          <span className="tiles-end" lang="nl" aria-hidden="true">
            {prompt.end}
          </span>
        </div>
      )}
      {!answered && (
        <div className="tiles-pool" role="group" aria-label={exerciseCopy.pieces.nl} ref={pool}>
          {loose.map((tile, index) => (
            <button
              key={tile.id}
              type="button"
              className="tile"
              onClick={() => update([...placed, tile.id], "pool", index)}
            >
              <Dutch text={tile.nl} />
            </button>
          ))}
        </div>
      )}
      {answered && (first !== null || skipped) && (
        <p className="tiles-right">
          <UiText text={exerciseCopy.rightSentence} inline />
          {": "}
          <Dutch text={feedback.sentence ?? `${(feedback.texts ?? []).join(" ")}${prompt.end}`} />
        </p>
      )}
    </div>
  );
}
