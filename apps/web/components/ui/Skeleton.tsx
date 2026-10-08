import type { ReactNode } from "react";

interface Props {
  kind?: "text" | "block" | "circle";
  /** Number of text lines; ignored for the other kinds. */
  lines?: number;
  width?: string | number;
  height?: string | number;
  className?: string;
}

/** Placeholder shapes; hidden from assistive technology, so pair them with a `SkeletonPanel` status. */
export function Skeleton({ kind = "text", lines = 1, width, height, className = "" }: Props) {
  const count = kind === "text" ? Math.max(1, lines) : 1;
  return (
    <>
      {Array.from({ length: count }, (_, index) => (
        <span
          key={index}
          className={`skeleton ${kind} ${className}`.trim()}
          style={{ width: index === count - 1 && kind === "text" && count > 1 ? "40%" : width, height }}
          aria-hidden="true"
          data-anim="shimmer"
        />
      ))}
    </>
  );
}

export function SkeletonPanel({
  label = "Bezig met laden",
  className = "",
  children,
}: {
  label?: string;
  className?: string;
  children?: ReactNode;
}) {
  return (
    <div className={`skeleton-panel ${className}`.trim()} role="status" aria-live="polite">
      <span className="visually-hidden">{label}</span>
      {children}
    </div>
  );
}
