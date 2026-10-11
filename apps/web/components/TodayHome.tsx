"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import { Icon } from "@/components/Icon";
import { LearningText } from "@/components/LanguageSupport";
import { errorCopy, type FailureContext } from "@/lib/client/error-copy";
import { isAbort } from "@/lib/client/errors";
import {
  episodeHref,
  greeting,
  stageLabels,
  stories,
  type EpisodeSummary,
  type TodayPlan,
} from "@/lib/client/stories";
import { Cover, ProgressBar, ProgressRing, Skeleton, SkeletonPanel } from "@/components/ui";
import { useDeveloperDetails } from "@/components/shell/EnvContext";
import { HonestyChip } from "@/components/ui/HonestyChip";
import { episodeFailure } from "@/lib/client/failures";
import { UiText } from "@/components/ui/UiText";
import { WaitPracticeCard } from "@/components/exercise/WaitPracticeCard";
import { uiCopy, type Copy } from "@/lib/ui-copy";

const POLL_MS = 5000;
const POLL_LIMIT = 48; // four minutes: a local model writes an episode in one to three minutes

function dayLabel(iso: string) {
  const date = new Date(`${iso}T12:00:00`);
  return date.toLocaleDateString("nl-BE", { weekday: "long", day: "numeric", month: "long" });
}

export function TodayHome() {
  const developer = useDeveloperDetails();
  const [plan, setPlan] = useState<TodayPlan | null>(null);
  const [error, setError] = useState<Copy | null>(null);
  const [busy, setBusy] = useState("");
  const [wish, setWish] = useState("");
  const [notice, setNotice] = useState<Copy | null>(null);
  const [polls, setPolls] = useState(0);
  // opening the page, trying again after a failure and the stalled "Vernieuwen" prepare the day; the polls
  // and the reloads after an action only read it
  const load = useCallback(
    (signal?: AbortSignal, open = false) =>
      (open ? stories.prepare : stories.today)(signal)
        .then((value) => {
          setPlan(value);
          setError(null);
        })
        .catch((cause) => {
          if (!isAbort(cause)) setError(errorCopy(cause, uiCopy.today.loadFailed, undefined, "load"));
        }),
    [],
  );
  useEffect(() => {
    const controller = new AbortController();
    void load(controller.signal, true);
    return () => controller.abort();
  }, [load]);
  const pending = plan?.episode && (plan.episode.status === "queued" || plan.episode.status === "generating");
  const stalled = polls >= POLL_LIMIT;
  useEffect(() => {
    if (!pending || stalled) return;
    const timer = window.setTimeout(() => {
      setPolls((count) => count + 1);
      void load();
    }, POLL_MS);
    return () => window.clearTimeout(timer);
  }, [pending, stalled, plan, load]);

  /** Run one request; true when it went through. `load` handles its own failures, so a refresh never reads as one. */
  async function act(
    key: string,
    work: () => Promise<unknown>,
    done?: Copy,
    context: FailureContext = "action",
  ) {
    setBusy(key);
    setNotice(null);
    try {
      await work();
      await load();
      if (done) setNotice(done);
      return true;
    } catch (cause) {
      setNotice(
        errorCopy(
          cause,
          undefined,
          { 429: uiCopy.failures.writerLimit, paid_not_approved: uiCopy.failures.paidNotApproved },
          context,
        ),
      );
      return false;
    } finally {
      setBusy("");
    }
  }

  if (error)
    return (
      <div className="error" role="alert">
        <UiText text={error} tier="guide" inline />{" "}
        <button className="linklike" onClick={() => void load(undefined, true)}>
          <UiText text={uiCopy.action.retry} inline />
        </button>
      </div>
    );
  if (!plan)
    return (
      <SkeletonPanel label="Je dag voorbereiden…">
        <Skeleton lines={3} />
      </SkeletonPanel>
    );
  const { streak, goal, episode, failed, awaiting_choice: awaiting, words } = plan;
  const headline =
    plan.next_step === "read"
      ? "Er ligt een nieuwe aflevering klaar."
      : plan.next_step === "choose"
        ? "Hoe gaat het verder in de Lindestraat?"
        : plan.next_step === "review"
          ? `${words.due_count} ${words.due_count === 1 ? "woord wacht" : "woorden wachten"} op je.`
          : plan.next_step === "wait"
            ? "Je volgende aflevering wordt geschreven."
            : "Kies waar je vandaag mee begint.";

  return (
    <div className="today" data-testid="today-home">
      <header className="today-heading">
        <p className="eyebrow">VANDAAG · {dayLabel(plan.date)}</p>
        <h1>
          {greeting()}. {headline}
        </h1>
        <p className="muted">
          <LearningText
            text={{
              nl: "Eén aflevering, een paar woorden, één gesprek. Twintig minuten volstaan.",
              en: "One episode, a few words, one conversation. Twenty minutes is enough.",
              fa: "یک قسمت، چند واژه، یک گفت‌وگو. بیست دقیقه کافی است.",
            }}
          />
        </p>
      </header>

      <div className="today-grid">
        <section className="today-episode" aria-labelledby="today-episode-title">
          {episode && episode.status === "ready" && (
            <EpisodeCard episode={episode} cta={episode.read_at ? "Lees opnieuw" : "Lees aflevering"} />
          )}
          {episode && pending && (
            <div className="episode-pending" role="status">
              <Cover number={episode.number} />
              <div>
                <p className="eyebrow">
                  AFLEVERING {episode.number} · {stageLabels[episode.stage_id] ?? episode.stage_id}
                </p>
                <h2 id="today-episode-title">De schrijver is bezig…</h2>
                <p className="muted">
                  Thema: {episode.theme}. Een nieuwe aflevering van <strong>{plan.series.title}</strong> wordt
                  nu geschreven en gecontroleerd. Dit duurt meestal één tot drie minuten.
                </p>
                <span className="writing-dots" data-anim="dots" aria-hidden="true">
                  <span />
                  <span />
                  <span />
                </span>
                {stalled && (
                  <p className="small-text">
                    Het duurt langer dan verwacht.{" "}
                    <button
                      className="linklike"
                      onClick={() => {
                        setPolls(0);
                        void load(undefined, true);
                      }}
                    >
                      Vernieuwen
                    </button>
                  </p>
                )}
              </div>
            </div>
          )}
          {/* outside the status region, which announces its own changes */}
          {episode && pending && <WaitPracticeCard />}
          {!episode && awaiting && (
            <div className="episode-pending choose-next">
              <Cover number={awaiting.number} />
              <div>
                <p className="eyebrow">AFLEVERING {awaiting.number} · KEUZE</p>
                <h2 id="today-episode-title">Jij beslist hoe het verdergaat.</h2>
                <p className="muted">
                  Je las <strong>{awaiting.title}</strong>, maar koos nog niet. De volgende aflevering wacht
                  op jouw keuze.
                </p>
                <Link className="button" href={episodeHref(awaiting.id) + "#keuze"}>
                  Maak je keuze
                  <Icon name="arrow" size={18} />
                </Link>
              </div>
            </div>
          )}
          {!episode && !awaiting && failed && (
            <div className="episode-pending episode-failed" role="status">
              <Cover number={failed.number} />
              <div>
                <p className="eyebrow">AFLEVERING {failed.number}</p>
                <h2 id="today-episode-title">
                  <UiText text={episodeFailure(failed.error_code, uiCopy.failures, developer).title} />
                </h2>
                <p className="muted">
                  <UiText
                    text={episodeFailure(failed.error_code, uiCopy.failures, developer).body}
                    tier="guide"
                  />
                </p>
                {developer && failed.failure_reasons?.length > 0 && (
                  <details className="failure-details">
                    <summary>Wat er niet klopte</summary>
                    <ul>
                      {failed.failure_reasons.map((reason) => (
                        <li key={reason}>
                          <code>{reason}</code>
                        </li>
                      ))}
                    </ul>
                  </details>
                )}
                {failed.error_code !== "allowance" && failed.error_code !== "paid_not_approved" && (
                  <button
                    className="button"
                    disabled={busy === "retry"}
                    onClick={() =>
                      void act("retry", () => stories.retry(failed.id), uiCopy.today.retryStarted)
                    }
                  >
                    Opnieuw laten schrijven
                  </button>
                )}
              </div>
            </div>
          )}
          {!episode && !awaiting && !failed && (
            <div className="episode-pending">
              <div className="episode-cover tone-1" aria-hidden="true">
                <span className="cover-number">1</span>
              </div>
              <div>
                <h2 id="today-episode-title">Je eerste aflevering komt eraan.</h2>
                <p className="muted">Vernieuw zo meteen deze pagina.</p>
              </div>
            </div>
          )}
        </section>

        <aside className="today-side">
          <div className="streak-card">
            <ProgressRing
              className={`streak-ring ${streak.today_active ? "is-active" : ""}`}
              value={goal.points}
              max={goal.target}
              label={`${streak.current} ${streak.current === 1 ? "dag" : "dagen"} op rij, ${goal.points} van ${goal.target} punten vandaag`}
              tone={streak.today_active ? "warm" : "accent"}
            >
              <span className="streak-number">{streak.current}</span>
              <span className="streak-label">{streak.current === 1 ? "dag op rij" : "dagen op rij"}</span>
            </ProgressRing>
            <dl className="streak-facts">
              <div>
                <dt>Vandaag</dt>
                <dd>
                  {goal.points} / {goal.target} punten
                </dd>
              </div>
              <div>
                <dt>Beste reeks</dt>
                <dd>
                  {streak.best} {streak.best === 1 ? "dag" : "dagen"}
                </dd>
              </div>
              <div>
                <dt>Actieve dagen</dt>
                <dd>{streak.active_days}</dd>
              </div>
            </dl>
            <ProgressBar
              className="goal-bar"
              value={goal.points}
              max={goal.target}
              label="Dagdoel"
              tone="warm"
            />
            <p className="small-text muted">
              {goal.met
                ? "Dagdoel gehaald. Alles wat je nu nog doet, is extra."
                : `Nog ${goal.target - goal.points} punten tot je dagdoel.`}
            </p>
            <ol className="day-dots" aria-label="De laatste veertien dagen">
              {plan.recent_days.map((day) => (
                <li
                  key={day.day}
                  className={day.goal_met ? "is-goal" : day.points > 0 ? "is-active" : ""}
                  title={`${day.day}: ${day.points} punten`}
                />
              ))}
            </ol>
          </div>
          <Link href="/woorden" className={`words-card ${words.due_count ? "has-due" : ""}`}>
            <span className="words-count">{words.due_count}</span>
            <span>
              <strong>{words.due_count === 1 ? "woord om te herhalen" : "woorden om te herhalen"}</strong>
              <small>
                {words.total} bewaard · {words.learned_count} stevig onthouden
              </small>
            </span>
            <Icon name="arrow" />
          </Link>
          <Link
            href={plan.videos?.ready ? `/videos/${plan.videos.ready.id}` : "/videos"}
            className={`words-card video-card ${plan.videos?.ready ? "has-due" : ""}`}
            data-testid="today-video"
          >
            <span className="words-count">
              <Icon name="play" size={22} />
            </span>
            <span>
              {plan.videos?.ready ? (
                <>
                  <strong>Een video staat klaar</strong>
                  <small>
                    {plan.videos.ready.title || plan.videos.ready.topic} · {plan.videos.ready.kind_label}
                  </small>
                </>
              ) : plan.videos?.pending ? (
                <>
                  <strong>Je video wordt gemaakt</strong>
                  <small>Dat duurt een paar minuten.</small>
                </>
              ) : (
                <>
                  <strong>Vraag een video</strong>
                  <small>Op jouw niveau, over wat jij kiest.</small>
                </>
              )}
            </span>
            <Icon name="arrow" />
          </Link>
        </aside>
      </div>

      <section className="today-actions" aria-labelledby="wish-title">
        <div className="wish-card">
          <h2 id="wish-title">Vraag een verhaal</h2>
          <p className="muted">
            Zeg waar de volgende aflevering over moet gaan. De schrijver houdt je niveau en de personages aan.
          </p>
          <form
            onSubmit={(event) => {
              event.preventDefault();
              if (!wish.trim()) return;
              // the wish stays in the field until the writer has it
              void act("wish", () => stories.request(wish.trim()), uiCopy.today.wishQueued, "input").then(
                (sent) => {
                  if (sent) setWish("");
                },
              );
            }}
          >
            <label htmlFor="story-wish" className="visually-hidden">
              Onderwerp
            </label>
            <input
              id="story-wish"
              value={wish}
              onChange={(event) => setWish(event.target.value)}
              maxLength={120}
              placeholder="bv. een regenachtige dag op de markt"
            />
            <button className="button" type="submit" disabled={busy === "wish" || !wish.trim()}>
              Schrijf dit
            </button>
          </form>
          {notice && (
            <p className="practice-hint" role="status">
              <UiText text={notice} tier="guide" />
            </p>
          )}
        </div>
        <div className="cast-card">
          <h2>Wie is wie in {plan.series.title}</h2>
          <ul>
            {plan.series.cast.map((person) => (
              <li key={person.name}>
                <strong>{person.name}</strong> <span className="muted">{person.role}</span>
              </li>
            ))}
          </ul>
          {plan.series.memory.length > 0 && (
            <details>
              <summary>Wat er al gebeurde</summary>
              <ol className="memory-list">
                {plan.series.memory.map((item) => (
                  <li key={item.number}>
                    <strong>
                      {item.number}. {item.title}
                    </strong>{" "}
                    {item.recap}
                    {item.choice && <em> Jouw keuze: {item.choice}</em>}
                  </li>
                ))}
              </ol>
            </details>
          )}
        </div>
      </section>

      <div className="path-bottom-links">
        <Link href="/leerpad">
          <Icon name="chart" />
          <span>
            <strong>Mijn leerpad</strong>
            <small>Twaalf niveaus met woorden, grammatica en toetsen.</small>
          </span>
          <Icon name="arrow" />
        </Link>
        <Link href="/missions">
          <Icon name="book" />
          <span>
            <strong>Praktijkgesprekken</strong>
            <small>Een afspraak verzetten, iets terugbrengen, bestellen.</small>
          </span>
          <Icon name="arrow" />
        </Link>
        <Link href="/speech-check">
          <Icon name="mic" />
          <span>
            <strong>Spraakstudio</strong>
            <small>Neem op, luister terug en vergelijk.</small>
          </span>
          <Icon name="arrow" />
        </Link>
      </div>
      <div className="honesty-row">
        <HonestyChip kind="generated" />
      </div>
    </div>
  );
}

export function EpisodeCard({ episode, cta }: { episode: EpisodeSummary; cta: string }) {
  return (
    <Link href={episodeHref(episode.id)} className="episode-card" data-testid="episode-card">
      <Cover number={episode.number} caption="De Lindestraat" />
      <div className="episode-card-body">
        <p className="eyebrow">
          AFLEVERING {episode.number} · {stageLabels[episode.stage_id] ?? episode.stage_id} ·{" "}
          {episode.word_count} WOORDEN
        </p>
        <h2 id="today-episode-title">{episode.title}</h2>
        <p className="muted">
          Thema: {episode.theme}
          {episode.theme_source === "learner" ? " (jouw wens)" : ""}
        </p>
        <span className="button">
          {cta}
          <Icon name="arrow" size={18} />
        </span>
      </div>
    </Link>
  );
}
