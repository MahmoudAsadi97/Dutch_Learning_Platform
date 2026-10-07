import type { HTMLAttributes, ReactNode } from "react";

interface Props extends HTMLAttributes<HTMLElement> {
  as?: "section" | "div" | "article" | "aside";
  /** `tinted` takes the accent of the section it sits in. */
  tone?: "default" | "tinted";
  flat?: boolean;
  children?: ReactNode;
}

export function Card({
  as = "section",
  tone = "default",
  flat = false,
  className = "",
  children,
  ...rest
}: Props) {
  const Tag = as;
  const classes = ["card", tone === "tinted" ? "tinted" : "", flat ? "flat" : "", className]
    .filter(Boolean)
    .join(" ");
  return (
    <Tag className={classes} {...rest}>
      {children}
    </Tag>
  );
}
