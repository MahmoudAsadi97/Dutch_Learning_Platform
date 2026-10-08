import type { CSSProperties, ReactNode } from "react";

import { dashOffset, percent } from "@/lib/design/progress";

interface Props {
  value: number;
  max: number;
  /** Accessible name; the ring is an image with this name unless `progressbar` is set. */
  label: string;
  /** Expose the value through the progressbar role instead of an image. */
  progressbar?: boolean;
  size?: number;
  stroke?: number;
  /** `warm` is the streak colour; `accent` follows the section. */
  tone?: "accent" | "warm" | "success";
  className?: string;
  /** What sits in the middle: a number and a caption. */
  children?: ReactNode;
}

/**
 * A ring that fills clockwise from the top. It shows one measured value against one maximum (today's
 * points against the goal) and never an overall level; the text inside carries the same facts.
 */
export function ProgressRing({
  value,
  max,
  label,
  progressbar = false,
  size = 138,
  stroke = 8,
  tone = "accent",
  className = "",
  children,
}: Props) {
  const radius = 50 - stroke / 2;
  const roleProps = progressbar
    ? {
        role: "progressbar" as const,
        "aria-label": label,
        "aria-valuenow": Math.min(value, max),
        "aria-valuemin": 0,
        "aria-valuemax": max,
      }
    : { role: "img" as const, "aria-label": label };
  return (
    <div
      className={`progress-ring ${tone} ${className}`.trim()}
      style={{ "--ring-size": `${size}px` } as CSSProperties}
      data-percent={percent(value, max)}
      {...roleProps}
    >
      <svg viewBox="0 0 100 100" aria-hidden="true" focusable="false">
        <circle className="progress-ring-track" cx="50" cy="50" r={radius} strokeWidth={stroke} />
        <circle
          className="progress-ring-fill"
          cx="50"
          cy="50"
          r={radius}
          strokeWidth={stroke}
          pathLength={100}
          strokeDasharray="100"
          strokeDashoffset={dashOffset(value, max)}
        />
      </svg>
      <div className="progress-ring-content">{children}</div>
    </div>
  );
}
