"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Icon } from "@/components/Icon";
import { LearningText } from "@/components/LanguageSupport";
import { SpokenText } from "@/components/SpokenPassage";
import { apiJson } from "@/lib/client/api";
import { friendlyError } from "@/lib/client/curriculum";
import { useNavigationCheck } from "@/lib/client/navigation";
import { studyHref, studySkillCopy, type StudyLesson, type StudyStep } from "@/lib/client/study";
import { stageLabel, type Skill } from "@/lib/domain/registry";
import { studyCopy, studyLabels, studySteps } from "@/lib/copy/study";
import { CompactWords, StudyError } from "./StudyShared";
import { PracticePart } from "./StudyPracticePart";
import { StudyActivityPicker } from "./StudyActivityPicker";

export function GuidedLesson({
  stageId,
  skill,
  topicId,
  activityId,
  initialStep,
  initialPart,
}: {
  stageId: string;
  skill: Skill;
  topicId: string;
  activityId?: string;
  initialStep: StudyStep;
  initialPart?: string;
}) {
  const router = useRouter();
  const canLeave = useNavigationCheck();
  const [lesson, setLesson] = useState<StudyLesson | null>(null);
  const step = initialStep;
  const partId = initialPart ?? "";
  const [error, setError] = useState("");
  const [retry, setRetry] = useState(0);
  const [assisted, setAssisted] = useState(false);
  const [reference, setReference] = useState(false);
  const part = lesson?.parts.find((item) => item.id === partId) ?? lesson?.parts[0];
  useEffect(() => {
    const controller = new AbortController();
    apiJson<StudyLesson>(
      `study/${stageId}/topics/${topicId}?${new URLSearchParams({ skill, ...(activityId ? { activity_id: activityId } : {}) })}`,
      { signal: controller.signal },
    )
      .then((value) => {
        setLesson(value);
        setError("");
      })
      .catch((cause) => {
        if (cause?.name !== "AbortError") setError(friendlyError(cause, "load"));
      });
    return () => controller.abort();
  }, [stageId, skill, topicId, activityId, retry]);
  async function navigate(nextStep: StudyStep, nextPart = part?.id ?? "") {
    const href = studyHref(stageId, skill, {
      topic: topicId,
      activity: lesson?.activity_id,
      step: nextStep,
      part: nextPart,
    });
    if (await canLeave()) router.push(href, { scroll: false });
  }
  if (error) return <StudyError message={error} retry={() => setRetry((value) => value + 1)} />;
  if (!lesson || !part)
    return (
      <div className="study-loading" role="status">
        <LearningText text={studyCopy.loadingLesson} />{" "}
      </div>
    );
  return (
    <section className="study-lesson" data-testid="guided-lesson">
      <header className="study-lesson-heading">
        <div>
          <p className="study-kicker">
            {stageLabel(stageId)} · {studySkillCopy[skill].title.nl}
            {lesson.topic_title && (
              <>
                {" "}
                · <LearningText text={lesson.topic_title} />
              </>
            )}
          </p>
          <h1>
            <LearningText text={lesson.title} />
          </h1>
        </div>
        <span className="study-review-note">
          {" "}
          <LearningText text={studyCopy.reviewPending} />{" "}
        </span>
      </header>
      {lesson.activities.length > 1 && skill === "reading" ? (
        <StudyActivityPicker
          key={lesson.activity_id}
          activities={lesson.activities}
          selected={lesson.activity_id}
          onChoose={async (nextActivity) => {
            if (!(await canLeave())) return false;
            router.push(studyHref(stageId, skill, { topic: topicId, activity: nextActivity }));
            return true;
          }}
        />
      ) : (
        lesson.activities.length > 1 && (
          <label className="study-activity-picker">
            <LearningText text={studyLabels.chooseActivity(skill === "reading")} />
            <select
              value={lesson.activity_id}
              onChange={async (event) => {
                const nextActivity = event.target.value;
                if (await canLeave())
                  router.push(studyHref(stageId, skill, { topic: topicId, activity: nextActivity }));
              }}
            >
              {lesson.activities.map((activity) => (
                <option key={activity.id} value={activity.id}>
                  {activity.title.nl}
                </option>
              ))}
            </select>
          </label>
        )
      )}
      <nav className="study-stepper" aria-label={studyCopy.exerciseSteps.nl}>
        {studySteps.map((item, index) => (
          <button
            key={item.id}
            aria-current={step === item.id ? "step" : undefined}
            onClick={() => navigate(item.id)}
          >
            <span>{index + 1}</span>
            <LearningText text={item.title} />
          </button>
        ))}
      </nav>
      {step === "prepare" ? (
        <div className="study-preparation">
          <div className="study-section-heading">
            <div>
              <h2>
                <LearningText text={studyCopy.wordsYouCanUseStraightAway} />
              </h2>
              <p>
                {" "}
                <LearningText text={studyCopy.prepareInvitation} />{" "}
              </p>
            </div>
          </div>
          <CompactWords words={lesson.preparation.words} />
          {lesson.preparation.grammar.map((rule, index) => (
            <article className="study-grammar" key={index}>
              <div className="study-grammar-icon">
                <Icon name="layers" size={20} />
              </div>
              <div>
                <h3>
                  <LearningText text={rule.title} />
                </h3>
                <p>
                  <LearningText text={rule.explanation} />
                </p>
                {rule.examples.map((example, i) => (
                  <p key={i}>
                    <SpokenText text={example} />
                  </p>
                ))}
              </div>
            </article>
          ))}
          <button className="button" onClick={() => navigate("practise")}>
            <LearningText text={studyCopy.iMReadyToPractise} />
            <Icon name="arrow" size={18} />
          </button>
        </div>
      ) : (
        <>
          <nav className="study-part-tabs" aria-label={studyCopy.skillParts.nl}>
            {lesson.parts.map((item, index) => (
              <button
                key={item.id}
                aria-pressed={part.id === item.id}
                onClick={() => navigate(step, item.id)}
              >
                <span>{index + 1}.</span> <LearningText text={item.title} />
              </button>
            ))}
          </nav>
          <div className="study-lesson-tools">
            <button
              className="study-text-button"
              onClick={() => {
                setReference(!reference);
                setAssisted(true);
              }}
              aria-expanded={reference}
            >
              <Icon name="book" size={16} />
              <LearningText text={studyCopy.keepWordsOpen} />{" "}
            </button>
            <span className="study-temporary">
              <Icon name="shield" size={14} />
              <LearningText text={studyCopy.temporaryScore} />{" "}
            </span>
          </div>
          {reference && <CompactWords words={lesson.preparation.words} />}
          <PracticePart
            key={`${lesson.activity_id}.${part.id}.${step}`}
            lesson={lesson}
            part={part}
            mode={step}
            assisted={assisted}
            onAssisted={() => setAssisted(true)}
            onNext={() => {
              const next = lesson.parts[lesson.parts.findIndex((item) => item.id === part.id) + 1];
              navigate(next ? step : "check", next?.id ?? lesson.parts[0].id);
            }}
          />
        </>
      )}
    </section>
  );
}
