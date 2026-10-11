"use client";

import { useId, type ReactNode, type Ref } from "react";

import { AnswerOption, type AnswerState } from "@/components/ui/AnswerOption";
import { UiText } from "@/components/ui/UiText";
import { exerciseCopy } from "@/lib/copy/exercise";
import type { Feedback, Option, SupportOption } from "@/lib/client/exercises";
import type { Copy } from "@/lib/ui-copy";

import { Dutch, Meaning } from "./ContentText";
import type { ChoicePrompt } from "./registry";

function question(prompt: ChoicePrompt): Copy {
  if (prompt.kind === "cloze_choice") return exerciseCopy.askCloze;
  if (prompt.kind === "odd_one_out") return exerciseCopy.askOdd;
  if (prompt.kind === "listen_choose") return exerciseCopy.askListen;
  switch (prompt.direction) {
    case "meaning":
      return exerciseCopy.askMeaning;
    case "term":
      return exerciseCopy.askTerm;
    case "definition":
      return exerciseCopy.askDefinition;
    default:
      return exerciseCopy.askQuestion;
  }
}

/** What the question is about: a Dutch word, a meaning, a sentence with a gap, a topic, a question or a sound. */
function Stem({ prompt, audio }: { prompt: ChoicePrompt; audio?: ReactNode }) {
  if (prompt.kind === "listen_choose") return <div className="exercise-stem">{audio}</div>;
  if (prompt.kind === "cloze_choice") {
    const [before, ...rest] = prompt.sentence.split("___");
    return (
      <div className="exercise-stem">
        <p className="exercise-sentence" lang="nl">
          {before}
          <span className="exercise-gap">
            <span className="visually-hidden">
              <UiText text={exerciseCopy.blank} inline />
            </span>
          </span>
          {rest.join("___")}
        </p>
        <Meaning text={prompt.cue} className="exercise-cue" />
      </div>
    );
  }
  if (prompt.kind === "odd_one_out") {
    return (
      <div className="exercise-stem">
        <p className="exercise-topic">
          <UiText text={exerciseCopy.oddTopic} tier="guide" />{" "}
          <strong>
            <Dutch text={prompt.topic.nl} />
          </strong>{" "}
          <Meaning text={prompt.topic} />
        </p>
      </div>
    );
  }
  if (prompt.direction === "term")
    return (
      <div className="exercise-stem">
        <p className="exercise-term">
          <Meaning text={prompt.stem} />
        </p>
      </div>
    );
  if (prompt.direction === "question")
    return (
      <div className="exercise-stem">
        <p className="exercise-prompt">
          <Dutch text={prompt.stem.nl} />
        </p>
      </div>
    );
  return (
    <div className="exercise-stem">
      <p className="exercise-term">
        <Dutch text={prompt.stem.nl} />
      </p>
    </div>
  );
}

/** An option before the answer: Dutch alone (no glosses that give it away), or a meaning to choose. */
function OptionText({ prompt, option }: { prompt: ChoicePrompt; option: Option }) {
  if (prompt.kind === "choice" && prompt.direction === "meaning") return <Meaning text={option} />;
  return <Dutch text={option.nl} />;
}

/** What an option adds once answered: the meaning of a Dutch option, or the Dutch word of a meaning. */
function OptionAfter({ prompt, support }: { prompt: ChoicePrompt; support?: SupportOption }) {
  if (!support) return null;
  if (prompt.kind === "choice" && prompt.direction === "meaning")
    return <Dutch text={support.nl} className="answer-option-after" />;
  if (prompt.kind === "choice" && prompt.direction === "definition")
    return (
      <span className="answer-option-after">
        <Dutch text={support.nl} /> <Meaning text={support} />
      </span>
    );
  return <Meaning text={support} className="answer-option-after" />;
}

function verdictFor(option: string, feedback: Feedback | null): AnswerState | undefined {
  if (!feedback) return undefined;
  if (option === feedback.correct) return feedback.given === option ? "correct" : "reveal";
  if (option === feedback.given) return "incorrect";
  return "idle";
}

interface Props {
  prompt: ChoicePrompt;
  selected: string | null;
  onSelect: (option: string) => void;
  /** The verdict of the answer just given, or of an item already closed. */
  feedback: Feedback | null;
  headingRef?: Ref<HTMLHeadingElement>;
  /** Listen and choose: the control that plays the item's sound. */
  audio?: ReactNode;
}

/**
 * Choice, cloze by choice, odd one out and listen-and-choose: a question, its stem (or its sound) and up to
 * four options in a radio group.
 */
export function ChoiceItem({ prompt, selected, onSelect, feedback, headingRef, audio }: Props) {
  const name = useId();
  const headingId = useId();
  const support = new Map((feedback?.support ?? []).map((entry) => [entry.id, entry]));
  return (
    <div className="exercise-item">
      <h2 className="exercise-question" id={headingId} tabIndex={-1} ref={headingRef}>
        <UiText text={question(prompt)} tier="guide" />
      </h2>
      <Stem prompt={prompt} audio={audio} />
      <fieldset className="answer-group" aria-labelledby={headingId}>
        <div className="answer-list">
          {prompt.options.map((option, index) => (
            <AnswerOption
              key={option.id}
              name={name}
              value={option.id}
              checked={feedback ? feedback.given === option.id : selected === option.id}
              onSelect={onSelect}
              verdict={verdictFor(option.id, feedback)}
              shortcut={index < 9 ? index + 1 : undefined}
              after={feedback ? <OptionAfter prompt={prompt} support={support.get(option.id)} /> : null}
            >
              <OptionText prompt={prompt} option={option} />
            </AnswerOption>
          ))}
        </div>
      </fieldset>
    </div>
  );
}
