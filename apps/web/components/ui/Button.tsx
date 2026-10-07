import Link from "next/link";
import type { ButtonHTMLAttributes, ComponentProps, ReactNode } from "react";

import { Icon, type IconName } from "@/components/Icon";

export type ButtonVariant = "primary" | "secondary" | "ghost" | "danger" | "talk";
export type ButtonSize = "md" | "small";

interface Look {
  variant?: ButtonVariant;
  size?: ButtonSize;
  className?: string;
}

/** The class string for a `.button`, for the places that render their own element (a Link, a label). */
export function buttonClass({ variant = "primary", size = "md", className = "" }: Look = {}) {
  return ["button", variant === "primary" ? "" : variant, size === "small" ? "small" : "", className]
    .filter(Boolean)
    .join(" ");
}

interface Extras extends Look {
  /** An icon before the text, or after it with `iconEnd`. */
  icon?: IconName;
  iconEnd?: boolean;
  children?: ReactNode;
}

function Content({ icon, iconEnd, children }: Extras) {
  if (!icon) return <>{children}</>;
  const glyph = <Icon name={icon} size={16} />;
  return iconEnd ? (
    <>
      {children}
      {glyph}
    </>
  ) : (
    <>
      {glyph}
      {children}
    </>
  );
}

export function Button({
  variant,
  size,
  icon,
  iconEnd,
  className,
  type = "button",
  children,
  ...rest
}: ButtonHTMLAttributes<HTMLButtonElement> & Extras) {
  return (
    <button type={type} className={buttonClass({ variant, size, className })} {...rest}>
      <Content icon={icon} iconEnd={iconEnd}>
        {children}
      </Content>
    </button>
  );
}

export function ButtonLink({
  variant,
  size,
  icon,
  iconEnd,
  className,
  children,
  ...rest
}: ComponentProps<typeof Link> & Extras) {
  return (
    <Link className={buttonClass({ variant, size, className })} {...rest}>
      <Content icon={icon} iconEnd={iconEnd}>
        {children}
      </Content>
    </Link>
  );
}
