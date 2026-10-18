"use client";

import { studyCopy, studyLabels, studyRoute } from "@/lib/copy/study";

import Link from "next/link";
import { Icon } from "@/components/Icon";
import { LearningText } from "@/components/LanguageSupport";
import { useProfile } from "@/lib/client/profile";
import { studyHref, studySkillCopy } from "@/lib/client/study";
import { isStageId, SKILLS, stageLabel, stageNames } from "@/lib/domain/registry";
import { useLastStudyStage } from "@/lib/client/study-stage";

export function StudyDashboard() {
  const profile = useProfile();
  const preferred = profile.data?.profile.stage_id;
  const lastStage = useLastStudyStage();
  const stage = lastStage ?? (preferred && isStageId(preferred) ? preferred : "pre-a1");
  return (
    <div className="study-dashboard" data-testid="study-dashboard">
      <section className="study-welcome">
        <div className="study-welcome-content">
          <p className="study-kicker">
            {" "}
            <LearningText text={studyCopy.dashboardKicker} />{" "}
          </p>
          <h1>
            <LearningText text={studyCopy.whatWouldYouLikeToSay} />
          </h1>
          <p className="study-lead">
            <LearningText text={studyCopy.chooseOneTopicLearnUsefulWords} />
          </p>
          <div className="study-hero-actions">
            <Link className="button" href={studyHref(stage)}>
              <LearningText text={studyLabels.continueAt(stageLabel(stage))} />
              <Icon name="arrow" size={18} />
            </Link>
            <Link className="button secondary" href="/leerpad">
              <LearningText text={studyCopy.chooseAnotherLevel} />
            </Link>
          </div>
        </div>
        <div className="study-welcome-note" aria-label={studyCopy.startingPoint.nl}>
          <span className="study-level-stamp">{stageLabel(stage)}</span>
          <strong>{stageNames[stage]}</strong>
          <span>
            {" "}
            <LearningText text={studyCopy.fourSkills} />{" "}
          </span>
          <p>
            <LearningText text={studyCopy.chooseWhereToBeginEveryLevel} />
          </p>
        </div>
      </section>
      <section className="study-route" aria-labelledby="study-route-title">
        <div className="study-section-heading">
          <div>
            <p className="study-kicker">
              {" "}
              <LearningText text={studyCopy.routeKicker} />{" "}
            </p>
            <h2 id="study-route-title">
              <LearningText text={studyCopy.aClearNextStepEveryTime} />
            </h2>
          </div>
        </div>
        <ol className="study-route-grid">
          {studyRoute.map((item, index) => (
            <li key={item.nl}>
              <span className="study-route-number">{index + 1}</span>
              <div>
                <strong>
                  <LearningText text={item} />
                </strong>
                <p>
                  <LearningText text={item.hint} />
                </p>
              </div>
            </li>
          ))}
        </ol>
      </section>
      <section aria-labelledby="study-skills-title">
        <div className="study-section-heading">
          <div>
            <p className="study-kicker">
              {" "}
              <LearningText text={studyCopy.skillKicker} />{" "}
            </p>
            <h2 id="study-skills-title">
              <LearningText text={studyLabels.practiseAt(stageLabel(stage))} />
            </h2>
          </div>
          <Link href="/leerpad">
            <LearningText text={studyCopy.allLevels} /> <Icon name="arrow" size={16} />
          </Link>
        </div>
        <div className="study-skill-grid">
          {SKILLS.map((skill) => (
            <Link key={skill} className="study-skill-card" href={studyHref(stage, skill)} data-skill={skill}>
              <span className="study-skill-icon">
                <Icon name={studySkillCopy[skill].icon} size={24} />
              </span>
              <h3>
                <LearningText text={studySkillCopy[skill].title} />
              </h3>
              <p>
                <LearningText text={studySkillCopy[skill].action} />
              </p>
              <span className="study-card-arrow">
                <Icon name="arrow" size={18} />
              </span>
            </Link>
          ))}
        </div>
      </section>
    </div>
  );
}
