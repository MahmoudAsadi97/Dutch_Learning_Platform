"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { Icon } from "@/components/Icon";
import { EpisodeCard } from "@/components/TodayHome";
import { useDeveloperDetails } from "@/components/shell/EnvContext";
import { Cover, EmptyState, Skeleton, SkeletonPanel } from "@/components/ui";
import { UiText } from "@/components/ui/UiText";
import { errorCopy } from "@/lib/client/error-copy";
import { isAbort } from "@/lib/client/errors";
import {
  episodeHref,
  stageLabels,
  stories,
  type EpisodeSummary,
  type SeriesView,
} from "@/lib/client/stories";
import { episodeCopy } from "@/lib/copy/episode";
import { uiCopy, type Copy } from "@/lib/ui-copy";

const statusCopy: Record<string, string> = {
  queued: "wordt geschreven",
  generating: "wordt geschreven",
  ready: "klaar om te lezen",
  failed: "niet gelukt",
};

export function StoryLibrary() {
  const [data, setData] = useState<{ series: SeriesView; items: EpisodeSummary[] } | null>(null);
  const [error, setError] = useState<Copy | null>(null);
  const [wish, setWish] = useState("");
  const [notice, setNotice] = useState<Copy | null>(null);
  const [busy, setBusy] = useState(false);
  const developer = useDeveloperDetails();
  useEffect(() => {
    const controller = new AbortController();
    stories
      .library(controller.signal)
      .then(setData)
      .catch((cause) => {
        if (!isAbort(cause)) setError(errorCopy(cause, episodeCopy.libraryLoadFailed, undefined, "load"));
      });
    return () => controller.abort();
  }, []);
  async function request() {
    setBusy(true);
    setNotice(null);
    try {
      await stories.request(wish.trim());
    } catch (cause) {
      // the wish is still in the field
      setNotice(errorCopy(cause, undefined, { 429: uiCopy.failures.writerLimit }, "input"));
      setBusy(false);
      return;
    }
    setWish("");
    setNotice(episodeCopy.requestStarted);
    setBusy(false);
    // the episode is queued either way; a failed refresh only means the list shows it on the next visit
    await stories
      .library()
      .then(setData)
      .catch(() => undefined);
  }
  if (error)
    return (
      <div className="error" role="alert">
        <UiText text={error} tier="guide" />
      </div>
    );
  if (!data)
    return (
      <SkeletonPanel label="Verhalen laden…">
        <Skeleton lines={3} />
      </SkeletonPanel>
    );
  const next = data.items.find((item) => item.status === "ready" && !item.read_at);
  const read = data.items.filter((item) => item.read_at).length;
  return (
    <div className="story-library" data-testid="story-library">
      <header className="path-heading">
        <div>
          <p className="eyebrow">VERHALEN</p>
          <h1>{data.series.title}</h1>
          <p className="muted">
            Een doorlopend feuilleton uit {data.series.town}, geschreven op jouw niveau (
            {stageLabels[data.series.stage_id] ?? data.series.stage_id}). {read} van {data.items.length}{" "}
            afleveringen gelezen.
          </p>
        </div>
        <span className="quiet-badge">{data.series.episode_count} afleveringen</span>
      </header>
      {next && <EpisodeCard episode={next} cta="Lees de volgende aflevering" />}
      <section className="wish-card inline" aria-labelledby="library-wish">
        <h2 id="library-wish">Een nieuwe aflevering vragen</h2>
        <form
          onSubmit={(event) => {
            event.preventDefault();
            void request();
          }}
        >
          <label htmlFor="library-wish-input" className="visually-hidden">
            Onderwerp
          </label>
          <input
            id="library-wish-input"
            value={wish}
            onChange={(event) => setWish(event.target.value)}
            maxLength={120}
            placeholder="Laat leeg voor een verrassing, of geef een onderwerp"
          />
          <button className="button" type="submit" disabled={busy}>
            Schrijf een aflevering
          </button>
        </form>
        {notice && (
          <p className="practice-hint" role="status">
            <UiText text={notice} tier="guide" />
          </p>
        )}
      </section>
      <ol className="episode-grid">
        {data.items.map((item) => (
          <li key={item.id} className={`episode-tile status-${item.status} ${item.read_at ? "is-read" : ""}`}>
            <Cover number={item.number} />
            <div className="episode-tile-body">
              <p className="eyebrow">
                AFLEVERING {item.number} · {stageLabels[item.stage_id] ?? item.stage_id}
              </p>
              <h3>{item.status === "ready" ? item.title : item.theme}</h3>
              <p className="small-text muted">
                {item.status === "ready"
                  ? `${item.word_count} woorden · ${item.read_at ? "gelezen" : "nog niet gelezen"}${item.rating === 1 ? " · 👍" : item.rating === -1 ? " · 👎" : ""}`
                  : statusCopy[item.status]}
              </p>
              {developer && item.status === "failed" && item.failure_reasons?.length > 0 && (
                <details className="failure-details">
                  <summary>Wat er niet klopte</summary>
                  <ul>
                    {item.failure_reasons.map((reason) => (
                      <li key={reason}>
                        <code>{reason}</code>
                      </li>
                    ))}
                  </ul>
                </details>
              )}
              {item.status === "ready" ? (
                <Link className="stage-link" href={episodeHref(item.id)}>
                  {item.read_at ? "Lees opnieuw" : "Lees"}
                  <Icon name="arrow" size={17} />
                </Link>
              ) : item.status === "failed" ? (
                <button
                  className="linklike"
                  onClick={() =>
                    void stories
                      .retry(item.id)
                      .then(() => stories.library())
                      .then(setData)
                      .catch((cause) =>
                        setNotice(
                          errorCopy(cause, episodeCopy.retryFailed, {
                            paid_not_approved: uiCopy.failures.paidNotApproved,
                          }),
                        ),
                      )
                  }
                >
                  Opnieuw laten schrijven
                </button>
              ) : (
                <span className="writing-dots" data-anim="dots" aria-hidden="true">
                  <span />
                  <span />
                  <span />
                </span>
              )}
            </div>
          </li>
        ))}
      </ol>
      {data.items.length === 0 && (
        <EmptyState icon="book" accent="stories" title="Nog geen afleveringen">
          <p>
            Ga naar <Link href="/">Vandaag</Link>; daar start de eerste.
          </p>
        </EmptyState>
      )}
      <section className="cast-card" aria-labelledby="cast-title">
        <h2 id="cast-title">De personages</h2>
        <ul>
          {data.series.cast.map((person) => (
            <li key={person.name}>
              <strong>{person.name}</strong> <span className="muted">{person.role}</span>
            </li>
          ))}
        </ul>
      </section>
    </div>
  );
}
