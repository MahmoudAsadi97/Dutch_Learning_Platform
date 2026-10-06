"use client";

import Link from "next/link";
import { LearningText } from "@/components/LanguageSupport";
import { useCurriculumCatalog } from "@/lib/client/queries/curriculum";
import {
  skillNames,
  skillOrder,
  stageLabel,
  type CurriculumCatalog,
  type SkillResult,
  type StageSummary,
} from "@/lib/client/curriculum";
import type { Skill } from "@/lib/types";

type ProgressStage = StageSummary & {
  latest_check?: { status: string; results: Partial<Record<Skill, SkillResult>> } | null;
};
type PathProgress = Omit<CurriculumCatalog, "stages"> & { stages: ProgressStage[] };

export function CurriculumProgress() {
  const { data, error: failure, refetch } = useCurriculumCatalog<PathProgress>();
  const error = Boolean(failure);
  return (
    <section className="course-progress" aria-labelledby="course-progress-title">
      <header className="page-heading">
        <div>
          <p className="eyebrow">JOUW LEERPAD</p>
          <h1 id="course-progress-title">Elke stap vertelt iets.</h1>
          <p>
            <LearningText
              text={{
                nl: "Volg elke vaardigheid apart. Oefenen en slagen voor een toets zijn verschillende stappen.",
                en: "Track each skill separately. Practising and passing a check are different steps.",
                fa: "هر مهارت را جداگانه دنبال کن. تمرین کردن و قبولی در آزمون دو مرحلهٔ متفاوت‌اند.",
              }}
            />
          </p>
        </div>
        <Link className="button secondary" href="/leerpad">
          Terug naar je leerpad
        </Link>
      </header>
      {error ? (
        <p role="alert">
          Je voortgang kon niet worden geladen.{" "}
          <button className="linklike" onClick={() => void refetch()}>
            Opnieuw proberen
          </button>
        </p>
      ) : !data ? (
        <p role="status">Je voortgang laden…</p>
      ) : (
        <div className="course-progress-list">
          {data.stages.map((stage) => (
            <article className="card course-progress-row" key={stage.id}>
              <div className="section-heading">
                <div>
                  <span className="stage-level">{stageLabel(stage.id)}</span>
                  <h2>
                    <LearningText text={stage.title} />
                  </h2>
                </div>
                {stage.passed ? (
                  <span className="label ok">Eindtoets afgerond</span>
                ) : (
                  <Link href={`/learn/${stage.id}`} className="linklike">
                    Verder oefenen
                  </Link>
                )}
              </div>
              <dl className="course-skill-status">
                {skillOrder.map((skill) => {
                  const result = stage.latest_check?.results[skill];
                  return (
                    <div key={skill}>
                      <dt>{skillNames[skill]}</dt>
                      <dd>
                        {result
                          ? result.passed
                            ? "Toets: geslaagd"
                            : "Toets: verder oefenen"
                          : stage.practice_completed.includes(skill)
                            ? "Geoefend · nog niet getoetst"
                            : "Nog niet geoefend"}
                      </dd>
                    </div>
                  );
                })}
              </dl>
              {stage.latest_check && (
                <details>
                  <summary>Feedback op je laatste toets</summary>
                  {skillOrder.map((skill) => {
                    const result = stage.latest_check?.results[skill];
                    return result ? (
                      <section key={skill}>
                        <h3>{skillNames[skill]}</h3>
                        <p>
                          <LearningText text={result.feedback} />
                        </p>
                      </section>
                    ) : null;
                  })}
                </details>
              )}
            </article>
          ))}
        </div>
      )}
    </section>
  );
}
