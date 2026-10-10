"use client";

import type { ReactNode } from "react";

import { Icon } from "@/components/Icon";
import { UiText } from "@/components/ui/UiText";
import { exerciseCopy } from "@/lib/copy/exercise";
import { usePrefersReducedMotion } from "@/lib/client/motion";
import { uiCopy } from "@/lib/ui-copy";

/**
 * What an option shows after the server's verdict: the learner's right choice (`correct`), their choice that
 * was not right (`incorrect`), the right option they did not choose (`reveal`), or an option the verdict is
 * not about (`idle`). "Almost" never applies to a single option: it belongs to typed answers.
 */
export type AnswerState = "correct" | "incorrect" | "reveal" | "idle";

interface Props {
  name: string;
  value: string;
  checked: boolean;
  onSelect: (value: string) => void;
  /** Set once the item is answered: the options are then read-only and show their state. */
  verdict?: AnswerState;
  /** The key that chooses it (1 to 4), shown as a hint. */
  shortcut?: number;
  children: ReactNode;
  /** Shown under the option once it is answered: its glosses. */
  after?: ReactNode;
}

const MARKS = {
  correct: { icon: "check", text: uiCopy.state.correct },
  incorrect: { icon: "close", text: exerciseCopy.yourAnswer },
  reveal: { icon: "check", text: exerciseCopy.rightAnswer },
} as const;

/**
 * One answer to choose: a native radio inside its label (so clicks, arrow keys and screen readers work as
 * they do everywhere), drawn as a card. The state shows as colour, an icon and words, never colour alone;
 * a wrong choice is a soft red that shakes once (unless motion is reduced), never a solid fill.
 */
export function AnswerOption({ name, value, checked, onSelect, verdict, shortcut, children, after }: Props) {
  const reducedMotion = usePrefersReducedMotion();
  const answered = verdict !== undefined;
  const state = verdict ?? (checked ? "selected" : "default");
  const mark = verdict && verdict !== "idle" ? MARKS[verdict] : null;
  return (
    <label
      className="answer-option"
      data-state={state}
      data-anim={verdict === "incorrect" && !reducedMotion ? "shake" : undefined}
    >
      <input
        className="answer-option-input"
        type="radio"
        name={name}
        value={value}
        checked={checked}
        disabled={answered}
        onChange={() => onSelect(value)}
      />
      {shortcut !== undefined && (
        <span className="answer-option-key" aria-hidden="true">
          {shortcut}
        </span>
      )}
      <span className="answer-option-body">
        <span className="answer-option-text">{children}</span>
        {/* real spaces, so the accessible name reads "het raam Het juiste antwoord", not one run-on word */}
        {mark && " "}
        {mark && (
          <span className="answer-option-mark">
            <Icon name={mark.icon} size={16} />
            <UiText text={mark.text} inline />
          </span>
        )}
        {after && " "}
        {after}
      </span>
    </label>
  );
}
