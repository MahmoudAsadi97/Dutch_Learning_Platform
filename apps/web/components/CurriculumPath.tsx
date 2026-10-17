"use client";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { PracticeCoach } from "@/components/PracticeCoach";
import { ContentCoverage } from "@/components/ContentCoverage";
import { Icon } from "@/components/Icon";
import { LearningText } from "@/components/LanguageSupport";
import { apiJson } from "@/lib/client/api";
import { stageLabel, type CurriculumCatalog } from "@/lib/client/curriculum";
import { STAGE_IDS, stageNames, isStageId } from "@/lib/domain/registry";
import { activityHref, type LearningActivity } from "@/lib/client/learning-navigation";
import { workspaceCopy as copy } from "@/lib/copy/workspace";
import { Skeleton, SkeletonPanel, SkillMeter } from "@/components/ui";
import { useProfile } from "@/lib/client/profile";
import { HonestyChip } from "@/components/ui/HonestyChip";
import { fill } from "@/lib/ui-copy";

const activities: { id: LearningActivity; icon: "book" | "headphones" | "mic" | "pen" | "star" }[] = [
  { id: "reading", icon: "book" },
  { id: "listening", icon: "headphones" },
  { id: "speaking", icon: "mic" },
  { id: "writing", icon: "pen" },
  { id: "words", icon: "star" },
  { id: "grammar", icon: "pen" },
  { id: "stories", icon: "book" },
];
export function CurriculumPath() {
  const [data, setData] = useState<CurriculumCatalog | null>(null);
  const [error, setError] = useState(false);
  const [retry, setRetry] = useState(0);
  const profile = useProfile();
  const router = useRouter();
  useEffect(() => {
    const controller = new AbortController();
    apiJson<CurriculumCatalog>("curriculum", { signal: controller.signal })
      .then((value) => {
        setData(value);
        setError(false);
      })
      .catch((cause) => {
        if (cause?.name !== "AbortError") setError(true);
      });
    return () => controller.abort();
  }, [retry]);
  const current = profile.data?.profile.stage_id;
  const next = data?.stages.find((s) => s.id === current) ?? data?.stages[0];
  return (
    <div className="learning-path level-directory" data-testid="learning-overview">
      <header className="path-heading">
        <div>
          <h1>
            <LearningText text={copy.title} />
          </h1>
          <p>
            <LearningText text={copy.intro} />
          </p>
          <div className="directory-quick-level">
            <label htmlFor="directory-stage">
              <LearningText text={copy.level} />
            </label>
            <select
              id="directory-stage"
              value={current ?? "pre-a1"}
              onChange={(event) => router.push(activityHref(event.target.value, "words"))}
            >
              {STAGE_IDS.map((id) => (
                <option value={id} key={id}>
                  {stageLabel(id)} · {stageNames[id]}
                </option>
              ))}
            </select>
          </div>
        </div>
      </header>
      {error ? (
        <div className="error" role="alert">
          <p>Je leerpad kon niet worden geladen.</p>
          <button className="button secondary" onClick={() => setRetry((v) => v + 1)}>
            Opnieuw proberen
          </button>
        </div>
      ) : !data ? (
        <SkeletonPanel label="Je leerpad laden…">
          <Skeleton lines={3} />
        </SkeletonPanel>
      ) : (
        <>
          {next && (
            <div className="level-resume">
              <span>
                <LearningText text={copy.resume} />: <strong>{stageLabel(next.id)}</strong>
              </span>
              <Link className="button" href={`/learn/${next.id}`}>
                <LearningText text={copy.resume} />
                <Icon name="arrow" size={18} />
              </Link>
            </div>
          )}
          <ol className="stage-grid" data-testid="curriculum-path">
            {data.stages.map((stage) => (
              <li key={stage.id} className={`stage-card ${stage.id === next?.id ? "stage-current" : ""}`}>
                <div className="stage-card-top">
                  <span className="stage-level">{stageLabel(stage.id)}</span>
                  <span className="stage-status">
                    {stage.passed ? <Icon name="check" size={16} /> : null}
                    {stage.passed ? "Afgerond" : "Beschikbaar"}
                  </span>
                </div>
                <h2>{isStageId(stage.id) ? stageNames[stage.id] : stageLabel(stage.id)}</h2>
                <ContentCoverage coverage={stage.coverage} compact />
                <div className="stage-activity-grid">
                  {activities.map((item) => (
                    <Link key={item.id} href={activityHref(stage.id, item.id)}>
                      <Icon name={item.icon} size={17} />
                      <LearningText text={copy[item.id]} />
                      {["reading", "listening", "speaking", "writing"].includes(item.id) && stage.coverage ? (
                        <small>{stage.coverage.skill_topics[item.id as "reading"]}</small>
                      ) : null}
                    </Link>
                  ))}
                </div>
                {stage.id === "pre-a1" && (
                  <Link className="alphabet-entry" href={activityHref(stage.id, "alphabet")}>
                    <Icon name="volume" size={16} />
                    <LearningText text={copy.alphabet} />
                  </Link>
                )}
                <ContentCoverage coverage={stage.coverage} />
                <SkillMeter
                  done={Object.fromEntries(stage.practice_completed.map((skill) => [skill, true]))}
                  label={`Vaardigheden van ${stageLabel(stage.id)}`}
                />
                <p className="stage-practice-status">
                  <LearningText text={fill(copy.practiced, { n: stage.practice_completed.length })} />
                </p>
                <Link
                  className="stage-link"
                  href={`/learn/${stage.id}`}
                  aria-label={`Open ${stageLabel(stage.id)}: ${stage.title.nl}`}
                >
                  Open dit niveau
                  <Icon name="arrow" size={17} />
                </Link>
              </li>
            ))}
          </ol>
          <details className="directory-coach">
            <summary>
              <LearningText text={copy.coach} />
            </summary>
            <PracticeCoach key={data.learner_key} />
          </details>
          <div className="honesty-row">
            <HonestyChip kind="check" />
          </div>
        </>
      )}
    </div>
  );
}
