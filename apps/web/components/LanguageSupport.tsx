"use client";

import { createContext, useContext, useEffect, useRef, useSyncExternalStore, type ReactNode } from "react";

import { useQueryClient } from "@tanstack/react-query";

import { useProfile, updateProfile, type Me } from "@/lib/client/profile";
import { glossLevelFor, type GlossLevel } from "@/lib/client/gloss";
import { isSupportMode, reconcileMode, type SupportMode } from "@/lib/client/profile-sync";
import { queryKeys } from "@/lib/client/query-keys";
import { storageKeys } from "@/lib/client/storage";

export type { SupportMode };
export type LearningCopy = { nl: string; en?: string; fa?: string };
const key = storageKeys.languageSupport;
const unsentKey = storageKeys.languageSupportUnsent;
const changeEvent = "taalstudio:language-support";
/** Fallbacks for a browser whose storage is disabled. */
let volatileStored: SupportMode | null = null;
let volatileUnsent = false;
const LanguageContext = createContext({
  mode: "nl-en" as SupportMode,
  setMode: (() => {}) as (mode: SupportMode) => void,
  showEnglish: true,
  showPersian: false,
  glossLevel: "chrome" as GlossLevel,
});

/** The mode chosen on this device, or null when the learner never chose one here. */
function readStored(): SupportMode | null {
  try {
    const value = localStorage.getItem(key);
    return isSupportMode(value) ? value : null;
  } catch {
    return volatileStored;
  }
}
function writeMode(value: SupportMode) {
  volatileStored = value;
  try {
    localStorage.setItem(key, value);
  } catch {
    /* Storage may be disabled. */
  }
  window.dispatchEvent(new Event(changeEvent));
}
function readUnsent(): boolean {
  try {
    return localStorage.getItem(unsentKey) === "1";
  } catch {
    return volatileUnsent;
  }
}
function markUnsent(on: boolean) {
  volatileUnsent = on;
  try {
    if (on) localStorage.setItem(unsentKey, "1");
    else localStorage.removeItem(unsentKey);
  } catch {
    /* Storage may be disabled. */
  }
}
function subscribe(listener: () => void) {
  window.addEventListener(changeEvent, listener);
  window.addEventListener("storage", listener);
  return () => {
    window.removeEventListener(changeEvent, listener);
    window.removeEventListener("storage", listener);
  };
}

/** Saves go out one after another, so a quick second change can never be overtaken by the first. */
let saving: Promise<unknown> = Promise.resolve();
function send(value: SupportMode, remember: (me: Me) => void) {
  markUnsent(true);
  saving = saving
    .then(() => updateProfile({ support_mode: value }))
    .then(
      (me) => {
        // only the latest choice clears the mark; an older save that lands first leaves it set
        if (readStored() === value) markUnsent(false);
        remember(me);
      },
      () => undefined,
    );
}

/**
 * The device keeps a synchronous copy of the support mode so the first paint never flashes; the server
 * profile is the record, and the server render already knows it. On load the two are reconciled once
 * (see profile-sync.ts); every change the learner makes goes to both, and a change that never reached
 * the server is sent again on the next load.
 */
export function LanguageProvider({ children }: { children: ReactNode }) {
  const profile = useProfile();
  const serverMode = profile.data?.profile.support_mode ?? "nl-en";
  const mode = useSyncExternalStore(
    subscribe,
    () => readStored() ?? serverMode,
    () => serverMode,
  );
  const client = useQueryClient();
  const reconciled = useRef(false);
  // a save answers with the whole profile; take only its support language, a level saved meanwhile stays
  const remember = (me: Me) =>
    client.setQueryData<Me>(queryKeys.me(), (old) =>
      old ? { ...old, profile: { ...old.profile, support_mode: me.profile.support_mode } } : me,
    );
  useEffect(() => {
    if (reconciled.current || !profile.data) return;
    reconciled.current = true;
    const server = profile.data.profile.support_mode;
    const result = reconcileMode({ stored: readStored(), pending: readUnsent() }, server);
    if (result.upload) send(result.mode, remember);
    else if (isSupportMode(server) && readStored() !== server) writeMode(server);
    // eslint-disable-next-line react-hooks/exhaustive-deps -- reconcile once, when the profile first arrives
  }, [profile.data]);
  function setMode(value: SupportMode) {
    writeMode(value);
    send(value, remember);
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
