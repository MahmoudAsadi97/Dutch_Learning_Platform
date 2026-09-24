"use client";

import { useEffect, useRef, useState, useSyncExternalStore } from "react";
import { LearningText, type LearningCopy } from "@/components/LanguageSupport";
import { PhraseAudio } from "@/components/PhraseAudio";
import { VocabularyRecall } from "@/components/VocabularyRecall";
import { CurriculumQuestions } from "@/components/CurriculumControls";
import { dutchSentences } from "@/lib/client/sentences";
import { apiJson, ApiError } from "@/lib/client/api";
import { friendlyError, type CurriculumQuestion } from "@/lib/client/curriculum";

type Word = {id: string; term: string; topic: LearningCopy; meaning: LearningCopy; example: LearningCopy};
type StorySummary = {id: string; title: LearningCopy; topic: LearningCopy; preview: LearningCopy; word_count: number; paragraph_count: number};
type Story = StorySummary & {paragraphs: LearningCopy[]; vocabulary: Word[]; question: CurriculumQuestion};
type Overview = {stage_id: string; learner_key: string; vocabulary_count: number; story_count: number; topics: {key: string; label: LearningCopy; vocabulary_count: number; story_count: number}[]};
type Page<T> = {items: T[]; total: number; offset: number; limit: number};

/** Sentence replay remains separate from translations and from final tests. */
export function SpokenPassage({ text }: {text: LearningCopy}) {
  const paragraphs = text.nl.split(/\n\s*\n/).filter(Boolean);
  return <div className="spoken-passage"><div lang="nl">{paragraphs.map((paragraph, i) => <p key={i}>{dutchSentences(paragraph).map((sentence, j) => <span className="spoken-sentence" key={j}><span>{sentence.trim()} </span><PhraseAudio text={sentence.trim()}/>{" "}</span>)}</p>)}</div><LearningText text={text} supportOnly/></div>;
}

function subscribeReads(listener: () => void) {
  window.addEventListener("storage", listener); window.addEventListener("taalstudio:reading", listener);
  return () => {window.removeEventListener("storage", listener); window.removeEventListener("taalstudio:reading", listener);};
}
function readSnapshot(key: string) {try {return localStorage.getItem(key) ?? "[]";} catch {return "[]";}}
function readIds(value: string): string[] {try {const saved = JSON.parse(value); return Array.isArray(saved) ? saved.filter(x => typeof x === "string").slice(0, 500) : [];} catch {return [];}}

function LibraryError({ retry }: {retry: () => void}) {
  return <p role="alert" className="error">De bibliotheek kon niet worden geladen. <button className="linklike" onClick={retry}>Opnieuw proberen</button></p>;
}

function useOverview(stageId: string) {
  const [overview, setOverview] = useState<Overview | null>(null);
  const [failed, setFailed] = useState(""); const [revision, setRevision] = useState(0);
  useEffect(() => {
    const controller = new AbortController();
    apiJson<Overview>(`library/${stageId}`, {signal: controller.signal}).then(value => {if (!controller.signal.aborted) {setOverview(value); setFailed("");}}).catch(() => {if (!controller.signal.aborted) setFailed(stageId);});
    return () => controller.abort();
  }, [stageId, revision]);
  return {overview: overview?.stage_id === stageId ? overview : null, failed: failed === stageId, retryOverview: () => setRevision(v => v + 1)};
}

function LibraryFilters({kind, overview, query, topic, onQuery, onTopic}: {kind: "words" | "stories"; overview: Overview | null; query: string; topic: string; onQuery: (v: string) => void; onTopic: (v: string) => void}) {
  return <div className="library-filters"><div className="library-filter"><label htmlFor={`${kind}-search`}>Zoeken</label><input type="search" id={`${kind}-search`} value={query} maxLength={120} onChange={e => onQuery(e.target.value)} placeholder={kind === "words" ? "Woord, betekenis of voorbeeld…" : "Titel of onderwerp…"}/></div><div className="library-filter"><label htmlFor={`${kind}-topic`}>Onderwerp</label><select id={`${kind}-topic`} value={topic} onChange={e => onTopic(e.target.value)}><option value="">Alle onderwerpen</option>{overview?.topics.filter(t => kind === "words" ? t.vocabulary_count : t.story_count).map(t => <option key={t.key} value={t.key}>{t.label.nl}</option>)}</select></div></div>;
}

function Pager({offset, limit, total, onChange}: {offset: number; limit: number; total: number; onChange: (value: number) => void}) {
  return <nav className="library-pagination" aria-label="Pagina’s in de bibliotheek"><button className="button secondary" disabled={offset === 0} onClick={() => onChange(Math.max(0, offset - limit))}>Vorige</button><span role="status">{total ? `${offset + 1}–${Math.min(offset + limit, total)} van ${total}` : "Geen resultaten"}</span><button className="button secondary" disabled={offset + limit >= total} onClick={() => onChange(offset + limit)}>Volgende</button></nav>;
}

export function WordLibrary({stageId}: {stageId: string}) {
  const {overview, failed: overviewFailed, retryOverview} = useOverview(stageId);
  const [query, setQuery] = useState(""); const [topic, setTopic] = useState(""); const [offset, setOffset] = useState(0);
  const [result, setResult] = useState<{key: string; page: Page<Word>} | null>(null); const [error, setError] = useState(false); const [retry, setRetry] = useState(0);
  const [revealed, setRevealed] = useState<Record<string, boolean>>({});
  const key = JSON.stringify([stageId, query, topic, offset, retry]);
  const data = result?.key === key ? result.page : null;
  useEffect(() => {
    const controller = new AbortController();
    const timer = window.setTimeout(() => {
      setResult(null); setError(false);
      const params = new URLSearchParams({q: query, topic, offset: String(offset), limit: "20"});
      apiJson<Page<Word>>(`library/${stageId}/vocabulary?${params}`, {signal: controller.signal}).then(value => { if (!controller.signal.aborted) setResult({key, page: value}); }).catch(() => {if (!controller.signal.aborted) setError(true);});
    }, query ? 200 : 0);
    return () => {clearTimeout(timer); controller.abort();};
  }, [stageId, query, topic, offset, retry, key]);
  return <section className="word-library" aria-label="Woordkaarten">
    <div className="library-intro"><p className="eyebrow">LUISTER · HERINNER · GEBRUIK</p><h3>{overview ? `${overview.vocabulary_count} woorden en uitdrukkingen` : "Je woordkaarten"}</h3><p><LearningText text={{nl: "Kies een onderwerp. Leer vijf woorden per ronde, luister naar de uitspraak en gebruik ze in je eigen zin. Je hoeft de hele bank niet in één keer te leren.", en: "Choose a topic. Practise five words at a time, listen and use them in your own sentence. You do not need to learn the entire bank at once.", fa: "موضوعی انتخاب کن. هر بار پنج واژه تمرین کن، تلفظ را بشنو و با آن‌ها جمله بساز. لازم نیست همهٔ واژه‌ها را یک‌جا یاد بگیری."}}/></p></div>
    {overviewFailed && <LibraryError retry={retryOverview}/>}
    <LibraryFilters kind="words" overview={overview} query={query} topic={topic} onQuery={value => {setQuery(value); setOffset(0);}} onTopic={value => {setTopic(value); setOffset(0);}}/>
    {error ? <LibraryError retry={() => setRetry(v => v + 1)}/> : !data ? <p role="status">Woordkaarten laden…</p> : <>
      <VocabularyRecall key={key} words={data.items}/>
      {!data.total && <p>Geen woorden gevonden. Probeer een korter zoekwoord of een ander onderwerp.</p>}
      <div className="vocabulary-cards">{data.items.map(word => <article className={`vocabulary-card ${revealed[word.id] ? "revealed" : ""}`} key={word.id}><span className="eyebrow">{word.topic.nl}</span><div className="word-card-heading"><h3 lang="nl">{word.term}</h3><PhraseAudio text={word.term} label={`Luister naar ${word.term}`}/></div><button className="word-reveal" aria-expanded={!!revealed[word.id]} onClick={() => setRevealed(v => ({...v, [word.id]: !v[word.id]}))}>{revealed[word.id] ? "Verberg de betekenis" : "Toon de betekenis"}</button>{revealed[word.id] && <div className="word-answer"><p><LearningText text={word.meaning}/></p><div className="word-example"><LearningText text={word.example}/><PhraseAudio text={word.example.nl} label={`Luister naar het voorbeeld bij ${word.term}`}/></div></div>}</article>)}</div>
      <Pager offset={offset} limit={20} total={data.total} onChange={value => {setOffset(value); setRevealed({});}}/>
    </>}
  </section>;
}

export function StoryTime({stageId}: {stageId: string}) {
  const {overview, failed: overviewFailed, retryOverview} = useOverview(stageId);
  const [query, setQuery] = useState(""); const [topic, setTopic] = useState(""); const [offset, setOffset] = useState(0);
  const [result, setResult] = useState<{key: string; page: Page<StorySummary>} | null>(null); const [error, setError] = useState(false); const [retry, setRetry] = useState(0);
  const key = JSON.stringify([stageId, query, topic, offset, retry]);
  const data = result?.key === key ? result.page : null;
  const [selected, setSelected] = useState(""); const [story, setStory] = useState<Story | null>(null); const [storyError, setStoryError] = useState("");
  const [answers, setAnswers] = useState<Record<string, number>>({}); const [checked, setChecked] = useState(false); const [showSupport, setShowSupport] = useState(false);
  const [readError, setReadError] = useState(false);
  const readKey = `taalstudio.stories.${overview?.learner_key ?? "pending"}.${stageId}`;
  const readRaw = useSyncExternalStore(subscribeReads, () => readSnapshot(readKey), () => "[]");
  const read = readIds(readRaw);
  const titleRef = useRef<HTMLHeadingElement | null>(null);
  useEffect(() => {
    const controller = new AbortController();
    const timer = window.setTimeout(() => {
      setResult(null); setError(false);
      const params = new URLSearchParams({q: query, topic, offset: String(offset), limit: "12"});
      apiJson<Page<StorySummary>>(`library/${stageId}/stories?${params}`, {signal: controller.signal}).then(value => {if (!controller.signal.aborted) setResult({key, page: value});}).catch(() => {if (!controller.signal.aborted) setError(true);});
    }, query ? 200 : 0);
    return () => {clearTimeout(timer); controller.abort();};
  }, [stageId, query, topic, offset, retry, key]);
  useEffect(() => {
    if (!selected) return;
    const controller = new AbortController();
    apiJson<Story>(`library/${stageId}/stories/${encodeURIComponent(selected)}`, {signal: controller.signal}).then(value => {if (!controller.signal.aborted) {setStory(value); setStoryError("");}}).catch(cause => {if (!controller.signal.aborted) setStoryError(friendlyError(cause instanceof ApiError ? cause.status : undefined));});
    return () => controller.abort();
  }, [stageId, selected, retry]);
  useEffect(() => { if (story) titleRef.current?.focus(); }, [story]);
  function markRead() {
    if (!overview || !story) return;
    const values = [...new Set([...read, story.id])].slice(-500);
    try {localStorage.setItem(`taalstudio.stories.${overview.learner_key}.${stageId}`, JSON.stringify(values)); window.dispatchEvent(new Event("taalstudio:reading")); setReadError(false);} catch {setReadError(true);}
  }
  if (selected) return <section className="story-reader"><button className="linklike story-back" onClick={() => {setSelected(""); setStory(null);}}>← Alle verhalen</button>{storyError ? <LibraryError retry={() => setRetry(v => v + 1)}/> : !story ? <p role="status">Verhaal laden…</p> : <>
    <header><p className="eyebrow">STORY TIME · {story.topic.nl}</p><h3 ref={titleRef} tabIndex={-1}><LearningText text={story.title}/></h3><button className="button secondary" aria-pressed={showSupport} onClick={() => setShowSupport(v => !v)}>{showSupport ? "Vertaling verbergen" : "Vertaling tonen"}</button></header>
    <article className="story-paper" aria-label="Leesverhaal">{story.paragraphs.map((paragraph, i) => <div className="story-paragraph" key={i}><SpokenPassage text={showSupport ? paragraph : {nl: paragraph.nl}}/></div>)}</article>
    <section className="story-word-strip"><h4>Woorden uit dit verhaal</h4><div>{story.vocabulary.map(word => <details key={word.id}><summary>{word.term}</summary><PhraseAudio text={word.term}/><p><LearningText text={word.meaning}/></p><LearningText text={word.example}/><PhraseAudio text={word.example.nl}/></details>)}</div></section>
    <section className="story-understanding"><h4>Even nadenken</h4><CurriculumQuestions questions={[story.question]} answers={answers} onAnswer={(id, index) => {setAnswers({[id]: index}); setChecked(false);}} checked={checked}/><button className="button secondary" disabled={answers[story.question.id] === undefined} onClick={() => setChecked(true)}>Controleer mijn begrip</button><p><LearningText text={{nl: "Vertel het verhaal daarna in je eigen woorden. Wat zou jij doen?", en: "Then retell the story in your own words. What would you do?", fa: "سپس داستان را با کلمات خودت تعریف کن. تو چه کار می‌کردی؟"}}/></p><button className="button" onClick={markRead} disabled={read.includes(story.id)}>{read.includes(story.id) ? "Gelezen" : "Markeer als gelezen"}</button>{readError && <p role="status">Je browser kon het leesmerk niet bewaren. Je kunt verder lezen.</p>}<p className="small-text muted">Je leeslijst blijft in deze browser. Lezen telt niet als een geslaagde eindtoets.</p></section>
  </>}</section>;
  return <section className="story-time"><header className="library-intro"><p className="eyebrow">STORY TIME</p><h3>Kleine verhalen, een grotere wereld.</h3><p><LearningText text={{nl: "Ontmoet mensen, ontdek een onverwachte wending en herken je woorden in een verhaal. Lees, luister en vertel het na.", en: "Meet people, discover a small twist and recognise your vocabulary in context. Read, listen and retell.", fa: "با آدم‌ها آشنا شو، اتفاقی غیرمنتظره کشف کن و واژه‌هایت را در داستان ببین. بخوان، گوش بده و بازگو کن."}}/></p>{overview && <p className="library-count">{overview.story_count} verhalen · {read.length} gemarkeerd als gelezen</p>}</header>
    {overviewFailed && <LibraryError retry={retryOverview}/>}
    <LibraryFilters kind="stories" overview={overview} query={query} topic={topic} onQuery={value => {setQuery(value); setOffset(0);}} onTopic={value => {setTopic(value); setOffset(0);}}/>
    {error ? <LibraryError retry={() => setRetry(v => v + 1)}/> : !data ? <p role="status">Verhalen laden…</p> : <><div className="story-grid">{data.items.map((item, i) => <article className="story-tile" key={item.id}><div className={`story-cover cover-${i % 4}`} aria-hidden="true"><span>{String(offset + i + 1).padStart(2, "0")}</span><span>Verhaal</span></div><div className="story-tile-copy"><span className="eyebrow">{item.topic.nl}</span><h4><LearningText text={item.title}/></h4><p className="story-excerpt" lang="nl">{item.preview.nl}</p><div className="story-tile-meta"><span>{item.word_count} woorden</span>{read.includes(item.id) && <span>Gelezen</span>}</div><button className="button secondary" onClick={() => {setStory(null); setStoryError(""); setAnswers({}); setChecked(false); setShowSupport(false); setReadError(false); setSelected(item.id);}} aria-label={`Lees ${item.title.nl}`}>Lees het verhaal →</button></div></article>)}</div>{!data.total && <p>Geen verhalen gevonden. Kies een ander onderwerp.</p>}<Pager offset={offset} limit={12} total={data.total} onChange={setOffset}/></>}
  </section>;
}
