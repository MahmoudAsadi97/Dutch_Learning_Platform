"use client";

import { useId, type Ref } from "react";

import { Icon, type IconName } from "@/components/Icon";
import { Button } from "@/components/ui/Button";
import { UiText } from "@/components/ui/UiText";
import { exerciseCopy } from "@/lib/copy/exercise";
import type { AnswerResult, Outcome } from "@/lib/client/exercises";
import { uiCopy, type Copy } from "@/lib/ui-copy";

import { Dutch, Meaning } from "./ContentText";

const OUTCOMES: Partial<Record<Outcome, { text: Copy; icon: IconName }>> = {
  correct: { text: uiCopy.state.correct, icon: "check" },
  almost: { text: uiCopy.state.almost, icon: "info" },
  incorrect: { text: exerciseCopy.incorrect, icon: "repeat" },
  accepted: { text: exerciseCopy.accepted, icon: "check" },
  heard: { text: exerciseCopy.heard, icon: "ear" },
  not_heard: { text: uiCopy.state.notHeard, icon: "ear" },
  skipped: { text: exerciseCopy.skipped, icon: "repeat" },
};

/** The outcome's headline, also announced in the session's live region. */
export function outcomeCopy(outcome: Outcome): Copy | null {
  return OUTCOMES[outcome]?.text ?? null;
}

interface Props {
  result: AnswerResult;
  onContinue: () => void;
  onReport: () => void;
  /** "Mijn antwoord klopt ook", offered on a typed answer or a built sentence the check did not accept. */
  onOverride?: () => void;
  continueRef?: Ref<HTMLButtonElement>;
  /** The item's own verdict details (a word comparison, what was heard), read out with "Verder". */
  describedBy?: string;
}

/**
 * What an answer reveals: the outcome in words and an icon (a miss is "Nog niet", never red here), the point
 * it earned, whether the item comes back, and the word it was about with its meaning and example (for a cloze,
 * the whole sentence).
 */
export function FeedbackBar({ result, onContinue, onReport, onOverride, continueRef, describedBy }: Props) {
  const titleId = useId();
  const correctionId = useId();
  const { feedback } = result;
  const outcome = OUTCOMES[result.outcome];
  const word = feedback.word;
  const missed = result.outcome !== "correct" && result.outcome !== "almost";
  // the right option, for an item without a word card (an authored question)
  const right =
    missed && !word ? feedback.support?.find((entry) => entry.id === feedback.correct) : undefined;
  // "Verder" takes focus after the verdict, so it also reads out what the answer revealed (an id that is not
  // on the page is ignored)
  const correction = right || feedback.explanation || feedback.odd_topic || word ? correctionId : undefined;
  const described = [describedBy, correction].filter(Boolean).join(" ") || undefined;
  return (
    <section className="feedback-bar" data-outcome={result.outcome} aria-labelledby={titleId}>
      <p className="feedback-title" id={titleId}>
        {outcome && <Icon name={outcome.icon} size={20} />}
        {outcome && <UiText text={outcome.text} />}
        {result.points > 0 && (
          <span className="feedback-points">
            <UiText text={exerciseCopy.pointEarned} inline />
          </span>
        )}
      </p>
      {result.requeue && (
        <p className="feedback-line">
          <UiText text={exerciseCopy.comesBack} tier="guide" />
        </p>
      )}
      {!result.closed && !result.requeue && (
        <p className="feedback-line">
          <UiText text={exerciseCopy.tryOnceMore} tier="guide" />
        </p>
      )}
      <div className="feedback-correction" id={correctionId}>
        {right && (
          <p className="feedback-line">
            <UiText text={exerciseCopy.rightAnswer} inline />
            {": "}
            <Dutch text={right.nl} /> <Meaning text={right} />
          </p>
        )}
        {feedback.odd_topic && (
          <p className="feedback-line">
            <UiText text={exerciseCopy.oddBelongs} inline /> <Dutch text={feedback.odd_topic.nl} />{" "}
            <Meaning text={feedback.odd_topic} />
          </p>
        )}
        {feedback.explanation && (
          <p className="feedback-line">
            <Dutch text={feedback.explanation.nl} /> <Meaning text={feedback.explanation} />
          </p>
        )}
        {word && (
          <div className="feedback-word">
            <Dutch text={word.term} className="feedback-term" /> <Meaning text={word.meaning} />{" "}
            <span className="feedback-example">
              <Dutch text={word.example.nl} /> <Meaning text={word.example} />
            </span>
          </div>
        )}
      </div>
      <div className="feedback-actions">
        <Button ref={continueRef} onClick={onContinue} icon="arrow" iconEnd aria-describedby={described}>
          <UiText text={exerciseCopy.continue} inline />
        </Button>
        {onOverride && (
          <Button variant="secondary" size="small" icon="check" onClick={onOverride}>
            <UiText text={exerciseCopy.override} inline />
          </Button>
        )}
        <Button variant="ghost" size="small" icon="flag" onClick={onReport}>
          <UiText text={exerciseCopy.report} inline />
        </Button>
      </div>
    </section>
  );
}
