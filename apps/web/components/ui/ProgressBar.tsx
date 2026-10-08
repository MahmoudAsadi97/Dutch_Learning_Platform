import { percent } from "@/lib/design/progress";

interface Props {
  value: number;
  max: number;
  label: string;
  tone?: "accent" | "warm" | "success";
  /** Thin bars sit under a card title; regular bars stand on their own. */
  size?: "thin" | "regular";
  className?: string;
}

/** A horizontal bar for one value against one maximum, exposed as a progressbar. */
export function ProgressBar({ value, max, label, tone = "accent", size = "regular", className = "" }: Props) {
  return (
    <div
      className={`progress-bar ${tone} ${size} ${className}`.trim()}
      role="progressbar"
      aria-label={label}
      aria-valuenow={Math.min(value, max)}
      aria-valuemin={0}
      aria-valuemax={max}
    >
      <span style={{ width: `${percent(value, max)}%` }} />
    </div>
  );
}
