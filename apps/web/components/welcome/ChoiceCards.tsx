"use client";

import type { ReactNode } from "react";

export interface Choice<T extends string> {
  value: T;
  title: ReactNode;
  detail?: ReactNode;
}

/**
 * A group of large single-choice cards. Each card is a native radio with its label, so arrow keys,
 * the form semantics and the screen-reader announcement come from the browser; the transparent input
 * covers the whole card, so the card is the target.
 */
export function ChoiceCards<T extends string>({
  name,
  legend,
  choices,
  value,
  onChange,
  columns = 2,
}: {
  name: string;
  legend: ReactNode;
  choices: Choice<T>[];
  value: T | null;
  onChange: (value: T) => void;
  columns?: 1 | 2 | 3;
}) {
  return (
    <fieldset className="choice-group">
      <legend className="choice-legend">{legend}</legend>
      <div className={`choice-grid columns-${columns}`}>
        {choices.map((choice) => (
          <label key={choice.value} className="choice-card">
            <input
              type="radio"
              className="choice-input"
              name={name}
              value={choice.value}
              checked={value === choice.value}
              onChange={() => onChange(choice.value)}
            />
            <span className="choice-title">{choice.title}</span>
            {choice.detail && <span className="choice-detail">{choice.detail}</span>}
          </label>
        ))}
      </div>
    </fieldset>
  );
}
