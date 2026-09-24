"use client";

import Link from "next/link";
import { useState } from "react";
import { Icon } from "@/components/Icon";
import { skills } from "@/components/LearningOverview";
import {
  localDate,
  recordStatus,
  sessionStatus,
  useLearningData,
} from "@/lib/client/learning";

export function ProgressOverview() {
  const { data, error, retry } = useLearningData();
  const [missionId, setMissionId] = useState("appointment-change");
  return (
    <>
      <header className="page-heading">
        <div>
          <p className="eyebrow">ZICHT OP JE LEERPROCES</p>
          <h1>Elke stap vertelt iets.</h1>
          <p>
            Vier vaardigheden. Je eigen tempo. Geen cijfer dat alles samenvat.
          </p>
        </div>
        <Link className="button secondary" href={`/missions/${missionId}`}>
          Verder oefenen <Icon name="arrow" size={17} />
        </Link>
      </header>
      {error ? (
        <div className="error" role="alert">
          Voortgang is tijdelijk niet beschikbaar.{" "}
          <button className="linklike" onClick={retry}>
            Opnieuw proberen
          </button>
        </div>
      ) : !data ? (
        <div className="card" role="status">
          Je oefenrecords laden…
        </div>
      ) : (
        <>
          <label className="card" style={{ display: "block", marginBottom: "1rem" }}>
            Voortgang per oefenmissie{" "}
            <select aria-label="Oefenmissie" value={missionId} onChange={event => setMissionId(event.target.value)}>
              {data.missions.map(mission => <option key={mission.id} value={mission.id}>{mission.title.nl}</option>)}
            </select>
          </label>
          <div className="progress-grid">
            {skills.map(({ key, label, icon, color, description }) => {
              const record = data.skill_records.find(
                (item) =>
                  item.skill === key &&
                  item.mission_id === missionId,
              );
              return (
                <section className="progress-card" key={key} aria-label={label}>
                  <div className="section-heading">
                    <span className={`icon-tile ${color}`}>
                      <Icon name={icon} size={25} />
                    </span>
                    <span
                      className={`label ${record?.status === "practised" ? "ok" : "neutral"}`}
                    >
                      {recordStatus[record?.status ?? "not_started"]}
                    </span>
                  </div>
                  <h2>{label}</h2>
                  <p className="muted">{description}</p>
                  <dl className="record-facts">
                    <div>
                      <dt>Oefenpogingen</dt>
                      <dd>{record?.attempts ?? 0}</dd>
                    </div>
                    <div>
                      <dt>Laatst bijgewerkt</dt>
                      <dd>
                        {record
                          ? localDate(record.updated_at)
                          : "Nog niet gestart"}
                      </dd>
                    </div>
                  </dl>
                  <p className="record-note">
                    {key === "speaking"
                      ? "Getypte antwoorden zijn geen bewijs van gesproken vaardigheid."
                      : "Geoefend betekent niet automatisch zelfstandig beheerst."}
                  </p>
                </section>
              );
            })}
          </div>
          <section className="card session-history">
            <div className="section-heading">
              <h2>Oefengeschiedenis</h2>
              <span className="quiet-badge">
                {data.sessions.length} sessies
              </span>
            </div>
            {data.sessions.length === 0 ? (
              <p className="muted">
                Je geschiedenis verschijnt zodra je een oefensessie start.
              </p>
            ) : (
              <ul className="activity-list">
                {data.sessions.map((session) => (
                  <li key={session.id}>
                    <span className="icon-tile small sage">
                      <Icon
                        name={
                          session.variant === "transfer" ? "shield" : "calendar"
                        }
                        size={18}
                      />
                    </span>
                    <div>
                      <strong>
                        {session.variant === "transfer"
                          ? "Zelfstandig toepassen"
                          : data.missions.find(m => m.id === session.mission_id)?.title.nl ?? "Oefenmissie"}
                      </strong>
                      <span>
                        {localDate(session.updated_at)} · {session.turn_count}{" "}
                        gespreksbeurten
                      </span>
                    </div>
                    <span className="activity-status">
                      {sessionStatus[session.status]}
                    </span>
                  </li>
                ))}
              </ul>
            )}
          </section>
        </>
      )}
      <aside className="information-callout">
        <Icon name="shield" size={22} />
        <div>
          <h3>Je groei is meer dan een score.</h3>
          <p>
            Deze records beschrijven je oefeningen, geen gevalideerd
            CEFR-niveau. Hulp en zelfstandig werk worden afzonderlijk
            vastgelegd. Feedback is automatisch en kan fouten bevatten.
          </p>
        </div>
      </aside>
    </>
  );
}
