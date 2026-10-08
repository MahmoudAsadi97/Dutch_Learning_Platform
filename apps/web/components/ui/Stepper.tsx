"use client";

import type { ReactNode } from "react";

import { Icon } from "@/components/Icon";

export interface StepItem<T extends string> {
  key: T;
  title: ReactNode;
  /** A short line above the title: the skill, the duration, the kind. */
  meta?: ReactNode;
  done?: boolean;
}

interface Props<T extends string> {
  steps: StepItem<T>[];
  current?: T;
  /** When given, steps are buttons; otherwise they are plain list items. */
  onSelect?: (key: T) => void;
  disabled?: boolean;
  /** Accessible name of the list. */
  label?: string;
  className?: string;
}

/** An ordered list of steps with one current step; done steps show a check instead of their number. */
export function Stepper<T extends string>({
  steps,
  current,
  onSelect,
  disabled,
  label,
  className = "",
}: Props<T>) {
  return (
    <ol className={`stepper ${className}`.trim()} aria-label={label}>
      {steps.map((step, index) => {
        const isCurrent = step.key === current;
        const body = (
          <>
            <span className={`step-mark ${step.done ? "done" : ""}`.trim()} aria-hidden="true">
              {step.done ? <Icon name="check" size={14} /> : index + 1}
            </span>
            <span className="step-copy">
              {step.meta && <span className="step-meta">{step.meta}</span>}
              <span className="step-title">{step.title}</span>
              {step.done && <span className="visually-hidden">, afgerond</span>}
            </span>
          </>
        );
        return (
          <li key={step.key} className={step.done ? "is-done" : undefined}>
            {onSelect ? (
              <button
                type="button"
                className="step"
                aria-current={isCurrent ? "step" : undefined}
                disabled={disabled}
                onClick={() => onSelect(step.key)}
              >
                {body}
              </button>
            ) : (
              <span className="step" aria-current={isCurrent ? "step" : undefined}>
                {body}
              </span>
            )}
          </li>
        );
      })}
    </ol>
  );
}
