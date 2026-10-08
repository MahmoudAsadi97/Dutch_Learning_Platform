"use client";

import type { ReactNode } from "react";

import { Icon, type IconName } from "@/components/Icon";

export interface SegmentOption<T extends string> {
  value: T;
  label: ReactNode;
  icon?: IconName;
  disabled?: boolean;
}

interface Props<T extends string> {
  options: SegmentOption<T>[];
  value: T;
  onChange: (value: T) => void;
  /** Accessible name of the group. */
  label: string;
  className?: string;
}

/** A small set of mutually exclusive choices, shown as pressed buttons in one pill. */
export function Segmented<T extends string>({ options, value, onChange, label, className = "" }: Props<T>) {
  return (
    <div className={`segmented ${className}`.trim()} role="group" aria-label={label}>
      {options.map((option) => (
        <button
          key={option.value}
          type="button"
          className="segment"
          aria-pressed={option.value === value}
          disabled={option.disabled}
          onClick={() => onChange(option.value)}
        >
          {option.icon && <Icon name={option.icon} size={16} />}
          {option.label}
        </button>
      ))}
    </div>
  );
}
