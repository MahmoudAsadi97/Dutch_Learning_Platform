"use client";

import { useEffect, useState } from "react";

import { Illustration } from "@/components/illustrations";
import { ButtonLink } from "@/components/ui/Button";
import { UiText } from "@/components/ui/UiText";
import { episodeHref, stories, type EpisodeStatus } from "@/lib/client/stories";
import { fill, uiCopy } from "@/lib/ui-copy";

const POLL_MS = 5000;
/** Four minutes: a local model writes an episode in one to three. */
const POLL_LIMIT = 48;

export interface QueuedEpisode {
  id: string;
  number: number;
  status: string;
}

/**
 * The first episode, written while the learner practises. It reads the episode without changing it and
 * says plainly when writing failed, instead of spinning: Vandaag offers the retry.
 */
export function WritingProgress({ episode }: { episode: QueuedEpisode | null }) {
  const [status, setStatus] = useState<EpisodeStatus | "unknown">(
    (episode?.status as EpisodeStatus | undefined) ?? "unknown",
  );
  const [polls, setPolls] = useState(0);
  const waiting = status === "queued" || status === "generating";
  useEffect(() => {
    if (!episode || !waiting || polls >= POLL_LIMIT) return;
    const controller = new AbortController();
    const timer = setTimeout(() => {
      stories
        .episode(episode.id, controller.signal)
        .then((value) => setStatus(value.status))
        .catch(() => undefined)
        .finally(() => setPolls((count) => count + 1));
    }, POLL_MS);
    return () => {
      clearTimeout(timer);
      controller.abort();
    };
  }, [episode, waiting, polls]);

  if (!episode) {
    return (
      <p className="writing-progress" role="status">
        <UiText text={uiCopy.welcome.writerLater} tier="always" />
      </p>
    );
  }
  const values = { number: episode.number };
  return (
    <div className="writing-progress" data-state={status} data-testid="writing-progress">
      <span data-accent="stories">
        <Illustration name="writer" size={56} />
      </span>
      <div>
        <p role="status">
          {status === "queued" && <UiText text={uiCopy.welcome.writerQueued} tier="always" />}
          {(status === "generating" || status === "unknown") && (
            <UiText text={fill(uiCopy.welcome.writerBusy, values)} tier="always" />
          )}
          {status === "ready" && <UiText text={fill(uiCopy.welcome.writerReady, values)} tier="always" />}
          {status === "failed" && <UiText text={uiCopy.welcome.writerFailed} tier="always" />}
        </p>
        {waiting && (
          <span className="writing-dots" data-anim="dots" aria-hidden="true">
            <span />
            <span />
            <span />
          </span>
        )}
        {status === "ready" && (
          <ButtonLink href={episodeHref(episode.id)} variant="secondary" size="small" icon="book">
            <UiText text={fill(uiCopy.welcome.writerRead, values)} inline />
          </ButtonLink>
        )}
      </div>
    </div>
  );
}
