"use client";

import { createContext, useContext, type ComponentPropsWithRef, type ReactNode } from "react";

type Level = 2 | 3 | 4 | 5;

const HeadingContext = createContext<Level>(2);

/** The heading level of a session's questions: 2 on its own page, deeper inside another page's section. */
export function HeadingLevel({ value, children }: { value: Level; children: ReactNode }) {
  return <HeadingContext value={value}>{children}</HeadingContext>;
}

/** A question's or a summary's heading at the session's level (`sub`: one below it). */
export function ItemHeading({ sub = false, ...rest }: { sub?: boolean } & ComponentPropsWithRef<"h2">) {
  const level = Math.min(useContext(HeadingContext) + (sub ? 1 : 0), 6);
  const Tag = `h${level}` as "h2";
  return <Tag {...rest} />;
}
