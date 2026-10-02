"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import { Icon } from "@/components/Icon";
import { LearningText } from "@/components/LanguageSupport";
import { ApiError } from "@/lib/client/api";
import { episodeHref, greeting, stageLabels, stories, type EpisodeSummary, type TodayPlan } from "@/lib/client/stories";

const POLL_MS = 5000;
const POLL_LIMIT = 48; // four minutes: a local model writes an episode in one to three minutes

export function coverClass(number: number) { return `episode-cover tone-${((number - 1) % 6) + 1}`; }

function dayLabel(iso: string) {
  const date = new Date(`${iso}T12:00:00`);
  return date.toLocaleDateString("nl-BE", { weekday: "long", day: "numeric", month: "long" });
}

export function TodayHome() {
  const [plan, setPlan] = useState<TodayPlan | null>(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState("");
  const [wish, setWish] = useState("");
  const [notice, setNotice] = useState("");
  const [polls, setPolls] = useState(0);
  const load = useCallback((signal?: AbortSignal) => stories.today(signal)
    .then(value => { setPlan(value); setError(""); })
    .catch(cause => { if (!(cause instanceof DOMException && cause.name === "AbortError")) setError("Je overzicht kon niet worden geladen."); }), []);
  useEffect(() => { const controller = new AbortController(); void load(controller.signal); return () => controller.abort(); }, [load]);
  const pending = plan?.episode && (plan.episode.status === "queued" || plan.episode.status === "generating");
  const stalled = polls >= POLL_LIMIT;
  useEffect(() => {
    if (!pending || stalled) return;
    const timer = window.setTimeout(() => { setPolls(count => count + 1); void load(); }, POLL_MS);
    return () => window.clearTimeout(timer);
  }, [pending, stalled, plan, load]);

  async function act(key: string, work: () => Promise<unknown>, done?: string) {
    setBusy(key); setNotice("");
    try { await work(); await load(); if (done) setNotice(done); }
    catch (cause) { setNotice(cause instanceof ApiError && cause.status === 429 ? "Je dagelijkse limiet voor de schrijver is bereikt. Morgen schrijft hij verder." : cause instanceof ApiError && cause.status === 409 ? cause.detail : "Dat lukte nu niet. Probeer het zo opnieuw."); }
    finally { setBusy(""); }
  }

  if (error) return <div className="error" role="alert">{error} <button className="linklike" onClick={() => void load()}>Opnieuw proberen</button></div>;
  if (!plan) return <div className="path-loading" role="status">Je dag voorbereiden…</div>;
  const { streak, goal, episode, failed, awaiting_choice: awaiting, words } = plan;
  const progress = Math.min(100, Math.round(goal.points / goal.target * 100));
  const headline = plan.next_step === "read" ? "Er ligt een nieuwe aflevering klaar."
    : plan.next_step === "choose" ? "Hoe gaat het verder in de Lindestraat?"
    : plan.next_step === "review" ? `${words.due_count} ${words.due_count === 1 ? "woord wacht" : "woorden wachten"} op je.`
    : plan.next_step === "wait" ? "Je volgende aflevering wordt geschreven."
    : "Kies waar je vandaag mee begint.";

  return <div className="today" data-testid="today-home">
    <header className="today-heading">
      <p className="eyebrow">VANDAAG · {dayLabel(plan.date)}</p>
      <h1>{greeting()}. {headline}</h1>
      <p className="muted"><LearningText text={{ nl: "Eén aflevering, een paar woorden, één gesprek. Twintig minuten volstaan.", en: "One episode, a few words, one conversation. Twenty minutes is enough.", fa: "یک قسمت، چند واژه، یک گفت‌وگو. بیست دقیقه کافی است." }} /></p>
    </header>

    <div className="today-grid">
      <section className="today-episode" aria-labelledby="today-episode-title">
        {episode && episode.status === "ready" && <EpisodeCard episode={episode} cta={episode.read_at ? "Lees opnieuw" : "Lees aflevering"} />}
        {episode && pending && <div className="episode-pending" role="status">
          <div className={coverClass(episode.number)} aria-hidden="true"><span className="cover-number">{episode.number}</span></div>
          <div>
            <p className="eyebrow">AFLEVERING {episode.number} · {stageLabels[episode.stage_id] ?? episode.stage_id}</p>
            <h2 id="today-episode-title">De schrijver is bezig…</h2>
            <p className="muted">Thema: {episode.theme}. Een nieuwe aflevering van <strong>{plan.series.title}</strong> wordt nu geschreven en gecontroleerd. Dit duurt meestal één tot drie minuten.</p>
            <span className="writing-dots" aria-hidden="true"><span /><span /><span /></span>
            {stalled && <p className="small-text">Het duurt langer dan verwacht. <button className="linklike" onClick={() => { setPolls(0); void load(); }}>Vernieuwen</button></p>}
          </div>
        </div>}
        {!episode && awaiting && <div className="episode-pending choose-next">
          <div className={coverClass(awaiting.number)} aria-hidden="true"><span className="cover-number">{awaiting.number}</span></div>
          <div>
            <p className="eyebrow">AFLEVERING {awaiting.number} · KEUZE</p>
            <h2 id="today-episode-title">Jij beslist hoe het verdergaat.</h2>
            <p className="muted">Je las <strong>{awaiting.title}</strong>, maar koos nog niet. De volgende aflevering wacht op jouw keuze.</p>
            <Link className="button" href={episodeHref(awaiting.id) + "#keuze"}>Maak je keuze<Icon name="arrow" size={18} /></Link>
          </div>
        </div>}
        {!episode && !awaiting && failed && <div className="episode-pending episode-failed" role="status">
          <div className={coverClass(failed.number)} aria-hidden="true"><span className="cover-number">{failed.number}</span></div>
          <div>
            <p className="eyebrow">AFLEVERING {failed.number}</p>
            <h2 id="today-episode-title">{failed.error_code === "allowance" ? "De schrijver heeft vandaag genoeg geschreven." : failed.error_code === "quality" ? "Deze aflevering haalde de controle niet." : "De schrijver is even niet bereikbaar."}</h2>
            <p className="muted">{failed.error_code === "quality" ? "De tekst haalde de automatische controle niet, ook niet na een tweede poging. Een nieuwe poging gebruikt dezelfde personages." : failed.error_code === "allowance" ? "Je dagelijkse limiet voor modelgebruik is bereikt. Probeer het morgen opnieuw of herhaal vandaag je woorden." : failed.error_code === "paid_not_approved" ? "Betaald modelgebruik is in deze omgeving niet ingeschakeld." : "Controleer of het taalmodel draait (Instellingen › Technische ondersteuning) en probeer opnieuw."}</p>
            {failed.failure_reasons?.length > 0 && <details className="failure-details"><summary>Wat er niet klopte</summary><ul>{failed.failure_reasons.map(reason => <li key={reason}><code>{reason}</code></li>)}</ul></details>}
            {failed.error_code !== "allowance" && failed.error_code !== "paid_not_approved" && <button className="button" disabled={busy === "retry"} onClick={() => void act("retry", () => stories.retry(failed.id), "De schrijver begint opnieuw.")}>Opnieuw laten schrijven</button>}
          </div>
        </div>}
        {!episode && !awaiting && !failed && <div className="episode-pending"><div className="episode-cover tone-1" aria-hidden="true"><span className="cover-number">1</span></div><div><h2 id="today-episode-title">Je eerste aflevering komt eraan.</h2><p className="muted">Vernieuw zo meteen deze pagina.</p></div></div>}
      </section>

      <aside className="today-side">
        <div className="streak-card">
          <div className={`streak-ring ${streak.today_active ? "is-active" : ""}`} role="img" aria-label={`${streak.current} dagen op rij`}>
            <span className="streak-number">{streak.current}</span>
            <span className="streak-label">{streak.current === 1 ? "dag op rij" : "dagen op rij"}</span>
          </div>
          <dl className="streak-facts">
            <div><dt>Vandaag</dt><dd>{goal.points} / {goal.target} punten</dd></div>
            <div><dt>Beste reeks</dt><dd>{streak.best} {streak.best === 1 ? "dag" : "dagen"}</dd></div>
            <div><dt>Actieve dagen</dt><dd>{streak.active_days}</dd></div>
          </dl>
          <div className="goal-bar" role="progressbar" aria-label="Dagdoel" aria-valuenow={goal.points} aria-valuemin={0} aria-valuemax={goal.target}><span style={{ width: `${progress}%` }} /></div>
          <p className="small-text muted">{goal.met ? "Dagdoel gehaald. Alles wat je nu nog doet, is extra." : `Nog ${goal.target - goal.points} punten tot je dagdoel.`}</p>
          <ol className="day-dots" aria-label="De laatste veertien dagen">{plan.recent_days.map(day => <li key={day.day} className={day.goal_met ? "is-goal" : day.points > 0 ? "is-active" : ""} title={`${day.day}: ${day.points} punten`} />)}</ol>
        </div>
        <Link href="/woorden" className={`words-card ${words.due_count ? "has-due" : ""}`}>
          <span className="words-count">{words.due_count}</span>
          <span><strong>{words.due_count === 1 ? "woord om te herhalen" : "woorden om te herhalen"}</strong><small>{words.total} bewaard · {words.learned_count} stevig onthouden</small></span>
          <Icon name="arrow" />
        </Link>
        <Link href={plan.videos?.ready ? `/videos/${plan.videos.ready.id}` : "/videos"} className={`words-card video-card ${plan.videos?.ready ? "has-due" : ""}`} data-testid="today-video">
          <span className="words-count"><Icon name="play" size={22} /></span>
          <span>{plan.videos?.ready
            ? <><strong>Een video staat klaar</strong><small>{plan.videos.ready.title || plan.videos.ready.topic} · {plan.videos.ready.kind_label}</small></>
            : plan.videos?.pending
              ? <><strong>Je video wordt gemaakt</strong><small>Dat duurt een paar minuten.</small></>
              : <><strong>Vraag een video</strong><small>Op jouw niveau, over wat jij kiest.</small></>}</span>
          <Icon name="arrow" />
        </Link>
      </aside>
    </div>

    <section className="today-actions" aria-labelledby="wish-title">
      <div className="wish-card">
        <h2 id="wish-title">Vraag een verhaal</h2>
        <p className="muted">Zeg waar de volgende aflevering over moet gaan. De schrijver houdt je niveau en de personages aan.</p>
        <form onSubmit={event => { event.preventDefault(); if (!wish.trim()) return; void act("wish", () => stories.request(wish.trim()), "Je wens staat in de wachtrij. De aflevering verschijnt hierboven zodra ze klaar is."); setWish(""); }}>
          <label htmlFor="story-wish" className="visually-hidden">Onderwerp</label>
          <input id="story-wish" value={wish} onChange={event => setWish(event.target.value)} maxLength={120} placeholder="bv. een regenachtige dag op de markt" />
          <button className="button" type="submit" disabled={busy === "wish" || !wish.trim()}>Schrijf dit</button>
        </form>
        <div className="level-row">
          <label htmlFor="story-level">Niveau van de verhalen</label>
          <select id="story-level" value={plan.series.stage_id} disabled={busy === "level"} onChange={event => void act("level", () => stories.level(event.target.value), "Vanaf de volgende aflevering schrijft de schrijver op dit niveau.")}>
            {plan.levels.map(level => <option key={level.id} value={level.id}>{level.label}</option>)}
          </select>
        </div>
        {notice && <p className="practice-hint" role="status">{notice}</p>}
      </div>
      <div className="cast-card">
        <h2>Wie is wie in {plan.series.title}</h2>
        <ul>{plan.series.cast.map(person => <li key={person.name}><strong>{person.name}</strong> <span className="muted">{person.role}</span></li>)}</ul>
        {plan.series.memory.length > 0 && <details><summary>Wat er al gebeurde</summary><ol className="memory-list">{plan.series.memory.map(item => <li key={item.number}><strong>{item.number}. {item.title}</strong> {item.recap}{item.choice && <em> Jouw keuze: {item.choice}</em>}</li>)}</ol></details>}
      </div>
    </section>

    <div className="path-bottom-links">
      <Link href="/leerpad"><Icon name="chart" /><span><strong>Mijn leerpad</strong><small>Twaalf niveaus met woorden, grammatica en toetsen.</small></span><Icon name="arrow" /></Link>
      <Link href="/missions"><Icon name="book" /><span><strong>Praktijkgesprekken</strong><small>Een afspraak verzetten, iets terugbrengen, bestellen.</small></span><Icon name="arrow" /></Link>
      <Link href="/speech-check"><Icon name="mic" /><span><strong>Spraakstudio</strong><small>Neem op, luister terug en vergelijk.</small></span><Icon name="arrow" /></Link>
    </div>
    <p className="course-note">De verhalen worden door een taalmodel geschreven en automatisch gecontroleerd op lengte, moeilijkheid en samenhang. Ze zijn nog niet door een taaldocent nagekeken.</p>
  </div>;
}

export function EpisodeCard({ episode, cta }: { episode: EpisodeSummary; cta: string }) {
  return <Link href={episodeHref(episode.id)} className="episode-card" data-testid="episode-card">
    <div className={coverClass(episode.number)} aria-hidden="true"><span className="cover-number">{episode.number}</span><span className="cover-town">De Lindestraat</span></div>
    <div className="episode-card-body">
      <p className="eyebrow">AFLEVERING {episode.number} · {stageLabels[episode.stage_id] ?? episode.stage_id} · {episode.word_count} WOORDEN</p>
      <h2 id="today-episode-title">{episode.title}</h2>
      <p className="muted">Thema: {episode.theme}{episode.theme_source === "learner" ? " (jouw wens)" : ""}</p>
      <span className="button">{cta}<Icon name="arrow" size={18} /></span>
    </div>
  </Link>;
}
