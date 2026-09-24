"use client";

import { createContext, useContext, useSyncExternalStore, type ReactNode } from "react";

export type SupportMode = "nl-en" | "nl-fa" | "nl-fa-en";
export type LearningCopy = { nl: string; en?: string; fa?: string };
const key = "taalstudio.language-support";
const changeEvent = "taalstudio:language-support";
let volatileMode: SupportMode = "nl-en";
const LanguageContext = createContext({ mode: "nl-en" as SupportMode, setMode: (() => {}) as (mode: SupportMode) => void, showEnglish: true, showPersian: false });

function readMode(): SupportMode {
  try {
    const value = localStorage.getItem(key);
    return value === "nl-fa" || value === "nl-fa-en" ? value : "nl-en";
  } catch { return volatileMode; }
}
function subscribe(listener: () => void) {
  window.addEventListener(changeEvent, listener);
  window.addEventListener("storage", listener);
  return () => { window.removeEventListener(changeEvent, listener); window.removeEventListener("storage", listener); };
}
export function LanguageProvider({ children }: { children: ReactNode }) {
  const mode = useSyncExternalStore(subscribe, readMode, () => "nl-en" as SupportMode);
  function setMode(value: SupportMode) {
    volatileMode = value;
    try { localStorage.setItem(key, value); } catch { /* Storage may be disabled. */ }
    window.dispatchEvent(new Event(changeEvent));
  }
  return <LanguageContext.Provider value={{ mode, setMode, showEnglish: mode !== "nl-fa", showPersian: mode !== "nl-en" }}>{children}</LanguageContext.Provider>;
}
export function useLanguageSupport() { return useContext(LanguageContext); }

/** Dutch remains the practice language. Support lines follow the learner's selected languages. */
export function LearningText({ text, className = "", supportOnly = false }: { text?: LearningCopy | null; className?: string; supportOnly?: boolean }) {
  const { showEnglish, showPersian } = useLanguageSupport();
  if (!text) return null;
  return <span className={`learning-copy ${className}`}>
    {!supportOnly && <span lang="nl" className="copy-dutch">{text.nl}</span>}
    {showEnglish && text.en && <> <span lang="en" className="copy-support">{text.en}</span></>}
    {showPersian && text.fa && <> <span lang="fa" dir="rtl" className="copy-support fa">{text.fa}</span></>}
  </span>;
}

export function LanguageSwitcher() {
  const { mode, setMode } = useLanguageSupport();
  return <div className="language-control">
    <label htmlFor="language-support">Taalhulp <span lang="en">/ language</span></label>
    <select id="language-support" value={mode} onChange={event => setMode(event.target.value as SupportMode)}>
      <option value="nl-en">Nederlands · English</option>
      <option value="nl-fa">Nederlands · فارسی</option>
      <option value="nl-fa-en">Nederlands · فارسی · English</option>
    </select>
  </div>;
}
