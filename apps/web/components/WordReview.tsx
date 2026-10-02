"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import { Icon } from "@/components/Icon";
import { useLanguageSupport } from "@/components/LanguageSupport";
import { PhraseAudio } from "@/components/PhraseAudio";
import { ApiError } from "@/lib/client/api";
import { words, type Grade, type WordItem, type WordStats } from "@/lib/client/stories";

const gradeCopy: { grade: Grade; label: string; hint: string }[] = [
  { grade: "again", label: "Nog eens", hint: "straks opnieuw" },
  { grade: "hard", label: "Moeilijk", hint: "kort interval" },
  { grade: "good", label: "Goed", hint: "normaal interval" },
  { grade: "easy", label: "Makkelijk", hint: "langer interval" },
];

export function WordReview() {
  const [queue, setQueue] = useState<WordItem[] | null>(null);
  const [stats, setStats] = useState<WordStats | null>(null);
  const [revealed, setRevealed] = useState(false);
  const [done, setDone] = useState(0);
  const [error, setError] = useState("");
  const [allWords, setAllWords] = useState<WordItem[] | null>(null);
  const [draft, setDraft] = useState({ term: "", meaning_en: "", meaning_fa: "" });
  const [notice, setNotice] = useState("");
  const { showEnglish, showPersian } = useLanguageSupport();
  const load = useCallback((signal?: AbortSignal) => words.due(20, signal)
    .then(due => { setQueue(due.items); setStats(due); setRevealed(false); })
    .catch(cause => { if (!(cause instanceof DOMException && cause.name === "AbortError")) setError("Je woorden konden niet worden geladen."); }), []);
  useEffect(() => { const controller = new AbortController(); void load(controller.signal); return () => controller.abort(); }, [load]);

  async function grade(item: WordItem, value: Grade) {
    try {
      const updated = await words.review(item.id, value);
      setDone(count => count + 1);
      setQueue(current => {
        const rest = (current ?? []).filter(entry => entry.id !== item.id);
        return updated.due ? [...rest, updated] : rest; // "again" returns the card to the end of the session
      });
      setStats(current => current ? { ...current, due_count: Math.max(0, current.due_count - (updated.due ? 0 : 1)) } : current);
      setRevealed(false);
    } catch (cause) { setError(cause instanceof ApiError ? cause.detail : "Je antwoord kon niet worden bewaard."); }
  }
  async function toggleAll() {
    if (allWords) { setAllWords(null); return; }
    try { setAllWords((await words.all()).items); } catch { setError("De lijst kon niet worden geladen."); }
  }
  async function add() {
    if (!draft.term.trim()) return;
    try { const result = await words.save(draft.term.trim(), draft.meaning_en.trim(), draft.meaning_fa.trim()); setNotice(result.created ? `"${result.item.term}" is bewaard.` : `"${result.item.term}" stond er al.`); setDraft({ term: "", meaning_en: "", meaning_fa: "" }); await load(); if (allWords) setAllWords((await words.all()).items); }
    catch { setNotice("Bewaren lukte niet."); }
  }

  if (error) return <div className="error" role="alert">{error} <button className="linklike" onClick={() => { setError(""); void load(); }}>Opnieuw proberen</button></div>;
  if (!queue || !stats) return <div className="path-loading" role="status">Woorden laden…</div>;
  const current = queue[0];
  return <div className="word-review" data-testid="word-review">
    <header className="path-heading">
      <div><p className="eyebrow">WOORDEN</p><h1>{current ? "Herhaal wat je bewaarde." : done ? "Klaar voor vandaag." : "Niets te herhalen."}</h1><p className="muted">{stats.total} woorden bewaard · {stats.learned_count} stevig onthouden · {stats.due_count} vandaag te herhalen{done ? ` · ${done} gedaan` : ""}</p></div>
      <Link className="button secondary" href="/">Vandaag<Icon name="arrow" size={16} /></Link>
    </header>

    {current ? <section className="flashcard" aria-live="polite">
      <p className="eyebrow">{queue.length} {queue.length === 1 ? "KAART" : "KAARTEN"} IN DEZE RONDE</p>
      <div className="flashcard-face">
        <p className="flashcard-term" lang="nl">{current.term} <PhraseAudio text={current.term} /></p>
        {revealed ? <div className="flashcard-back">
          <p className="flashcard-meaning">{showEnglish && <span lang="en">{current.meaning_en}</span>}{showEnglish && showPersian && current.meaning_fa && <span aria-hidden="true"> · </span>}{showPersian && <span lang="fa" dir="rtl" className="fa">{current.meaning_fa}</span>}{!showEnglish && !showPersian && <span lang="en">{current.meaning_en}</span>}</p>
          {current.example && <p lang="nl" className="muted">{current.example}</p>}
          <div className="grade-buttons" role="group" aria-label="Hoe goed kende je dit woord?">{gradeCopy.map(option => <button key={option.grade} type="button" className={`grade-button grade-${option.grade}`} onClick={() => void grade(current, option.grade)}><strong>{option.label}</strong><small>{option.hint}</small></button>)}</div>
        </div> : <button className="button" type="button" data-testid="reveal-word" onClick={() => setRevealed(true)}>Toon de betekenis</button>}
      </div>
      <p className="small-text muted">Het interval groeit als je een woord goed kent en krimpt als je het vergeet. Het zegt niets over je niveau, alleen over wanneer je dit woord weer ziet.</p>
    </section> : <section className="card review-done">
      <p>{done ? "Alle kaarten van vandaag zijn gedaan. Lees een aflevering en bewaar nieuwe woorden; ze komen hier terug." : "Bewaar woorden uit de verhalen met de knop Bewaar, of voeg hieronder zelf een woord toe."}</p>
      <Link className="button" href="/verhalen">Naar de verhalen<Icon name="arrow" size={16} /></Link>
    </section>}

    <section className="wish-card inline" aria-labelledby="add-word">
      <h2 id="add-word">Zelf een woord toevoegen</h2>
      <form className="word-form" onSubmit={event => { event.preventDefault(); void add(); }}>
        <label>Woord<input lang="nl" value={draft.term} onChange={event => setDraft({ ...draft, term: event.target.value })} maxLength={120} placeholder="de buurvrouw" /></label>
        <label>Engels<input lang="en" value={draft.meaning_en} onChange={event => setDraft({ ...draft, meaning_en: event.target.value })} maxLength={300} placeholder="the neighbour" /></label>
        <label>Perzisch<input lang="fa" dir="rtl" value={draft.meaning_fa} onChange={event => setDraft({ ...draft, meaning_fa: event.target.value })} maxLength={300} placeholder="همسایه" /></label>
        <button className="button secondary" type="submit" disabled={!draft.term.trim()}>Bewaar</button>
      </form>
      {notice && <p className="practice-hint" role="status">{notice}</p>}
    </section>

    <button type="button" className="linklike" onClick={() => void toggleAll()}>{allWords ? "Verberg de lijst" : "Toon al mijn woorden"}</button>
    {allWords && <ul className="word-list">{allWords.map(item => <li key={item.id}>
      <strong lang="nl">{item.term}</strong> <span className="muted">{item.meaning_en}{item.meaning_fa ? ` · ${item.meaning_fa}` : ""}</span>
      <span className="small-text muted">{item.learned ? "stevig" : item.due ? "nu te herhalen" : `terug over ${item.interval_days} ${item.interval_days === 1 ? "dag" : "dagen"}`}</span>
      <button type="button" className="linklike" aria-label={`Verwijder ${item.term}`} onClick={() => void words.remove(item.id).then(() => Promise.all([load(), words.all().then(all => setAllWords(all.items))])).catch(() => setNotice("Verwijderen lukte niet."))}>Verwijder</button>
    </li>)}</ul>}
  </div>;
}
