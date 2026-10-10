"use client";

import type { Ref } from "react";

import { UiText } from "@/components/ui/UiText";
import { exerciseCopy } from "@/lib/copy/exercise";
import type { IntroWord } from "@/lib/client/exercises";

import { Dutch, Meaning } from "./ContentText";

/** The session's new words, shown once before they are practised; nothing to answer. */
export function IntroCard({
  words,
  headingRef,
}: {
  words: IntroWord[];
  headingRef?: Ref<HTMLHeadingElement>;
}) {
  return (
    <div className="exercise-item">
      <h2 className="exercise-question" tabIndex={-1} ref={headingRef}>
        <UiText text={exerciseCopy.introTitle} />
      </h2>
      <p className="exercise-lead">
        <UiText text={exerciseCopy.introLead} tier="guide" />
      </p>
      <ul className="intro-words">
        {words.map((word) => (
          <li key={word.term} className="intro-word">
            <Dutch text={word.term} className="intro-term" /> <Meaning text={word.meaning} />{" "}
            <span className="intro-example">
              <Dutch text={word.example.nl} /> <Meaning text={word.example} />
            </span>
          </li>
        ))}
      </ul>
    </div>
  );
}
