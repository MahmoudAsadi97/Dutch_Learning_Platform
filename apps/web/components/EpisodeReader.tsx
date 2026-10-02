"use client";

import Link from "next/link";
import { useCallback, useEffect, useRef, useState } from "react";
import { Icon } from "@/components/Icon";
import { useLanguageSupport } from "@/components/LanguageSupport";
import { PhraseAudio } from "@/components/PhraseAudio";
import { coverClass } from "@/components/TodayHome";
import { ApiError, newRequestId } from "@/lib/client/api";
import { useRecorder } from "@/lib/client/recorder";
import { stageLabels, stories, type Episode, type GlossaryItem } from "@/lib/client/stories";

function friendly(cause: unknown, fallback: string) {
  if (cause instanceof ApiError) {
    if (cause.status === 429) return "Je dagelijkse limiet voor het taalmodel is bereikt.";
    if (cause.status === 503) return "Het taalmodel is even niet bereikbaar. Je voortgang is bewaard.";
    if (cause.status === 409) return cause.detail;
  }
  return fallback;
}

export function EpisodeReader({ episodeId }: { episodeId: string }) {
  const [episode, setEpisode] = useState<Episode | null>(null);
  const [error, setError] = useState("");
  const [finished, setFinished] = useState(false);
  const [notice, setNotice] = useState("");
  const load = useCallback((signal?: AbortSignal) => stories.episode(episodeId, signal)
    .then(value => { setEpisode(value); setFinished(Boolean(value.read_at)); })
    .catch(cause => { if (!(cause instanceof DOMException && cause.name === "AbortError")) setError(cause instanceof ApiError && cause.status === 404 ? "Deze aflevering bestaat niet." : "De aflevering kon niet worden geladen."); }), [episodeId]);
  useEffect(() => { const controller = new AbortController(); void load(controller.signal); return () => controller.abort(); }, [load]);

  if (error) return <div className="error" role="alert">{error} <Link href="/verhalen">Naar de verhalen</Link></div>;
  if (!episode) return <div className="path-loading" role="status">Aflevering laden…</div>;
  if (episode.status !== "ready") return <div className="card"><p className="eyebrow">AFLEVERING {episode.number}</p><h1>{episode.status === "failed" ? "Deze aflevering is niet gelukt." : "Deze aflevering wordt nog geschreven."}</h1><p className="muted">Ga terug naar <Link href="/">Vandaag</Link> om de stand te zien.</p></div>;

  return <article className="episode-reader" data-testid="episode-reader">
    <header className="episode-header">
      <div className={coverClass(episode.number)} aria-hidden="true"><span className="cover-number">{episode.number}</span><span className="cover-town">De Lindestraat</span></div>
      <div>
        <p className="eyebrow">AFLEVERING {episode.number} · {stageLabels[episode.stage_id] ?? episode.stage_id} · {episode.word_count} WOORDEN</p>
        <h1>{episode.title}</h1>
        <p className="muted">Thema: {episode.theme}{episode.previous_choice && <> · Jouw vorige keuze: <em>{episode.previous_choice}</em></>}</p>
        <div className="episode-tools">
          <PhraseAudio text={episode.paragraphs.map(p => p.nl).join(" ")} label="de hele aflevering" />
          <span className="small-text muted">Luister naar de hele aflevering, of per alinea hieronder.</span>
        </div>
      </div>
    </header>

    <div className="episode-body">
      {episode.paragraphs.map((paragraph, index) => <Paragraph key={index} episodeId={episode.id} index={index} nl={paragraph.nl} en={paragraph.en} fa={paragraph.fa}
        onTranslated={fa => setEpisode(current => current ? { ...current, paragraphs: current.paragraphs.map((p, i) => i === index ? { ...p, fa } : p) } : current)}
        attempts={episode.read_aloud[String(index)]} onReadAloud={() => void load()} />)}
    </div>

    <Glossary episodeId={episode.id} items={episode.glossary} />

    {!finished && <div className="finish-row"><button className="button" data-testid="finish-reading" onClick={() => { setFinished(true); void stories.read(episode.id).then(setEpisode).catch(() => undefined); }}>Klaar met lezen<Icon name="arrow" size={18} /></button><span className="small-text muted">Daarna volgen een paar vragen en jouw keuze voor de volgende aflevering.</span></div>}

    {finished && <>
      <Questions episode={episode} onUpdate={setEpisode} />
      <section className="episode-choice" id="keuze" aria-labelledby="choice-title">
        <p className="eyebrow">JOUW KEUZE</p>
        <h2 id="choice-title">{episode.chosen_choice ? "De volgende aflevering wordt geschreven." : "Hoe gaat het verder?"}</h2>
        {!episode.chosen_choice && <p className="muted">De schrijver gebruikt jouw keuze voor de volgende aflevering.</p>}
        <div className="choice-buttons">{episode.choices.map(choice => <button key={choice.id} type="button" className={`choice-button ${episode.chosen_choice === choice.id ? "is-chosen" : ""}`} disabled={Boolean(episode.chosen_choice)} aria-pressed={episode.chosen_choice === choice.id}
          onClick={() => void stories.choose(episode.id, choice.id).then(setEpisode).catch(cause => setNotice(friendly(cause, "Je keuze kon niet worden bewaard.")))}>
          <span className="choice-letter" aria-hidden="true">{choice.id.toUpperCase()}</span><span lang="nl">{choice.label}</span></button>)}</div>
        {episode.chosen_choice && <p className="practice-complete" role="status">Je keuze is doorgegeven. <Link href="/">Terug naar Vandaag</Link> — daar verschijnt de nieuwe aflevering zodra ze klaar is.</p>}
        {notice && <p className="error" role="alert">{notice}</p>}
      </section>
      <footer className="episode-footer">
        <div className="rating" role="group" aria-label="Was deze aflevering goed?">
          <span className="small-text muted">Was dit een goede aflevering?</span>
          <button type="button" className={`linklike ${episode.rating === 1 ? "is-on" : ""}`} aria-pressed={episode.rating === 1} onClick={() => void stories.rate(episode.id, 1).then(setEpisode).catch(() => undefined)}>Ja</button>
          <button type="button" className={`linklike ${episode.rating === -1 ? "is-on" : ""}`} aria-pressed={episode.rating === -1} onClick={() => void stories.rate(episode.id, -1).then(setEpisode).catch(() => undefined)}>Niet echt</button>
        </div>
        {episode.topic_id && <Link className="stage-link" href={`/learn/${episode.stage_id}?skill=reading&topic=${episode.topic_id}`}>Oefen dit onderwerp in je leerpad<Icon name="arrow" size={17} /></Link>}
        <p className="small-text muted">Geschreven door het taalmodel ({episode.model || episode.provider}) en automatisch gecontroleerd{episode.warnings.length ? `; aandachtspunten: ${episode.warnings.length}` : ""}. Nog niet nagekeken door een taaldocent.</p>
      </footer>
    </>}
  </article>;
}

function Paragraph({ episodeId, index, nl, en, fa, onTranslated, attempts, onReadAloud }: {
  episodeId: string; index: number; nl: string; en: string; fa?: string; onTranslated: (fa: string) => void;
  attempts?: { matched_words: number; target_words: number; attempts: number }; onReadAloud: () => void;
}) {
  const { showEnglish, showPersian } = useLanguageSupport();
  const [translating, setTranslating] = useState(false);
  const [message, setMessage] = useState("");
  return <section className="episode-paragraph" data-testid="episode-paragraph">
    <p lang="nl" className="story-copy">{nl} <PhraseAudio text={nl} label={`alinea ${index + 1}`} /></p>
    {showEnglish && en && <p lang="en" className="copy-support">{en}</p>}
    {showPersian && (fa ? <p lang="fa" dir="rtl" className="copy-support fa">{fa}</p> : <button type="button" className="linklike" disabled={translating} onClick={() => { setTranslating(true); setMessage(""); void stories.translate(episodeId, index).then(result => onTranslated(result.fa)).catch(cause => setMessage(friendly(cause, "Vertalen lukte niet."))).finally(() => setTranslating(false)); }}>{translating ? "Vertalen…" : "Vertaal naar het Perzisch"}</button>)}
    <ReadAloud episodeId={episodeId} index={index} attempts={attempts} onDone={onReadAloud} />
    {message && <p className="error" role="alert">{message}</p>}
  </section>;
}

function ReadAloud({ episodeId, index, attempts, onDone }: { episodeId: string; index: number; attempts?: { matched_words: number; target_words: number; attempts: number }; onDone: () => void }) {
  const [busy, setBusy] = useState(false);
  const [result, setResult] = useState<{ matched: number; target: number; missed: string[]; points: number } | null>(null);
  const [error, setError] = useState("");
  const uploadRef = useRef<AbortController | null>(null);
  useEffect(() => () => uploadRef.current?.abort(), []);
  const recorder = useRecorder(recording => {
    uploadRef.current?.abort();
    const request = new AbortController(); uploadRef.current = request;
    setBusy(true); setError("");
    void stories.readAloud(episodeId, index, recording.blob, recording.fileName, request.signal)
      .then(value => { if (!request.signal.aborted) { setResult({ matched: value.matched_words, target: value.target_words, missed: value.missed, points: value.points }); onDone(); } })
      .catch(cause => { if (!request.signal.aborted) setError(friendly(cause, "We konden de opname niet verwerken. Probeer het in een rustige ruimte.")); })
      .finally(() => { if (uploadRef.current === request) setBusy(false); });
  });
  const recording = recorder.phase === "recording";
  if (recorder.phase === "unsupported") return null;
  return <div className={`read-aloud ${recording ? "is-recording" : ""}`}>
    <button type="button" className="button secondary" aria-pressed={recording} disabled={busy} onClick={() => { if (recording) recorder.stop(); else void recorder.start(); }}>
      <Icon name="mic" size={16} />{recording ? "Stop" : busy ? "Luisteren…" : result || attempts ? "Lees nog eens hardop" : "Lees hardop"}
    </button>
    {result && <span className="read-aloud-result" role="status">{result.matched} van {result.target} woorden herkend{result.points ? ` · +${result.points} punten` : ""}.{result.missed.length > 0 && <> Nog oefenen: <em lang="nl">{result.missed.slice(0, 8).join(", ")}</em></>}</span>}
    {!result && attempts && <span className="read-aloud-result muted">Eerder: {attempts.matched_words} van {attempts.target_words} woorden herkend.</span>}
    {(error || recorder.error) && <span className="error" role="alert">{error || "Geef je browser toegang tot de microfoon."}</span>}
  </div>;
}

function Glossary({ episodeId, items }: { episodeId: string; items: GlossaryItem[] }) {
  const { showEnglish, showPersian } = useLanguageSupport();
  const [saved, setSaved] = useState<Record<string, boolean>>({});
  const [message, setMessage] = useState("");
  if (!items.length) return null;
  return <section className="episode-glossary" aria-labelledby="glossary-title">
    <div className="section-heading"><div><p className="eyebrow">NIEUWE WOORDEN</p><h2 id="glossary-title">Bewaar wat je wilt onthouden</h2></div><span className="quiet-badge">{items.length} woorden</span></div>
    <ul className="glossary-list">{items.map(item => <li key={item.term} className="glossary-item">
      <div className="glossary-term"><strong lang="nl">{item.term}</strong><PhraseAudio text={item.term} /></div>
      <div className="glossary-meaning">{showEnglish && <span lang="en">{item.meaning_en}</span>}{showEnglish && showPersian && <span aria-hidden="true"> · </span>}{showPersian && <span lang="fa" dir="rtl" className="fa">{item.meaning_fa}</span>}{!showEnglish && !showPersian && <span lang="en">{item.meaning_en}</span>}</div>
      <p lang="nl" className="glossary-example muted">{item.example}</p>
      <button type="button" className="button secondary small" disabled={saved[item.term]} aria-pressed={saved[item.term] ?? false}
        onClick={() => void stories.saveWord(episodeId, item.term).then(result => { setSaved(current => ({ ...current, [item.term]: true })); setMessage(result.created ? `"${item.term}" staat in je woordenlijst en komt terug op het juiste moment.` : `"${item.term}" stond al in je woordenlijst.`); }).catch(cause => setMessage(friendly(cause, "Bewaren lukte niet.")))}>
        {saved[item.term] ? "Bewaard" : "Bewaar"}</button>
    </li>)}</ul>
    {message && <p className="practice-hint" role="status">{message}</p>}
  </section>;
}

function Questions({ episode, onUpdate }: { episode: Episode; onUpdate: (episode: Episode) => void }) {
  const [answers, setAnswers] = useState<Record<string, number>>({});
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState("");
  const requestId = useRef(newRequestId());
  const complete = episode.questions.every(question => answers[String(question.index)] !== undefined);
  const correct = episode.answered ? episode.questions.filter(question => question.correct).length : 0;
  return <section className="episode-questions" aria-labelledby="questions-title">
    <div className="section-heading"><div><p className="eyebrow">BEGRIP</p><h2 id="questions-title">{episode.answered ? `${correct} van ${episode.questions.length} juist` : `${episode.questions.length === 2 ? "Twee" : "Drie"} vragen over het verhaal`}</h2></div></div>
    <form onSubmit={event => { event.preventDefault(); if (!complete || busy) return; setBusy(true); setMessage(""); void stories.answer(episode.id, answers, requestId.current).then(onUpdate).catch(cause => setMessage(friendly(cause, "Je antwoorden konden niet worden bewaard."))).finally(() => setBusy(false)); }}>
      <ol className="question-list">{episode.questions.map(question => <li key={question.index} className={`episode-question ${episode.answered ? (question.correct ? "is-correct" : "is-wrong") : ""}`}>
        <p lang="nl" className="question-prompt">{question.prompt}</p>
        <div className="answer-options" role="radiogroup" aria-label={question.prompt}>{question.options.map((option, optionIndex) => <label key={optionIndex} className={episode.answered && question.answer_index === optionIndex ? "is-answer" : ""}>
          <input type="radio" name={`question-${question.index}`} value={optionIndex} disabled={episode.answered} checked={(episode.answered ? question.chosen : answers[String(question.index)]) === optionIndex} onChange={() => setAnswers(current => ({ ...current, [String(question.index)]: optionIndex }))} />
          <span lang="nl">{option}</span></label>)}</div>
        {episode.answered && question.evidence && <p className="question-evidence"><Icon name={question.correct ? "check" : "help"} size={15} /> <span lang="nl">In het verhaal: “{question.evidence}”</span></p>}
      </li>)}</ol>
      {!episode.answered && <button className="button" type="submit" disabled={!complete || busy}>Controleer mijn antwoorden</button>}
      {message && <p className="error" role="alert">{message}</p>}
    </form>
  </section>;
}
