"use client";

import { useSyncExternalStore } from "react";
import { isStageId, type StageId } from "../domain/registry";
import { storageKeys } from "./storage";

const changed = "taalstudio:study-stage";
let temporary: StageId | null = null;
function read(): StageId | null {
  try {
    const value = localStorage.getItem(storageKeys.studyStage);
    return value && isStageId(value) ? value : null;
  } catch {
    return temporary;
  }
}
function subscribe(listener: () => void) {
  window.addEventListener(changed, listener);
  window.addEventListener("storage", listener);
  return () => {
    window.removeEventListener(changed, listener);
    window.removeEventListener("storage", listener);
  };
}
export function rememberStudyStage(stage: string) {
  if (!isStageId(stage)) return;
  temporary = stage;
  try {
    localStorage.setItem(storageKeys.studyStage, stage);
  } catch {
    /* Optional preference. */
  }
  window.dispatchEvent(new Event(changed));
}
export function useLastStudyStage() {
  return useSyncExternalStore(subscribe, read, () => null);
}
