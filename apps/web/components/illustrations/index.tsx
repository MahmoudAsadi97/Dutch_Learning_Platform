import type { CSSProperties } from "react";

/**
 * A small set of inline illustrations in the accent of the section they sit in. They are decorative:
 * every one is hidden from assistive technology and the text beside it says what matters.
 */
export type IllustrationName = "writer" | "stories" | "goal" | "words" | "quiet";

const SHAPES: Record<IllustrationName, React.ReactElement> = {
  writer: (
    <>
      <rect x="14" y="20" width="52" height="40" rx="6" className="ill-paper" />
      <rect x="22" y="30" width="36" height="3" rx="1.5" className="ill-line" />
      <rect x="22" y="38" width="28" height="3" rx="1.5" className="ill-line" />
      <rect x="22" y="46" width="20" height="3" rx="1.5" className="ill-line" />
      <path d="M58 54 L72 40 L78 46 L64 60 L56 62 Z" className="ill-accent" />
    </>
  ),
  stories: (
    <>
      <path d="M12 22 C24 14 36 14 40 22 V62 C36 56 24 56 12 62 Z" className="ill-accent" />
      <path d="M68 22 C56 14 44 14 40 22 V62 C44 56 56 56 68 62 Z" className="ill-paper" />
      <rect x="47" y="28" width="14" height="3" rx="1.5" className="ill-line" />
      <rect x="47" y="36" width="14" height="3" rx="1.5" className="ill-line" />
    </>
  ),
  goal: (
    <>
      <circle cx="40" cy="40" r="26" className="ill-paper" />
      <circle cx="40" cy="40" r="16" className="ill-accent-soft" />
      <circle cx="40" cy="40" r="6" className="ill-accent" />
      <path d="M40 14 V40" className="ill-stroke" />
    </>
  ),
  words: (
    <>
      <rect x="10" y="26" width="34" height="24" rx="5" className="ill-accent" />
      <rect x="30" y="34" width="40" height="24" rx="5" className="ill-paper" />
      <rect x="38" y="42" width="24" height="3" rx="1.5" className="ill-line" />
      <rect x="38" y="49" width="16" height="3" rx="1.5" className="ill-line" />
    </>
  ),
  quiet: (
    <>
      <rect x="30" y="12" width="20" height="36" rx="10" className="ill-accent" />
      <path d="M22 40 a18 18 0 0 0 36 0" className="ill-stroke" />
      <path d="M40 58 V66 M30 66 H50" className="ill-stroke" />
    </>
  ),
};

export function Illustration({
  name,
  size = 80,
  className = "",
  style,
}: {
  name: IllustrationName;
  size?: number;
  className?: string;
  style?: CSSProperties;
}) {
  return (
    <svg
      className={`illustration ${className}`.trim()}
      viewBox="0 0 80 80"
      width={size}
      height={size}
      aria-hidden="true"
      focusable="false"
      style={style}
    >
      {SHAPES[name]}
    </svg>
  );
}
