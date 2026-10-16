"use client";

import { useId, useState, type Ref } from "react";

import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Field";
import { UiText } from "@/components/ui/UiText";
import { SentenceAudio } from "@/components/SpokenPassage";
import { exerciseCopy } from "@/lib/copy/exercise";
import type { Answer, Feedback, Hint } from "@/lib/client/exercises";
import { fill, type Copy } from "@/lib/ui-copy";

import { Dutch, Meaning } from "./ContentText";
import { ItemAudio } from "./ItemAudio";
import type { TypedPrompt } from "./registry";
import { TokenDiff } from "./TokenDiff";
import { hasDifference } from "./tokenParts";
import { ItemHeading } from "./heading";

/** What a compare note means, in words; the codes come from the API's tolerant comparison. */
const NOTES: Record<string, Copy> = {
  accents: exerciseCopy.noteAccents,
  punctuation: exerciseCopy.notePunctuation,
  article_missing: exerciseCopy.noteArticleMissing,
  article_extra: exerciseCopy.noteArticleExtra,
  article: exerciseCopy.noteArticle,
  spelling: exerciseCopy.noteSpelling,
  missing_word: exerciseCopy.noteMissingWord,
  extra_word: exerciseCopy.noteExtraWord,
};

function question(prompt: TypedPrompt): Copy {
  if (prompt.kind === "dictation") return exerciseCopy.askDictation;
  // an answer of several words ("tot ziens") is asked for as words
  const words = prompt.hint.letters.length > 1;
  if (prompt.kind === "cloze_typed")
    return words ? exerciseCopy.askClozeTypedWords : exerciseCopy.askClozeTyped;
  return words ? exerciseCopy.askRecallWords : exerciseCopy.askRecall;
}

function hintCopy(hint: Hint): Copy {
  if (hint.letters.length === 1)
    return fill(exerciseCopy.hintWord, { first: hint.first, letters: hint.letters[0] });
  return fill(exerciseCopy.hintWords, {
    first: hint.first,
    count: hint.letters.length,
    letters: hint.letters.join(" + "),
  });
}

interface Props {
  prompt: TypedPrompt;
  sessionId: string;
  itemId: string;
  feedback: Feedback | null;
  onDraft: (answer: Answer | null) => void;
  /** The learner asked for the hint (it is reported with the answer). */
  onHint: () => void;
  /** Enter in the field checks the answer. */
  onSubmit: () => void;
  headingRef?: Ref<HTMLHeadingElement>;
  /** Where the verdict's details go, so "Verder" can read them out. */
  verdictId?: string;
}

/**
 * A typed answer: a typed cloze, a word recalled from its meaning, or a dictation. The field is Dutch and
 * leaves the learner's spelling alone (no capitals, corrections or suggestions from the device). A hint (the
 * first letter and the letters of each word) is there on request; it is read out and focus stays in the
 * field. Answered, it shows what was typed against the answer it was compared with, word by word, and what
 * the comparison forgave or found; overruled by the learner, the same comparison is shown neutrally.
 */
export function TypedItem({
  prompt,
  sessionId,
  itemId,
  feedback,
  onDraft,
  onHint,
  onSubmit,
  headingRef,
  verdictId,
}: Props) {
  const headingId = useId();
  const fieldId = useId();
  const hintId = useId();
  const [text, setText] = useState("");
  const [hinted, setHinted] = useState(false);
  const answered = feedback !== null;
  const hint = prompt.kind === "dictation" ? null : prompt.hint;

  return (
    <div className="exercise-item">
      <ItemHeading className="exercise-question" id={headingId} tabIndex={-1} ref={headingRef}>
        <UiText text={question(prompt)} tier="guide" />
      </ItemHeading>
      <div className="exercise-stem">
        {prompt.kind === "cloze_typed" && (
          <>
            <p className="exercise-sentence" lang="nl">
              {prompt.sentence.split("___")[0]}
              <span className="exercise-gap">
                <span className="visually-hidden">
                  <UiText text={exerciseCopy.blank} inline />
                </span>
              </span>
              {prompt.sentence.split("___").slice(1).join("___")}
            </p>
            <Meaning text={prompt.cue} className="exercise-cue" />
          </>
        )}
        {prompt.kind === "typed_recall" && (
          <p className="exercise-term">
            <Meaning text={prompt.cue} />
          </p>
        )}
        {prompt.kind === "dictation" && (
          <>
            <ItemAudio sessionId={sessionId} itemId={itemId} />
            <p className="exercise-lead">
              <UiText text={fill(exerciseCopy.wordCount, { n: prompt.word_count })} tier="guide" />
            </p>
          </>
        )}
      </div>
      <div className="typed-answer">
        <label className="field-label" htmlFor={fieldId}>
          <UiText text={exerciseCopy.yourAnswer} />
        </label>
        <Input
          id={fieldId}
          aria-describedby={hinted && !answered ? hintId : undefined}
          lang="nl"
          autoCapitalize="off"
          autoCorrect="off"
          spellCheck={false}
          autoComplete="off"
          enterKeyHint="done"
          className="typed-input"
          value={answered ? (feedback.typed ?? text) : text}
          readOnly={answered}
          maxLength={300}
          onChange={(event) => {
            setText(event.target.value);
            onDraft(event.target.value.trim() ? { text: event.target.value } : null);
          }}
          onKeyDown={(event) => {
            if (event.key === "Enter" && !event.nativeEvent.isComposing && !answered) {
              event.preventDefault();
              onSubmit();
            }
          }}
        />
        {hint && !answered && (
          <div className="typed-hint">
            {/* mounted before the hint is asked for, so the hint is announced when it appears */}
            <p className="exercise-lead" role="status" id={hintId}>
              {hinted && <UiText text={hintCopy(hint)} tier="guide" />}
            </p>
            {!hinted && (
              <Button
                variant="ghost"
                size="small"
                icon="lightbulb"
                onClick={() => {
                  setHinted(true);
                  onHint();
                  // the button goes: focus goes back to the answer
                  document.getElementById(fieldId)?.focus();
                }}
              >
                <UiText text={exerciseCopy.showHint} inline />
              </Button>
            )}
          </div>
        )}
      </div>
      {answered && (
        <div className="typed-verdict" id={verdictId}>
          {feedback.diff && hasDifference(feedback.diff) && (
            <TokenDiff ops={feedback.diff} outcome={feedback.outcome} />
          )}
          {feedback.expected && feedback.outcome !== "correct" && (
            <p className="feedback-line">
              {/* overruled, the answer was right too: the check's answer is not "the" right one */}
              <UiText
                text={feedback.outcome === "accepted" ? exerciseCopy.checkExpected : exerciseCopy.rightAnswer}
                inline
              />
              {": "}
              <Dutch text={feedback.expected} />
              <SentenceAudio text={feedback.expected} />
            </p>
          )}
          {(feedback.notes ?? []).length > 0 && (
            <ul className="typed-notes">
              {(feedback.notes ?? [])
                .filter((note) => NOTES[note])
                .map((note) => (
                  <li key={note}>
                    <UiText text={NOTES[note]} tier="guide" />
                  </li>
                ))}
            </ul>
          )}
        </div>
      )}
    </div>
  );
}
