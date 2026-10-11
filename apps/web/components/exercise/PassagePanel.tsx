"use client";

import { useId, useState, type Ref } from "react";

import { CurriculumAudio } from "@/components/CurriculumControls";
import type { LearningCopy } from "@/components/LanguageSupport";
import { PhraseAudio } from "@/components/PhraseAudio";
import { SpokenPassage } from "@/components/SpokenPassage";
import { Button } from "@/components/ui/Button";
import { UiText } from "@/components/ui/UiText";
import { exerciseCopy } from "@/lib/copy/exercise";
import type { Text } from "@/lib/client/exercises";

import { Dutch, Meaning } from "./ContentText";
import { ItemHeading } from "./heading";
import { passageRevealed, type PassagePrompt } from "./registry";

function learning(text: Text): LearningCopy {
  return { nl: text.nl ?? "", en: text.en ?? undefined, fa: text.fa ?? undefined };
}

/**
 * The passage itself: the text sentence by sentence (each one to hear), or the listening player over the topic's
 * or lesson's own route, part by part; then the topic's words. `revealed` adds the translation or transcript.
 */
function PassageBody({
  prompt,
  audioPath,
  revealed,
}: {
  prompt: PassagePrompt;
  audioPath: string;
  revealed: boolean;
}) {
  return (
    <div className="exercise-passage-body">
      {prompt.kind === "read_passage" ? (
        <div className="exercise-passage-text">
          <SpokenPassage text={revealed ? learning(prompt.text) : { nl: prompt.text.nl ?? "" }} />
        </div>
      ) : (
        <CurriculumAudio
          endpoint={audioPath}
          parts={prompt.parts}
          transcript={revealed && prompt.transcript ? learning(prompt.transcript) : undefined}
        />
      )}
      {prompt.vocabulary.length > 0 && (
        <details className="exercise-passage-words">
          <summary>
            <UiText text={exerciseCopy.passageWords} inline />
          </summary>
          <ul>
            {prompt.vocabulary.map((word) => (
              <li key={word.term}>
                <Dutch text={word.term} className="exercise-passage-term" />
                <PhraseAudio text={word.term} /> <Meaning text={word.meaning} />
              </li>
            ))}
          </ul>
        </details>
      )}
    </div>
  );
}

interface Props {
  prompt: PassagePrompt;
  /** "step": the passage is the item on screen; "reference": it stays above each question. */
  mode: "step" | "reference";
  audioPath: string;
  headingRef?: Ref<HTMLHeadingElement>;
}

/**
 * A topic's passage in one place from its own step through every question: the heading and the lead change, the
 * text or the player below them stays the same node, so the place read or the part playing is never lost.
 */
export function PassagePanel({ prompt, mode, audioPath, headingRef }: Props) {
  const headingId = useId();
  const read = prompt.kind === "read_passage";
  const step = mode === "step";
  return (
    <section className="exercise-passage" data-mode={mode} aria-labelledby={headingId}>
      <ItemHeading
        className={step ? "exercise-question" : "exercise-passage-title"}
        id={headingId}
        tabIndex={-1}
        ref={step ? headingRef : undefined}
      >
        <UiText
          text={
            step
              ? read
                ? exerciseCopy.passageRead
                : exerciseCopy.passageListen
              : read
                ? exerciseCopy.passageText
                : exerciseCopy.passageAudio
          }
        />
      </ItemHeading>
      {step && (
        <p className="exercise-lead">
          <UiText text={read ? exerciseCopy.passageReadLead : exerciseCopy.passageListenLead} tier="guide" />
        </p>
      )}
      <PassageBody prompt={prompt} audioPath={audioPath} revealed={false} />
    </section>
  );
}

/** After the questions: the passage again, now with its translation on request or its transcript to read along. */
export function PassageReview({ prompt, audioPath }: { prompt: PassagePrompt; audioPath: string }) {
  const [translated, setTranslated] = useState(false);
  const read = prompt.kind === "read_passage";
  const revealed = passageRevealed(prompt);
  return (
    <div className="summary-block summary-passage">
      <ItemHeading sub className="summary-subtitle">
        <UiText text={read ? exerciseCopy.reviewRead : exerciseCopy.reviewListen} />
      </ItemHeading>
      {read && revealed && (
        <Button
          variant="secondary"
          size="small"
          icon="languages"
          onClick={() => setTranslated((value) => !value)}
        >
          <UiText text={translated ? exerciseCopy.translationHide : exerciseCopy.translationShow} inline />
        </Button>
      )}
      <PassageBody prompt={prompt} audioPath={audioPath} revealed={read ? translated : revealed} />
    </div>
  );
}
