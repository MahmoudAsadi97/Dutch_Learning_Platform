"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import { Icon } from "@/components/Icon";
import { LearningText } from "@/components/LanguageSupport";
import { ApiError } from "@/lib/client/api";
import { stageLabels } from "@/lib/client/stories";
import { clock, videoHref, videos, type VideoLibrary as Library, type VideoSummary } from "@/lib/client/videos";

const POLL_MS = 6000;
const POLL_LIMIT = 150; // fifteen minutes: the avatar service renders a minute of video in a few minutes

export const statusCopy: Record<string, string> = {
  queued: "wacht op de schrijver", writing: "het script wordt geschreven", rendering: "de video wordt gemaakt",
  ready: "klaar om te bekijken", failed: "niet gelukt",
};

export function failureCopy(video: VideoSummary): string {
  switch (video.error_code) {
    case "allowance": return "De schrijver heeft vandaag genoeg geschreven. Probeer het morgen opnieuw.";
    case "allowance_video": return "Je dagelijkse videotijd is op. Morgen kan er weer een video gemaakt worden.";
    case "quality": return "Het script haalde de automatische controle niet, ook niet na een tweede poging.";
    case "paid_not_approved": return "Betaald modelgebruik is in deze omgeving niet ingeschakeld.";
    case "render":
    case "render_timeout": return "Het maken van de video is mislukt. Het script is bewaard; een nieuwe poging gebruikt het opnieuw.";
    case "too_long": return "Het script was te lang voor één video.";
    default: return "De schrijver of de videodienst was even niet bereikbaar.";
  }
}

export function VideoTile({ video, onRetry }: { video: VideoSummary; onRetry?: (video: VideoSummary) => void }) {
  const pending = video.status === "queued" || video.status === "writing" || video.status === "rendering";
  return <li className={`video-tile status-${video.status} ${video.watched_at ? "is-watched" : ""}`} data-testid="video-tile">
    <div className={`video-poster kind-${video.kind}`} aria-hidden="true">
      <span className="poster-badge">{video.kind_label}</span>
      {video.status === "ready" ? <span className="poster-play"><Icon name="play" size={22} /></span> : pending ? <span className="writing-dots"><span /><span /><span /></span> : <span className="poster-mark">!</span>}
      {video.duration_seconds > 0 && <span className="poster-clock">{clock(video.duration_seconds)}</span>}
    </div>
    <div className="video-tile-body">
      <p className="eyebrow">{stageLabels[video.stage_id] ?? video.stage_id} · {video.kind_label.toUpperCase()}</p>
      <h3>{video.status === "ready" && video.title ? video.title : video.topic}</h3>
      <p className="small-text muted">{video.status === "ready" ? `${video.scene_count} scènes · ${video.word_count} woorden · ${video.watched_at ? "bekeken" : "nog niet bekeken"}${video.rating === 1 ? " · 👍" : video.rating === -1 ? " · 👎" : ""}` : statusCopy[video.status]}</p>
      {video.status === "failed" && <p className="small-text">{failureCopy(video)}</p>}
      {video.status === "failed" && video.failure_reasons?.length > 0 && <details className="failure-details"><summary>Wat er niet klopte</summary><ul>{video.failure_reasons.map(reason => <li key={reason}><code>{reason}</code></li>)}</ul></details>}
      {video.status === "ready" ? <Link className="stage-link" href={videoHref(video.id)}>{video.watched_at ? "Bekijk opnieuw" : "Bekijk"}<Icon name="arrow" size={17} /></Link>
        : video.status === "failed" && onRetry && video.error_code !== "paid_not_approved" && video.error_code !== "allowance" && video.error_code !== "allowance_video"
          ? <button type="button" className="linklike" onClick={() => onRetry(video)}>Opnieuw proberen</button> : null}
    </div>
  </li>;
}

export function VideoLibrary() {
  const [data, setData] = useState<Library | null>(null);
  const [error, setError] = useState("");
  const [topic, setTopic] = useState("");
  const [stage, setStage] = useState("");
  const [kind, setKind] = useState("uitleg");
  const [notice, setNotice] = useState("");
  const [busy, setBusy] = useState(false);
  const [polls, setPolls] = useState(0);
  const load = useCallback((signal?: AbortSignal) => videos.library(signal)
    .then(value => { setData(value); setError(""); setStage(current => current || value.default_stage); })
    .catch(cause => { if (!(cause instanceof DOMException && cause.name === "AbortError")) setError("De video's konden niet worden geladen."); }), []);
  useEffect(() => { const controller = new AbortController(); void load(controller.signal); return () => controller.abort(); }, [load]);
  const pending = data?.items.some(item => item.status === "queued" || item.status === "writing" || item.status === "rendering") ?? false;
  const stalled = polls >= POLL_LIMIT;
  useEffect(() => {
    if (!pending || stalled) return;
    const timer = window.setTimeout(() => { setPolls(count => count + 1); void load(); }, POLL_MS);
    return () => window.clearTimeout(timer);
  }, [pending, stalled, data, load]);

  async function request() {
    setBusy(true); setNotice("");
    try {
      await videos.request(stage, topic.trim(), kind);
      setTopic(""); setPolls(0);
      await load();
      setNotice("De schrijver is begonnen. De video verschijnt hier zodra ze klaar is; dat duurt een paar minuten.");
    } catch (cause) {
      setNotice(cause instanceof ApiError ? (cause.status === 409 ? "Er worden al twee video's gemaakt. Bekijk er eerst een." : cause.status === 429 ? "Je dagelijkse limiet is bereikt." : cause.detail) : "Dat lukte nu niet.");
    } finally { setBusy(false); }
  }
  async function retry(video: VideoSummary) {
    setNotice("");
    try { await videos.retry(video.id); setPolls(0); await load(); setNotice("Nieuwe poging gestart."); }
    catch { setNotice("Opnieuw proberen lukte niet."); }
  }

  if (error) return <div className="error" role="alert">{error}</div>;
  if (!data) return <div className="path-loading" role="status">Video&apos;s laden…</div>;
  const ready = data.items.filter(item => item.status === "ready").length;
  const presenter = data.renderer.label === "avatar" ? "een virtuele presentator" : "gesproken scènekaarten";

  return <div className="video-library" data-testid="video-library">
    <header className="path-heading">
      <div>
        <p className="eyebrow">VIDEO&apos;S</p>
        <h1>Een korte video op jouw niveau, over wat jij kiest.</h1>
        <p className="muted"><LearningText text={{
          nl: `Kies een niveau en een onderwerp. Het taalmodel schrijft een script op dat niveau, de computer controleert het, en ${presenter} spreekt het uit in het Belgisch Nederlands, met ondertitels en vertaling.`,
          en: `Pick a level and a topic. The language model writes a script at that level, the code checks it, and ${data.renderer.label === "avatar" ? "a virtual presenter delivers" : "spoken scene cards deliver"} it in Belgian Dutch with subtitles and a translation.`,
          fa: "یک سطح و یک موضوع انتخاب کن. مدل زبانی متنی در آن سطح می‌نویسد، برنامه آن را بررسی می‌کند و ویدیو با زیرنویس و ترجمه به هلندی بلژیکی ساخته می‌شود.",
        }} /></p>
      </div>
      <span className="quiet-badge">{ready} {ready === 1 ? "video" : "video's"}</span>
    </header>

    <section className="wish-card inline video-request" aria-labelledby="video-request-title">
      <h2 id="video-request-title">Een nieuwe video vragen</h2>
      <form onSubmit={event => { event.preventDefault(); void request(); }}>
        <div className="video-request-row">
          <label>Niveau<select value={stage} onChange={event => setStage(event.target.value)} data-testid="video-level">
            {data.levels.map(level => <option key={level.id} value={level.id}>{level.label}</option>)}
          </select></label>
          <label>Vorm<select value={kind} onChange={event => setKind(event.target.value)} data-testid="video-kind">
            {data.kinds.map(item => <option key={item.id} value={item.id}>{item.label}</option>)}
          </select></label>
        </div>
        <label htmlFor="video-topic" className="visually-hidden">Onderwerp</label>
        <input id="video-topic" value={topic} onChange={event => setTopic(event.target.value)} maxLength={120} placeholder="Waarover? bv. een afspraak bij de dokter, of laat leeg voor een verrassing" data-testid="video-topic" />
        <button className="button" type="submit" disabled={busy || !stage} data-testid="video-submit">Maak een video</button>
      </form>
      <p className="small-text muted">Hoogstens {data.max_pending} video&apos;s tegelijk in de maak; een video duurt minstens {data.min_seconds} seconden en hoogstens {clock(data.max_seconds)} minuten, afhankelijk van het niveau. {data.renderer.label === "avatar" ? "Elke minuut video kost geld; je dagelijkse videotijd staat bij Instellingen." : "Deze omgeving tekent scènekaarten en gebruikt de lokale stem."}</p>
      {notice && <p className="practice-hint" role="status">{notice}</p>}
      {stalled && pending && <p className="small-text">Het duurt langer dan verwacht. <button className="linklike" onClick={() => { setPolls(0); void load(); }}>Vernieuwen</button></p>}
    </section>

    {data.items.length === 0 ? <p className="muted">Nog geen video&apos;s. Vraag hierboven je eerste.</p>
      : <ol className="video-grid">{data.items.map(item => <VideoTile key={item.id} video={item} onRetry={retry} />)}</ol>}

    <section className="cast-card" aria-labelledby="video-honesty">
      <h2 id="video-honesty">Wat je ziet</h2>
      <ul>
        <li><strong>Script</strong> <span className="muted">geschreven door het taalmodel, automatisch gecontroleerd op niveau en woordenschat; nog niet nagekeken door een taaldocent.</span></li>
        <li><strong>Stem en beeld</strong> <span className="muted">{data.renderer.label === "avatar" ? `synthetische stem (${data.renderer.voice}) en een virtuele presentator; het is geen echte persoon.` : `synthetische stem (${data.renderer.voice || "lokaal"}) over getekende scènekaarten.`}</span></li>
        <li><strong>Ondertitels</strong> <span className="muted">komen uit de gesproken tekst zelf; de vertalingen onder het transcript komen van het taalmodel.</span></li>
      </ul>
    </section>
  </div>;
}
