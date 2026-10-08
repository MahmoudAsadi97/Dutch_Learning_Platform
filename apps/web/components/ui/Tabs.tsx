"use client";

import { useRef, type KeyboardEvent, type ReactNode } from "react";

import { Icon, type IconName } from "@/components/Icon";

export interface TabItem<T extends string> {
  id: T;
  label: ReactNode;
  icon?: IconName;
  /** A small count or state shown after the label. */
  badge?: ReactNode;
  disabled?: boolean;
}

interface Props<T extends string> {
  tabs: TabItem<T>[];
  value: T;
  onChange: (id: T) => void;
  /** Accessible name of the whole tab list. */
  label: string;
  /** Returns the id of the panel a tab controls, when the panels carry ids. */
  panelId?: (id: T) => string;
  className?: string;
}

/** A tab list with roving focus: arrows move, Home and End jump, Enter or Space are not needed. */
export function Tabs<T extends string>({ tabs, value, onChange, label, panelId, className = "" }: Props<T>) {
  const buttons = useRef<(HTMLButtonElement | null)[]>([]);

  function onKeyDown(event: KeyboardEvent<HTMLButtonElement>, index: number) {
    const enabled = tabs.map((tab, i) => (tab.disabled ? -1 : i)).filter((i) => i >= 0);
    if (!enabled.length) return;
    const position = enabled.indexOf(index);
    let next: number | undefined;
    if (event.key === "ArrowRight" || event.key === "ArrowDown")
      next = enabled[(position + 1) % enabled.length];
    if (event.key === "ArrowLeft" || event.key === "ArrowUp") {
      next = enabled[(position - 1 + enabled.length) % enabled.length];
    }
    if (event.key === "Home") next = enabled[0];
    if (event.key === "End") next = enabled[enabled.length - 1];
    if (next === undefined) return;
    event.preventDefault();
    buttons.current[next]?.focus();
    onChange(tabs[next].id);
  }

  return (
    <div className={`tabs ${className}`.trim()} role="tablist" aria-label={label}>
      {tabs.map((tab, index) => {
        const selected = tab.id === value;
        return (
          <button
            key={tab.id}
            ref={(element) => {
              buttons.current[index] = element;
            }}
            type="button"
            role="tab"
            className="tab"
            aria-selected={selected}
            aria-controls={panelId?.(tab.id)}
            tabIndex={selected ? 0 : -1}
            disabled={tab.disabled}
            onClick={() => onChange(tab.id)}
            onKeyDown={(event) => onKeyDown(event, index)}
          >
            {tab.icon && <Icon name={tab.icon} size={18} />}
            <span className="tab-label">{tab.label}</span>
            {tab.badge !== undefined && <span className="tab-badge">{tab.badge}</span>}
          </button>
        );
      })}
    </div>
  );
}
