"use client";

import { createContext, useContext, type ReactNode } from "react";

const DeveloperContext = createContext(false);

/** The shell says whether this is a development or test environment; production hides developer details. */
export function DeveloperDetailsProvider({ show, children }: { show: boolean; children: ReactNode }) {
  return <DeveloperContext.Provider value={show}>{children}</DeveloperContext.Provider>;
}

/**
 * True outside production: model names, failure codes, the local run command and the recording format
 * help whoever runs the app, and mean nothing to a learner.
 */
export function useDeveloperDetails(): boolean {
  return useContext(DeveloperContext);
}
