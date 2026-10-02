"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { Icon } from "@/components/Icon";
import { EpisodeCard, coverClass } from "@/components/TodayHome";
import { ApiError } from "@/lib/client/api";
import { episodeHref, stageLabels, stories, type EpisodeSummary, type SeriesView } from "@/lib/client/stories";

const statusCopy: Record<string, string> = { queued: "wordt geschreven", generating: "wordt geschreven", ready: "klaar om te lezen", failed: "niet gelukt" };

export function StoryLibrary() {
  const [data, setData] = useState<{ series: SeriesView; items: EpisodeSummary[] } | null>(null);
  const [error, setError] = useState("");
  const [wish, setWish] = useState("");
  const [notice, setNotice] = useState("");
  const [busy, setBusy] = useState(false);
  useEffect(() => {
    const controller = new AbortController();
    stories.library(controller.signal).then(setData).catch(cause => { if (cause?.name !== "AbortError") setError("De verhalen konden niet worden geladen."); });
    return () => controller.abort();
  }, []);
  async function request() {
    setBusy(true); setNotice("");
    try { await stories.request(wish.trim()); setWish(""); setData(await stories.library()); setNotice("De schrijver is begonnen. De aflevering verschijnt hier en op Vandaag zodra ze klaar is."); }
    catch (cause) { setNotice(cause instanceof ApiError ? (cause.status === 409 ? "Er worden al twee afleveringen geschreven. Lees er eerst een." : cause.status === 429 ? "Je dagelijkse limiet voor de schrijver is bereikt." : cause.detail) : "Dat lukte nu niet."); }
    finally { setBusy(false); }
  }
  if (error) return <div className="error" role="alert">{error}</div>;
  if (!data) return <div className="path-loading" role="status">Verhalen laden…</div>;
  const next = data.items.find(item => item.status === "ready" && !item.read_at);
  const read = data.items.filter(item => item.read_at).length;
  return <div className="story-library" data-testid="story-library">
    <header className="path-heading">
      <div><p className="eyebrow">VERHALEN</p><h1>{data.series.title}</h1><p className="muted">Een doorlopend feuilleton uit {data.series.town}, geschreven op jouw niveau ({stageLabels[data.series.stage_id] ?? data.series.stage_id}). {read} van {data.items.length} afleveringen gelezen.</p></div>
      <span className="quiet-badge">{data.series.episode_count} afleveringen</span>
    </header>
    {next && <EpisodeCard episode={next} cta="Lees de volgende aflevering" />}
    <section className="wish-card inline" aria-labelledby="library-wish">
      <h2 id="library-wish">Een nieuwe aflevering vragen</h2>
      <form onSubmit={event => { event.preventDefault(); void request(); }}>
        <label htmlFor="library-wish-input" className="visually-hidden">Onderwerp</label>
        <input id="library-wish-input" value={wish} onChange={event => setWish(event.target.value)} maxLength={120} placeholder="Laat leeg voor een verrassing, of geef een onderwerp" />
        <button className="button" type="submit" disabled={busy}>Schrijf een aflevering</button>
      </form>
      {notice && <p className="practice-hint" role="status">{notice}</p>}
    </section>
    <ol className="episode-grid">{data.items.map(item => <li key={item.id} className={`episode-tile status-${item.status} ${item.read_at ? "is-read" : ""}`}>
      <div className={coverClass(item.number)} aria-hidden="true"><span className="cover-number">{item.number}</span></div>
      <div className="episode-tile-body">
        <p className="eyebrow">AFLEVERING {item.number} · {stageLabels[item.stage_id] ?? item.stage_id}</p>
        <h3>{item.status === "ready" ? item.title : item.theme}</h3>
        <p className="small-text muted">{item.status === "ready" ? `${item.word_count} woorden · ${item.read_at ? "gelezen" : "nog niet gelezen"}${item.rating === 1 ? " · 👍" : item.rating === -1 ? " · 👎" : ""}` : statusCopy[item.status]}</p>
        {item.status === "failed" && item.failure_reasons?.length > 0 && <details className="failure-details"><summary>Wat er niet klopte</summary><ul>{item.failure_reasons.map(reason => <li key={reason}><code>{reason}</code></li>)}</ul></details>}
        {item.status === "ready" ? <Link className="stage-link" href={episodeHref(item.id)}>{item.read_at ? "Lees opnieuw" : "Lees"}<Icon name="arrow" size={17} /></Link>
          : item.status === "failed" ? <button className="linklike" onClick={() => void stories.retry(item.id).then(() => stories.library()).then(setData).catch(() => setNotice("Opnieuw proberen lukte niet."))}>Opnieuw laten schrijven</button>
          : <span className="writing-dots" aria-hidden="true"><span /><span /><span /></span>}
      </div>
    </li>)}</ol>
    {data.items.length === 0 && <p className="muted">Nog geen afleveringen. Ga naar <Link href="/">Vandaag</Link>; daar start de eerste.</p>}
    <section className="cast-card" aria-labelledby="cast-title">
      <h2 id="cast-title">De personages</h2>
      <ul>{data.series.cast.map(person => <li key={person.name}><strong>{person.name}</strong> <span className="muted">{person.role}</span></li>)}</ul>
    </section>
  </div>;
}
