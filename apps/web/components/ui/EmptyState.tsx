import type { ReactNode } from "react";

import type { IconName } from "@/components/Icon";
import { IconTile } from "@/components/ui/IconTile";
import type { Accent } from "@/lib/design/identity";

interface Props {
  icon?: IconName;
  accent?: Accent;
  title: ReactNode;
  description?: ReactNode;
  /** One action, usually a Button or ButtonLink. */
  children?: ReactNode;
  className?: string;
}

export function EmptyState({
  icon = "sparkles",
  accent,
  title,
  description,
  children,
  className = "",
}: Props) {
  return (
    <div className={`empty-state ${className}`.trim()}>
      <IconTile name={icon} accent={accent} />
      <div className="empty-state-copy">
        <h3>{title}</h3>
        {description && <p>{description}</p>}
        {children}
      </div>
    </div>
  );
}
