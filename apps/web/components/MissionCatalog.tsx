"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { apiJson } from "@/lib/client/api";
import { LearningText } from "@/components/LanguageSupport";
import { Icon } from "@/components/Icon";
import type { MissionResponse } from "@/lib/types";

export function MissionCatalog() {
  const [missions, setMissions] = useState<MissionResponse[] | null>(null);
  const [failed, setFailed] = useState(false);
  const [attempt, setAttempt] = useState(0);
  useEffect(() => {
    const controller = new AbortController();
    apiJson<{ missions: MissionResponse[] }>("missions", { signal: controller.signal })
      .then(result => setMissions(result.missions))
      .catch(() => { if (!controller.signal.aborted) setFailed(true); });
    return () => controller.abort();
  }, [attempt]);
  return (
    <section aria-labelledby="catalog-title" id="oefeningen">
      <div className="section-heading">
        <div>
          <p className="eyebrow">NEDERLANDS IN HET DAGELIJKS LEVEN</p>
          <h2 id="catalog-title">Wat wilt u vandaag oefenen?</h2>
          <p className="muted">Elke missie combineert lezen, luisteren, spreken en schrijven.</p>
        </div>
      </div>
      {failed ? <p role="alert">De oefeningen konden niet worden geladen. <button className="linklike" onClick={() => { setFailed(false); setAttempt(n => n + 1); }}>Opnieuw proberen</button></p>
        : missions === null ? <p role="status">Oefeningen laden…</p>
        : missions.length === 0 ? <p>Er zijn nog geen oefeningen beschikbaar.</p>
        : <div className="mission-catalog" data-testid="mission-catalog">
          {missions.map(mission => (
            <article className="card catalog-card" key={mission.id}>
              <span className="quiet-badge">{mission.cefr_target}-oefendoelen · 4 vaardigheden</span>
              <h3><LearningText text={mission.title} /></h3>
              <p><LearningText text={mission.description} /></p>
              <Link className="button secondary" href={`/missions/${mission.id}`}>Oefen {mission.title.nl.toLowerCase()} <Icon name="arrow" size={16} /></Link>
            </article>
          ))}
        </div>}
    </section>
  );
}
