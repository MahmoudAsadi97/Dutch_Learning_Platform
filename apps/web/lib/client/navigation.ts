"use client";
import { createContext, useContext } from "react";
export type LeaveGuard = (() => Promise<boolean>) | null;
export const NavigationGuardContext = createContext<
  (guard: LeaveGuard) => void
>(() => {});
export function useNavigationGuard() {
  return useContext(NavigationGuardContext);
}
