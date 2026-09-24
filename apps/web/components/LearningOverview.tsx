"use client";

import Link from "next/link";
import { MissionCatalog } from "@/components/MissionCatalog";
import { Icon, type IconName } from "@/components/Icon";
import {
  localDate,
  recordStatus,
  sessionStatus,
  useLearningData,
} from "@/lib/client/learning";
import type { Skill } from "@/lib/types";

export const skills: {
  key: Skill;
  label: string;
  description: string;
  icon: IconName;
  color: string;
}[] = [
  {
    key: "reading",
    label: "Lezen",
    description: "Begrijp wat er staat.",
    icon: "book",
    color: "sage",
  },
  {
    key: "listening",
    label: "Luisteren",
    description: "Hoor wat ertoe doet.",
    icon: "headphones",
    color: "sand",
  },
  {
    key: "speaking",
    label: "Spreken",
    description: "Vind de juiste woorden.",
    icon: "mic",
    color: "lilac",
  },
  {
    key: "writing",
    label: "Schrijven",
    description: "Maak je boodschap duidelijk.",
    icon: "pen",
    color: "peach",
  },
];

function MissionArtwork() {
  return (
    <div className="mission-art" aria-hidden="true">
      <div className="art-orbit orbit-one" />
      <div className="art-orbit orbit-two" />
      <span className="art-spark spark-one">✳</span>
      <span className="art-spark spark-two">+</span>
      <div className="art-card">
        <div className="art-card-top">
          <span>AFSPRAAK</span>
          <Icon name="calendar" size={20} />
        </div>
        <div className="art-date">
          <span>Een nieuw</span>
          <strong>moment.</strong>
        </div>
        <div className="art-calendar">
          {Array.from({ length: 15 }, (_, i) => (
            <span key={i} className={i === 8 ? "chosen" : ""}>
              {i === 8 ? <Icon name="check" size={14} /> : ""}
            </span>
          ))}
        </div>
        <div className="art-line" />
        <div className="art-line short" />
      </div>
      <div className="art-message">
        <span className="art-message-icon">
          <Icon name="check" size={16} />
        </span>
        Dat past voor mij!
      </div>
    </div>
  );
}

export function LearningOverview() {
  const { data, error, retry } = useLearningData();
  const records = data?.skill_records.filter(
    (record) => record.mission_id === "appointment-change",
  );
  const latest = data?.sessions.find((session) => session.variant === "base" && session.mission_id === "appointment-change");
  const stepCount =
    data?.mission.steps.filter((step) => step.variant === "base").length ?? 4;
  const completed = latest
    ? Object.values(latest.step_progress).filter((step) => step.completed)
        .length
    : 0;
  const recent = data?.sessions.slice(0, 3) ?? [];
  return (
    <div className="dashboard">
      <header className="page-heading">
        <div>
          <p className="eyebrow">JOUW NEDERLANDS, ELKE DAG</p>
          <h1>Kleine stappen. Echte gesprekken.</h1>
          <p>Een plek om te proberen, te oefenen en verder te groeien.</p>
        </div>
        <span className="quiet-badge">
          <Icon name="globe" size={15} /> Belgische context
        </span>
      </header>
      {error && (
        <div className="error" role="alert">
          Je voortgang kon niet worden geladen.{" "}
          <button className="linklike" onClick={retry}>
            Opnieuw proberen
          </button>
        </div>
      )}
      <MissionCatalog />
      <div className="dashboard-top">
        <section className="mission-hero" aria-labelledby="mission-title">
          <div className="mission-copy">
            <span className="hero-eyebrow">
              <span className="live-dot" /> JOUW OEFENMISSIE{" "}
              <span className="hero-level">A2-doelen</span>
            </span>
            <h2 id="mission-title">
              Een afspraak
              <br />
              verzetten.
            </h2>
            <p>
              Er komt iets tussen. Lees het bericht, bespreek een nieuw moment
              en bevestig je afspraak.
            </p>
            <div className="hero-meta">
              <span>
                <Icon name="clock" size={15} /> Op jouw tempo
              </span>
              <span>4 vaardigheden</span>
            </div>
            <Link
              href="/missions/appointment-change"
              className="button light"
              aria-label="Open de missie"
            >
              {latest ? "Verder met de missie" : "Begin met oefenen"}
              <Icon name="arrow" size={19} />
            </Link>
          </div>
          <MissionArtwork />
          <div className="hero-foot">
            <span>
              {error
                ? "Voortgang niet beschikbaar"
                : !data
                  ? "Voortgang laden…"
                  : `${completed} van ${stepCount} oefenstappen afgerond`}
            </span>
            <div className="step-segments" aria-hidden="true">
              {Array.from({ length: stepCount }, (_, i) => (
                <span key={i} className={data && i < completed ? "done" : ""} />
              ))}
            </div>
          </div>
        </section>
        <aside className="focus-card">
          <span className="icon-tile sand">
            <Icon name="help" size={23} />
          </span>
          <p className="eyebrow">JE HOEFT HET NIET ALLEEN TE DOEN</p>
          <h2>
            Even vast?{" "}
            <br />
            Begin met een hint.
          </h2>
          <p>
            Eerst een duwtje in het Nederlands. Daarna uitleg in het Perzisch,
            als je die nodig hebt.
          </p>
          <p className="fa focus-persian" lang="fa" dir="rtl">
            قدم‌به‌قدم پیش برو.
            <br />
            اگر لازم شد، راهنمایی بگیر.
          </p>
          <div className="focus-note">
            <Icon name="shield" size={17} />
            <span>Hulpgebruik wordt apart bijgehouden.</span>
          </div>
        </aside>
      </div>
      <section aria-labelledby="skills-title">
        <div className="section-heading">
          <div>
            <p className="eyebrow">VIER MANIEREN OM TE GROEIEN</p>
            <h2 id="skills-title">Jouw vaardigheden</h2>
          </div>
          <Link className="text-link" href="/progress">
            Bekijk je voortgang <Icon name="arrow" size={16} />
          </Link>
        </div>
        <div className="skill-overview" data-testid="learning-overview">
          {skills.map(({ key, label, description, icon, color }, index) => {
            const record = records?.find((item) => item.skill === key);
            return (
              <article className="skill-card" aria-label={label} key={key}>
                <div className="skill-card-top">
                  <span className={`icon-tile ${color}`}>
                    <Icon name={icon} size={23} />
                  </span>
                  <span className="skill-index">0{index + 1}</span>
                </div>
                <h3>{label}</h3>
                <p>{description}</p>
                <div className="skill-card-bottom">
                  <span
                    className={`status-dot ${record?.status === "practised" ? "done" : ""}`}
                  />
                  <span>
                    {error
                      ? "Niet beschikbaar"
                      : !data
                        ? "Laden…"
                        : (recordStatus[record?.status ?? "not_started"] ??
                          "Oefenrecord")}
                  </span>
                </div>
              </article>
            );
          })}
        </div>
      </section>
      <div className="dashboard-bottom">
        <section className="activity-card">
          <div className="section-heading">
            <h2>Je laatste stappen</h2>
            <Icon name="clock" size={19} />
          </div>
          {error ? (
            <p className="muted">Activiteit is tijdelijk niet beschikbaar.</p>
          ) : !data ? (
            <p role="status">Activiteit laden…</p>
          ) : recent.length === 0 ? (
            <div className="empty-state compact">
              <span className="icon-tile sage">
                <Icon name="book" />
              </span>
              <div>
                <h3>Je eerste stap begint hier.</h3>
                <p>Na je eerste oefening vind je hier je activiteit terug.</p>
              </div>
            </div>
          ) : (
            <ul className="activity-list">
              {recent.map((session) => (
                <li key={session.id}>
                  <span
                    className={`icon-tile small ${session.variant === "transfer" ? "lilac" : "sage"}`}
                  >
                    <Icon
                      name={session.variant === "transfer" ? "shield" : "book"}
                      size={18}
                    />
                  </span>
                  <div>
                    <strong>
                      {session.variant === "transfer"
                        ? "Zelfstandig toepassen"
                        : data?.missions.find(m => m.id === session.mission_id)?.title.nl ?? "Oefenmissie"}
                    </strong>
                    <span>
                      {localDate(session.updated_at)}
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
        <Link href="/speech-check" className="studio-card">
          <span className="icon-tile lilac">
            <Icon name="mic" size={23} />
          </span>
          <div>
            <p className="eyebrow">KLAAR OM TE SPREKEN?</p>
            <h2>
              Geef je Nederlands{" "}
              <br />
              een stem.
            </h2>
            <p>Test je microfoon en luister naar een voorbeeld.</p>
          </div>
          <span className="circle-arrow">
            <Icon name="arrow" />
          </span>
        </Link>
      </div>
      <p className="integrity-note">
        <Icon name="shield" size={16} /> Oefenrecords zijn geen
        niveaucertificaat. Lesinhoud{" "}
        {data?.mission.review.unreviewed === 0
          ? "nagekeken"
          : "nog niet nagekeken"}
        . Getypte gesprekken tellen niet als gesproken bewijs.
      </p>
    </div>
  );
}
