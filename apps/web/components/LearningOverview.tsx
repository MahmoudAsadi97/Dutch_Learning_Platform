"use client";

import { useEffect, useState } from "react";
import Link from "next/link";

import { apiJson } from "@/lib/client/api";
import type { Skill, SkillRecordView } from "@/lib/types";

const SKILLS: { key: Skill; label: string; description: string }[] = [
  { key: "reading", label: "Lezen", description: "Begrijp de afspraak." },
  { key: "listening", label: "Luisteren", description: "Hoor wat er verandert." },
  { key: "speaking", label: "Spreken", description: "Spreek een nieuw moment af." },
  { key: "writing", label: "Schrijven", description: "Bevestig uw afspraak." },
];
const STATUS: Record<string, string> = {
  not_started: "Nog niet gestart", in_progress: "In oefening", practised: "Geoefend",
};

/** Shows real records, never an aggregate proficiency score or a simulated streak. */
export function LearningOverview() {
  const [records, setRecords] = useState<SkillRecordView[] | null>(null);
  const [error, setError] = useState(false);
  const [attempt, setAttempt] = useState(0);
  useEffect(() => {
    const controller = new AbortController();
    apiJson<{ skill_records: SkillRecordView[] }>("progress", { signal: controller.signal })
      .then((data) => {
        setRecords(data.skill_records.filter((record) => record.mission_id === "appointment-change"));
        setError(false);
      })
      .catch(() => { if (!controller.signal.aborted) setError(true); });
    return () => controller.abort();
  }, [attempt]);

  return (
    <section aria-labelledby="learning-overview-title" className="learning-overview">
      <div className="mission-hero">
        <span className="label warn">Oefenmissie · A2-doelen · niet nagekeken</span>
        <h2 id="learning-overview-title">Een afspraak verzetten</h2>
        <p>Lees, luister, oefen het gesprek en schrijf een kort bericht. Uw werk wordt per vaardigheid bewaard.</p>
        <p className="fa" lang="fa" dir="rtl">بخوانید، گوش دهید، مکالمه را تمرین کنید و یک پیام کوتاه بنویسید.</p>
        <div className="overview-actions">
          <Link className="button" href="/missions/appointment-change">Open de missie</Link>
          <Link className="button secondary" href="/speech-check">Test de microfoon</Link>
        </div>
      </div>
      <div className="skill-overview" data-testid="learning-overview">
        {SKILLS.map(({ key, label, description }) => {
          const record = records?.find((item) => item.skill === key);
          return (
            <article className="card" key={key} aria-label={label}>
              <h3>{label}</h3>
              <p className="muted">{description}</p>
              <p>{error ? "Status niet beschikbaar" : records === null ? "Laden…" : STATUS[record?.status ?? "not_started"] ?? "Oefenrecord beschikbaar"}</p>
              {record && <small className="muted">{record.evidence_ids.length} gekoppelde bewijsstukken</small>}
            </article>
          );
        })}
      </div>
      {error && (
        <p role="alert">Voortgang kon niet worden geladen. <button className="button secondary" onClick={() => setAttempt((value) => value + 1)}>Opnieuw laden</button></p>
      )}
      <p className="muted">Oefenrecords zijn geen niveaucertificaat. Getypte gesprekken tellen niet als gesproken bewijs.</p>
    </section>
  );
}
