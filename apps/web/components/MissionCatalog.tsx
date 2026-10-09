"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { apiJson } from "@/lib/client/api";
import { LearningText } from "@/components/LanguageSupport";
import { Icon } from "@/components/Icon";
import { UiText } from "@/components/ui/UiText";
import { missionsCopy } from "@/lib/copy/missions";
import type { MissionResponse } from "@/lib/types";
import { fill, uiCopy } from "@/lib/ui-copy";

export function MissionCatalog() {
  const [missions, setMissions] = useState<MissionResponse[] | null>(null);
  const [failed, setFailed] = useState(false);
  const [attempt, setAttempt] = useState(0);
  useEffect(() => {
    const controller = new AbortController();
    apiJson<{ missions: MissionResponse[] }>("missions", { signal: controller.signal })
      .then((result) => setMissions(result.missions))
      .catch(() => {
        if (!controller.signal.aborted) setFailed(true);
      });
    return () => controller.abort();
  }, [attempt]);
  return (
    <section aria-labelledby="catalog-title" id="oefeningen">
      <div className="section-heading">
        <div>
          <p className="eyebrow">
            <UiText text={missionsCopy.catalogEyebrow} />
          </p>
          <h2 id="catalog-title">
            <UiText text={missionsCopy.catalogTitle} />
          </h2>
          <p className="muted">
            <UiText text={missionsCopy.catalogIntro} tier="guide" />
          </p>
        </div>
      </div>
      {failed ? (
        <p role="alert">
          <UiText text={missionsCopy.catalogFailed} tier="guide" inline />{" "}
          <button
            className="linklike"
            onClick={() => {
              setFailed(false);
              setAttempt((n) => n + 1);
            }}
          >
            <UiText text={uiCopy.action.retry} inline />
          </button>
        </p>
      ) : missions === null ? (
        <p role="status">
          <UiText text={missionsCopy.catalogLoading} />
        </p>
      ) : missions.length === 0 ? (
        <p>
          <UiText text={missionsCopy.catalogEmpty} tier="guide" />
        </p>
      ) : (
        <div className="mission-catalog" data-testid="mission-catalog">
          {missions.map((mission) => (
            <article className="card catalog-card" key={mission.id}>
              <span className="quiet-badge">
                <UiText text={fill(missionsCopy.catalogBadge, { level: mission.cefr_target })} inline />
              </span>
              <h3>
                <LearningText text={mission.title} />
              </h3>
              <p>
                <LearningText text={mission.description} />
              </p>
              <Link className="button secondary" href={`/missions/${mission.id}`}>
                <UiText
                  text={fill(missionsCopy.catalogPractise, { title: mission.title.nl.toLowerCase() })}
                  inline
                />{" "}
                <Icon name="arrow" size={16} />
              </Link>
            </article>
          ))}
        </div>
      )}
    </section>
  );
}
