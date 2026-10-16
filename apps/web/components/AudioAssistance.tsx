"use client";

import { createContext, useContext, type ReactNode } from "react";

type RegisterAudioAssistance = (signal: AbortSignal) => Promise<void> | void;
const AudioAssistanceContext = createContext<RegisterAudioAssistance | undefined>(undefined);

/** Optional study playback may change assessed evidence; its owning session records that before sound. */
export function AudioAssistanceProvider({
  onRequest,
  children,
}: {
  onRequest: RegisterAudioAssistance;
  children: ReactNode;
}) {
  return <AudioAssistanceContext.Provider value={onRequest}>{children}</AudioAssistanceContext.Provider>;
}

export function useAudioAssistance() {
  return useContext(AudioAssistanceContext);
}
