import type { ReactNode } from "react";

/** One of six cover pairs, chosen by the episode number so a serial cycles through them. */
export function coverTone(number: number): number {
  return ((Math.max(1, Math.floor(number)) - 1) % 6) + 1;
}

/** The class string the episode screens already rely on. */
export function coverClass(number: number): string {
  return `episode-cover tone-${coverTone(number)}`;
}

interface Props {
  number: number;
  /** The small caption in the corner: the town, the series, the kind. */
  caption?: ReactNode;
  className?: string;
  children?: ReactNode;
}

/** A decorative cover: a large number on a tinted pair; hidden from assistive technology. */
export function Cover({ number, caption, className = "", children }: Props) {
  return (
    <div className={`${coverClass(number)} ${className}`.trim()} aria-hidden="true">
      <span className="cover-number">{number}</span>
      {caption !== undefined && <span className="cover-town">{caption}</span>}
      {children}
    </div>
  );
}
