"use client";

import { Fragment } from "react";

import { UiText } from "@/components/ui/UiText";
import { exerciseCopy } from "@/lib/copy/exercise";
import type { DiffOp } from "@/lib/client/exercises";

import { diffParts } from "./tokenParts";

/**
 * A typed answer next to the one it was compared with, word by word: a missing word is shown inserted, a word
 * too many struck through, a word typed otherwise struck through with the right one after it. Each change also
 * says what it is in words (for screen readers and without colour), never as a score.
 */
export function TokenDiff({ ops }: { ops: readonly DiffOp[] }) {
  const parts = diffParts(ops);
  return (
    <p className="token-diff" lang="nl">
      {parts.map((part, index) => (
        <Fragment key={index}>
          {index > 0 && " "}
          {part.kind === "same" && <span className="token-same">{part.text}</span>}
          {part.kind === "missing" && (
            <ins className="token-missing">
              <span className="visually-hidden">
                <UiText text={exerciseCopy.diffMissing} inline />{" "}
              </span>
              {part.expected}
            </ins>
          )}
          {part.kind === "extra" && (
            <del className="token-extra">
              <span className="visually-hidden">
                <UiText text={exerciseCopy.diffExtra} inline />{" "}
              </span>
              {part.given}
            </del>
          )}
          {part.kind === "changed" && (
            <span className="token-changed">
              <del>
                <span className="visually-hidden">
                  <UiText text={exerciseCopy.diffTyped} inline />{" "}
                </span>
                {part.given}
              </del>{" "}
              <ins>
                <span className="visually-hidden">
                  <UiText text={exerciseCopy.diffRight} inline />{" "}
                </span>
                {part.expected}
              </ins>
            </span>
          )}
        </Fragment>
      ))}
    </p>
  );
}
