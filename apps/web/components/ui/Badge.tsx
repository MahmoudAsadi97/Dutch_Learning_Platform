import type { HTMLAttributes, ReactNode } from "react";

export type BadgeTone = "neutral" | "ok" | "warn" | "bad" | "info" | "accent";

interface Props extends HTMLAttributes<HTMLSpanElement> {
  tone?: BadgeTone;
  children?: ReactNode;
}

/** A status pill. Feedback tones are green, amber and red; `accent` follows the section. */
export function Badge({ tone = "neutral", className = "", children, ...rest }: Props) {
  return (
    <span className={["label", tone, className].filter(Boolean).join(" ")} {...rest}>
      {children}
    </span>
  );
}
