"use client";

import Link from "next/link";
import { useCallback, useEffect, useRef, useState } from "react";
import { Icon } from "@/components/Icon";
import { useLanguageSupport } from "@/components/LanguageSupport";
import { PhraseAudio } from "@/components/PhraseAudio";
import { failureCopy } from "@/components/VideoLibrary";
import { ApiError, newRequestId } from "@/lib/client/api";
import { stageLabels, type GlossaryItem } from "@/lib/client/stories";
import { clock, sceneAt, videos, type Video } from "@/lib/client/videos";

function friendly(cause: unknown, fallback: string) {
  if (cause instanceof ApiError) {
    if (cause.status === 429) return "Je dagelijkse limiet is bereikt.";
    if (cause.status === 503) return "De dienst is even niet bereikbaar. Je voortgang is bewaard.";
    if (cause.status === 409) return cause.detail;
  }
  return fallback;
}

export function VideoPlayer({ videoId }: { videoId: string }) {
  const [video, setVideo] = useState<Video | null>(null);
  const [error, setError] = useState("");
  const [time, setTime] = useState(0);
  const [finished, setFinished] = useState(false);
  const [showSubtitles, setShowSubtitles] = useState(true);
  const [notice, setNotice] = useState("");
  const player = useRef<HTMLVideoElement>(null);
  const load = useCallback((signal?: AbortSignal) => videos.get(videoId, signal)
    .then(value => { setVideo(value); setFinished(Boolean(value.watched_at)); })
    .catch(cause => { if (!(cause instanceof DOMException && cause.name === "AbortError")) setError(cause instanceof ApiError && cause.status === 404 ? "Deze video bestaat niet." : "De video kon niet worden geladen."); }), [videoId]);
  useEffect(() => { const controller = new AbortController(); void load(controller.signal); return () => controller.abort(); }, [load]);
  useEffect(() => {
    const element = player.current;
    if (!element) return;
    for (const track of Array.from(element.textTracks)) track.mode = showSubtitles ? "showing" : "hidden";
  }, [showSubtitles, video]);

  if (error) return <div className="error" role="alert">{error} <Link href="/videos">Naar de video&apos;s</Link></div>;
  if (!video) return <div className="path-loading" role="status">Video laden…</div>;
  if (video.status !== "ready") return <div className="card">
    <p className="eyebrow">{video.kind_label.toUpperCase()} · {stageLabels[video.stage_id] ?? video.stage_id}</p>
    <h1>{video.status === "failed" ? "Deze video is niet gelukt." : "Deze video wordt nog gemaakt."}</h1>
    <p className="muted">{video.status === "failed" ? failureCopy(video) : "Het script wordt geschreven en de video opgenomen. Dat duurt een paar minuten."} Ga terug naar <Link href="/videos">de video&apos;s</Link> om de stand te zien.</p>
  </div>;

  const activeScene = sceneAt(video.cues, time);
  function seekTo(scene: number) {
    const cue = video?.cues.find(item => item.scene === scene);
    const element = player.current;
    if (!cue || !element) return;
    element.currentTime = cue.start;
    setTime(cue.start);
    void element.play().catch(() => undefined);
  }
  const currentId = video.id;
  function markWatched() {
    if (finished) return;
    setFinished(true);
    void videos.watched(currentId).then(setVideo).catch(cause => setNotice(friendly(cause, "Je kijkbeurt kon niet worden bewaard.")));
  }

  return <article className="video-lesson" data-testid="video-lesson">
    <header className="video-lesson-header">
      <p className="eyebrow">{video.kind_label.toUpperCase()} · {stageLabels[video.stage_id] ?? video.stage_id} · {clock(video.duration_seconds)} · {video.word_count} WOORDEN</p>
      <h1>{video.title}</h1>
      <p className="muted">Onderwerp: {video.topic}</p>
    </header>

    <div className="video-stage">
      <video ref={player} controls playsInline preload="metadata" className="video-element" data-testid="video-element"
        onTimeUpdate={event => setTime(event.currentTarget.currentTime)} onSeeked={event => setTime(event.currentTarget.currentTime)} onEnded={markWatched}>
        <source src={`/api/${video.media_url}`} />
        <track kind="subtitles" src={`/api/${video.subtitles_url}`} srcLang="nl" label="Nederlands" default />
        Je browser kan deze video niet afspelen.
      </video>
      <div className="video-controls-row">
        <label className="toggle"><input type="checkbox" checked={showSubtitles} onChange={event => setShowSubtitles(event.target.checked)} /> Ondertitels</label>
        <span className="small-text muted">{video.presenter === "avatar" ? "Virtuele presentator en synthetische stem" : "Scènekaarten en synthetische stem"} ({video.voice || video.renderer}). Geen echte persoon.</span>
      </div>
    </div>

    <Transcript video={video} activeScene={activeScene} onSeek={seekTo} />

    <Glossary videoId={video.id} items={video.glossary} />

    {!finished && <div className="finish-row"><button className="button" data-testid="finish-watching" onClick={markWatched}>Klaar met kijken<Icon name="arrow" size={18} /></button><span className="small-text muted">Daarna volgen een paar vragen over de video.</span></div>}

    {finished && <>
      <Questions video={video} onUpdate={setVideo} />
      <footer className="episode-footer">
        <div className="rating" role="group" aria-label="Was deze video goed?">
          <span className="small-text muted">Was dit een goede video?</span>
          <button type="button" className={`linklike ${video.rating === 1 ? "is-on" : ""}`} aria-pressed={video.rating === 1} onClick={() => void videos.rate(video.id, 1).then(setVideo).catch(() => undefined)}>Ja</button>
          <button type="button" className={`linklike ${video.rating === -1 ? "is-on" : ""}`} aria-pressed={video.rating === -1} onClick={() => void videos.rate(video.id, -1).then(setVideo).catch(() => undefined)}>Niet echt</button>
        </div>
        <Link className="stage-link" href="/videos">Vraag nog een video<Icon name="arrow" size={17} /></Link>
        <p className="small-text muted">Script van het taalmodel ({video.model || video.provider}), automatisch gecontroleerd{video.warnings.length ? `; aandachtspunten: ${video.warnings.length}` : ""}. Nog niet nagekeken door een taaldocent.</p>
        {notice && <p className="error" role="alert">{notice}</p>}
      </footer>
    </>}
    {!finished && notice && <p className="error" role="alert">{notice}</p>}
  </article>;
}

function Transcript({ video, activeScene, onSeek }: { video: Video; activeScene: number; onSeek: (scene: number) => void }) {
  const { showEnglish, showPersian } = useLanguageSupport();
  return <section className="video-transcript" aria-labelledby="transcript-title">
    <div className="section-heading"><div><p className="eyebrow">TRANSCRIPT</p><h2 id="transcript-title">Lees mee</h2></div><span className="small-text muted">Klik op een scène om daar te kijken.</span></div>
    <ol className="scene-list">{video.scenes.map((scene, index) => <li key={index} className={`scene ${index === activeScene ? "is-active" : ""}`} data-testid="video-scene" aria-current={index === activeScene ? "true" : undefined}>
      <button type="button" className="scene-jump" onClick={() => onSeek(index)} aria-label={`Ga naar scène ${index + 1}`}><span className="scene-keyword" lang="nl">{scene.keyword}</span></button>
      <div className="scene-text">
        <p lang="nl" className="story-copy">{scene.nl} <PhraseAudio text={scene.nl} label={`scène ${index + 1}`} /></p>
        {showEnglish && scene.en && <p lang="en" className="copy-support">{scene.en}</p>}
        {showPersian && scene.fa && <p lang="fa" dir="rtl" className="copy-support fa">{scene.fa}</p>}
      </div>
    </li>)}</ol>
  </section>;
}

function Glossary({ videoId, items }: { videoId: string; items: GlossaryItem[] }) {
  const { showEnglish, showPersian } = useLanguageSupport();
  const [saved, setSaved] = useState<Record<string, boolean>>({});
  const [message, setMessage] = useState("");
  if (!items.length) return null;
  return <section className="episode-glossary" aria-labelledby="video-glossary-title">
    <div className="section-heading"><div><p className="eyebrow">NIEUWE WOORDEN</p><h2 id="video-glossary-title">Bewaar wat je wilt onthouden</h2></div><span className="quiet-badge">{items.length} woorden</span></div>
    <ul className="glossary-list">{items.map(item => <li key={item.term} className="glossary-item">
      <div className="glossary-term"><strong lang="nl">{item.term}</strong><PhraseAudio text={item.term} /></div>
      <div className="glossary-meaning">{showEnglish && <span lang="en">{item.meaning_en}</span>}{showEnglish && showPersian && <span aria-hidden="true"> · </span>}{showPersian && <span lang="fa" dir="rtl" className="fa">{item.meaning_fa}</span>}{!showEnglish && !showPersian && <span lang="en">{item.meaning_en}</span>}</div>
      <p lang="nl" className="glossary-example muted">{item.example}</p>
      <button type="button" className="button secondary small" disabled={saved[item.term]} aria-pressed={saved[item.term] ?? false}
        onClick={() => void videos.saveWord(videoId, item.term).then(result => { setSaved(current => ({ ...current, [item.term]: true })); setMessage(result.created ? `"${item.term}" staat in je woordenlijst en komt terug op het juiste moment.` : `"${item.term}" stond al in je woordenlijst.`); }).catch(cause => setMessage(friendly(cause, "Bewaren lukte niet.")))}>
        {saved[item.term] ? "Bewaard" : "Bewaar"}</button>
    </li>)}</ul>
    {message && <p className="practice-hint" role="status">{message}</p>}
  </section>;
}

function Questions({ video, onUpdate }: { video: Video; onUpdate: (video: Video) => void }) {
  const [answers, setAnswers] = useState<Record<string, number>>({});
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState("");
  const requestId = useRef(newRequestId());
  const complete = video.questions.every(question => answers[String(question.index)] !== undefined);
  const correct = video.answered ? video.questions.filter(question => question.correct).length : 0;
  return <section className="episode-questions" aria-labelledby="video-questions-title">
    <div className="section-heading"><div><p className="eyebrow">BEGRIP</p><h2 id="video-questions-title">{video.answered ? `${correct} van ${video.questions.length} juist` : `${video.questions.length === 2 ? "Twee" : "Drie"} vragen over de video`}</h2></div></div>
    <form onSubmit={event => { event.preventDefault(); if (!complete || busy) return; setBusy(true); setMessage(""); void videos.answer(video.id, answers, requestId.current).then(onUpdate).catch(cause => setMessage(friendly(cause, "Je antwoorden konden niet worden bewaard."))).finally(() => setBusy(false)); }}>
      <ol className="question-list">{video.questions.map(question => <li key={question.index} className={`episode-question ${video.answered ? (question.correct ? "is-correct" : "is-wrong") : ""}`}>
        <p lang="nl" className="question-prompt">{question.prompt}</p>
        <div className="answer-options" role="radiogroup" aria-label={question.prompt}>{question.options.map((option, optionIndex) => <label key={optionIndex} className={video.answered && question.answer_index === optionIndex ? "is-answer" : ""}>
          <input type="radio" name={`video-question-${question.index}`} value={optionIndex} disabled={video.answered} checked={(video.answered ? question.chosen : answers[String(question.index)]) === optionIndex} onChange={() => setAnswers(current => ({ ...current, [String(question.index)]: optionIndex }))} />
          <span lang="nl">{option}</span></label>)}</div>
        {video.answered && question.evidence && <p className="question-evidence"><Icon name={question.correct ? "check" : "help"} size={15} /> <span lang="nl">In de video: “{question.evidence}”</span></p>}
      </li>)}</ol>
      {!video.answered && <button className="button" type="submit" disabled={!complete || busy}>Controleer mijn antwoorden</button>}
      {message && <p className="error" role="alert">{message}</p>}
    </form>
  </section>;
}
