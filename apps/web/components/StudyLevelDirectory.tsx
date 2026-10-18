"use client";

import { studyCopy, studyStageDescriptions } from "@/lib/copy/study";

import Link from "next/link";
import { Icon } from "@/components/Icon";
import { LearningText } from "@/components/LanguageSupport";
import { SKILLS, STAGE_IDS, stageLabel, stageNames } from "@/lib/domain/registry";
import { studyHref, studySkillCopy } from "@/lib/client/study";
import { useProfile } from "@/lib/client/profile";
import { useState } from "react";
import { PracticeCoach } from "@/components/PracticeCoach";

export function StudyLevelDirectory() {
  const profile = useProfile();
  const [coachOpen, setCoachOpen] = useState(false);
  return (
    <div className="study-directory" data-testid="learning-overview">
      <header className="study-page-heading">
        <p className="study-kicker">
          {" "}
          <LearningText text={studyCopy.directoryKicker} />{" "}
        </p>
        <h1>
          <LearningText text={studyCopy.chooseYourLevel} />
        </h1>
        <p>
          <LearningText text={studyCopy.everyLevelHasTheSameFour} />
        </p>
      </header>
      <ol className="study-level-grid" data-testid="curriculum-path">
        {STAGE_IDS.map((stage, index) => (
          <li
            key={stage}
            className={`study-level-card ${profile.data?.profile.stage_id === stage ? "is-preferred" : ""}`}
          >
            <div className="study-level-top">
              <span className="study-stage-code">{stageLabel(stage)}</span>
              <span className="study-level-order">{String(index + 1).padStart(2, "0")}</span>
            </div>
            <h2>
              <Link href={studyHref(stage)}>{stageNames[stage]}</Link>
            </h2>
            <p>
              <LearningText text={studyStageDescriptions[stage]} />
            </p>
            <div className="study-level-skills">
              {SKILLS.map((skill) => (
                <Link
                  key={skill}
                  href={studyHref(stage, skill)}
                  aria-label={`${stageLabel(stage)} · ${studySkillCopy[skill].title.nl}`}
                >
                  <Icon name={studySkillCopy[skill].icon} size={17} />
                  <span>{studySkillCopy[skill].title.nl}</span>
                </Link>
              ))}
            </div>
          </li>
        ))}
      </ol>
      <details className="directory-coach" onToggle={(event) => setCoachOpen(event.currentTarget.open)}>
        <summary>
          <LearningText text={studyCopy.optionalCoach} />
        </summary>
        {coachOpen && <PracticeCoach />}
      </details>
      <p className="study-footnote">
        <LearningText text={studyCopy.thePreLevelsAreBridgeStages} />
      </p>
    </div>
  );
}
