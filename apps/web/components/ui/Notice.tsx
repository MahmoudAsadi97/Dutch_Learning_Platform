import type { HTMLAttributes, ReactNode, Ref } from "react";

import { Icon, type IconName } from "@/components/Icon";

export type NoticeTone = "neutral" | "info" | "success" | "warning" | "danger";

const defaultIcons: Record<NoticeTone, IconName | null> = {
  neutral: null,
  info: "info",
  success: "check",
  warning: "alert",
  danger: "alert",
};

interface Props extends Omit<HTMLAttributes<HTMLDivElement>, "title"> {
  tone?: NoticeTone;
  title?: ReactNode;
  /** Override the tone's icon, or pass `null` for none. */
  icon?: IconName | null;
  children?: ReactNode;
  ref?: Ref<HTMLDivElement>;
}

/** A message block with a tone. Pass `role="alert"` or `role="status"` when it appears after an action. */
export function Notice({ tone = "neutral", title, icon, className = "", children, ref, ...rest }: Props) {
  const glyph = icon === undefined ? defaultIcons[tone] : icon;
  return (
    <div
      ref={ref}
      className={["notice", tone === "neutral" ? "" : tone, className].filter(Boolean).join(" ")}
      {...rest}
    >
      {glyph && <Icon name={glyph} size={18} />}
      <div className="notice-body">
        {title && <strong className="notice-title">{title}</strong>}
        {children}
      </div>
    </div>
  );
}
