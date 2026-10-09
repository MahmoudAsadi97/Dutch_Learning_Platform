"use client";

import { createContext, useContext, useEffect, useRef, useSyncExternalStore, type ReactNode } from "react";

import { useQueryClient } from "@tanstack/react-query";

import { useProfile, updateProfile, type Me } from "@/lib/client/profile";
import { glossLevelFor, type GlossLevel } from "@/lib/client/gloss";
import { reconcileMode, type SupportMode } from "@/lib/client/profile-sync";
import { queryKeys } from "@/lib/client/query-keys";
import { storageKeys } from "@/lib/client/storage";

export type { SupportMode };
export type LearningCopy = { nl: string; en?: string; fa?: string };
const key = storageKeys.languageSupport;
const changeEvent = "taalstudio:language-support";
let volatileMode: SupportMode = "nl-en";
const LanguageContext = createContext({
  mode: "nl-en" as SupportMode,
  setMode: (() => {}) as (mode: SupportMode) => void,
  showEnglish: true,
  showPersian: false,
  glossLevel: "chrome" as GlossLevel,
});

function readMode(): SupportMode {
  try {
    const value = localStorage.getItem(key);
    return value === "nl-fa" || value === "nl-fa-en" ? value : "nl-en";
  } catch {
    return volatileMode;
  }
}
function writeMode(value: SupportMode) {
  volatileMode = value;
  try {
    localStorage.setItem(key, value);
  } catch {
    /* Storage may be disabled. */
  }
  window.dispatchEvent(new Event(changeEvent));
}
function subscribe(listener: () => void) {
  window.addEventListener(changeEvent, listener);
  window.addEventListener("storage", listener);
  return () => {
    window.removeEventListener(changeEvent, listener);
    window.removeEventListener("storage", listener);
  };
}

/**
 * The device keeps a synchronous copy of the support mode so the first paint never flashes; the server
 * profile is the record. On load the two are reconciled once: a server without a value adopts the
 * device's choice, otherwise the server wins. Every change the learner makes is written to both.
 */
export function LanguageProvider({ children }: { children: ReactNode }) {
  const mode = useSyncExternalStore(subscribe, readMode, () => "nl-en" as SupportMode);
  const profile = useProfile();
  const client = useQueryClient();
  const reconciled = useRef(false);
  // the header writes the support language straight to the server; the cached profile follows
  const remember = (me: Me) => client.setQueryData(queryKeys.me(), me);
  useEffect(() => {
    if (reconciled.current || !profile.data) return;
    reconciled.current = true;
    const result = reconcileMode(readMode(), profile.data.profile.support_mode);
    if (result.upload) {
      updateProfile({ support_mode: result.mode }).then(remember, () => undefined);
    } else if (result.mode !== readMode()) {
      writeMode(result.mode);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps -- reconcile once, when the profile first arrives
  }, [profile.data]);
  function setMode(value: SupportMode) {
    writeMode(value);
    updateProfile({ support_mode: value }).then(remember, () => undefined);
  }
  const glossLevel = glossLevelFor(
    profile.data?.profile.stage_id,
    profile.data?.profile.gloss_mode ?? "auto",
  );
  return (
    <LanguageContext.Provider
      value={{ mode, setMode, showEnglish: mode !== "nl-fa", showPersian: mode !== "nl-en", glossLevel }}
    >
      {children}
    </LanguageContext.Provider>
  );
}
export function useLanguageSupport() {
  return useContext(LanguageContext);
}

/** Dutch remains the practice language. Support lines follow the learner's selected languages. */
export function LearningText({
  text,
  className = "",
  supportOnly = false,
}: {
  text?: LearningCopy | null;
  className?: string;
  supportOnly?: boolean;
}) {
  const { showEnglish, showPersian } = useLanguageSupport();
  if (!text) return null;
  return (
    <span className={`learning-copy ${className}`}>
      {!supportOnly && (
        <span lang="nl" className="copy-dutch">
          {text.nl}
        </span>
      )}
      {showEnglish && text.en && (
        <>
          {" "}
          <span lang="en" className="copy-support">
            {text.en}
          </span>
        </>
      )}
      {showPersian && text.fa && (
        <>
          {" "}
          <span lang="fa" dir="rtl" className="copy-support fa">
            {text.fa}
          </span>
        </>
      )}
    </span>
  );
}

export function LanguageSwitcher() {
  const { mode, setMode } = useLanguageSupport();
  return (
    <div className="language-control">
      <label htmlFor="language-support">
        Taalhulp <span lang="en">/ language</span>
      </label>
      <select
        id="language-support"
        value={mode}
        onChange={(event) => setMode(event.target.value as SupportMode)}
      >
        <option value="nl-en">Nederlands · English</option>
        <option value="nl-fa">Nederlands · فارسی</option>
        <option value="nl-fa-en">Nederlands · فارسی · English</option>
      </select>
    </div>
  );
}
