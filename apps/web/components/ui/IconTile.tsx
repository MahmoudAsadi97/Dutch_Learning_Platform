import type { HTMLAttributes } from "react";

import { Icon, type IconName } from "@/components/Icon";
import type { Accent } from "@/lib/design/identity";

interface Props extends HTMLAttributes<HTMLSpanElement> {
  name: IconName;
  /** Overrides the accent of the surrounding section. */
  accent?: Accent;
  size?: "md" | "small";
  solid?: boolean;
  iconSize?: number;
}

export function IconTile({
  name,
  accent,
  size = "md",
  solid = false,
  iconSize,
  className = "",
  ...rest
}: Props) {
  const classes = ["icon-tile", size === "small" ? "small" : "", solid ? "solid" : "", className]
    .filter(Boolean)
    .join(" ");
  return (
    <span className={classes} data-accent={accent} {...rest}>
      <Icon name={name} size={iconSize ?? (size === "small" ? 18 : 22)} />
    </span>
  );
}
