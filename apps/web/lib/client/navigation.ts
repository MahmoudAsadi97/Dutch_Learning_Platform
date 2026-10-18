"use client";
import { createContext, useContext } from "react";
export type LeaveGuard = (() => Promise<boolean>) | null;
export const NavigationGuardContext = createContext<(guard: LeaveGuard) => void>(() => {});
export const NavigationCheckContext = createContext<() => Promise<boolean>>(async () => true);
export function useNavigationGuard() {
  return useContext(NavigationGuardContext);
}
export function useNavigationCheck() {
  return useContext(NavigationCheckContext);
}
