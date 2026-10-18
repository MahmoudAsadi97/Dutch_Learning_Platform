"use client";

import { useQueryClient } from "@tanstack/react-query";
import { useState } from "react";

import { useLanguageSupport, type SupportMode } from "@/components/LanguageSupport";
import { Button, ButtonLink } from "@/components/ui/Button";
import { Field, Select } from "@/components/ui/Field";
import { Notice } from "@/components/ui/Notice";
import { Skeleton, SkeletonPanel } from "@/components/ui/Skeleton";
import { Stepper } from "@/components/ui/Stepper";
import { UiText } from "@/components/ui/UiText";
import { completeOnboarding, useProfile, type DailyGoal, type Me, type Profile } from "@/lib/client/profile";
import { queryKeys } from "@/lib/client/query-keys";
import { STAGE_IDS, stageLabel, stageNames } from "@/lib/domain/registry";
import { uiCopy, type Copy } from "@/lib/ui-copy";
import { ChoiceCards } from "./ChoiceCards";
import { FirstActivity } from "./FirstActivity";
import { HowItWorks } from "./HowItWorks";
import { Trilingual } from "./Trilingual";
import { useWriting, WritingProgress, type QueuedEpisode } from "./WritingProgress";

type Step = "taal" | "niveau" | "doel" | "uitleg" | "start";
const ORDER: Step[] = ["taal", "niveau", "doel", "uitleg", "start"];
const STEP_COPY: Record<Step, Copy> = {
  taal: uiCopy.welcome.stepLanguage,
  niveau: uiCopy.welcome.stepLevel,
  doel: uiCopy.welcome.stepGoal,
  uitleg: uiCopy.welcome.stepHow,
  start: uiCopy.welcome.stepStart,
};

/** Dutch practice, with optional English explanations. */
const SUPPORT: { value: SupportMode; copy: Copy; autonym?: string }[] = [
  { value: "nl", copy: uiCopy.welcome.supportNl },
  { value: "nl-en", copy: uiCopy.welcome.supportEn },
];

/** Plain-language starting points; any of the twelve stages can be picked below them. */
const PLACEMENT: { value: string; title: Copy; detail: Copy }[] = [
  { value: "pre-a1", title: uiCopy.welcome.levelZero, detail: uiCopy.welcome.levelZeroDetail },
  { value: "a1", title: uiCopy.welcome.levelFew, detail: uiCopy.welcome.levelFewDetail },
  { value: "a2", title: uiCopy.welcome.levelSimple, detail: uiCopy.welcome.levelSimpleDetail },
  { value: "b1", title: uiCopy.welcome.levelFair, detail: uiCopy.welcome.levelFairDetail },
];

/** Stored as a short Dutch phrase in the profile's stated goal. */
const REASONS: { value: string; copy: Copy }[] = [
  { value: "werk", copy: uiCopy.welcome.reasonWork },
  { value: "studie", copy: uiCopy.welcome.reasonStudy },
  { value: "dagelijks leven", copy: uiCopy.welcome.reasonDaily },
  { value: "inburgering", copy: uiCopy.welcome.reasonIntegration },
  { value: "voor mezelf", copy: uiCopy.welcome.reasonSelf },
];

type Pace = "10" | "20" | "30";
const PACE: { value: Pace; copy: Copy }[] = [
  { value: "10", copy: uiCopy.welcome.paceShort },
  { value: "20", copy: uiCopy.welcome.paceUsual },
  { value: "30", copy: uiCopy.welcome.paceLong },
];

/**
 * The first visit: support language, a starting level, a reason and a daily goal, then how Taalstudio
 * works and something to practise while episode one is written. Onboarding is stored once; a learner who
 * already finished it, or who comes from Instellingen, sees the explanation.
 */
export function WelcomeFlow({ explainOnly = false }: { explainOnly?: boolean }) {
  const profile = useProfile();
  if (!profile.data && !profile.isError) {
    return (
      <SkeletonPanel label={uiCopy.state.loading.nl}>
        <Skeleton lines={4} />
      </SkeletonPanel>
    );
  }
  if (explainOnly) return <Explanation />;
  return <WelcomeSteps saved={profile.data?.profile ?? null} />;
}

function Explanation({ notice }: { notice?: Copy }) {
  return (
    <div className="welcome-flow" data-accent="today">
      {notice && (
        <Notice tone="info" role="status">
          <UiText text={notice} tier="always" />
        </Notice>
      )}
      <HowItWorks />
      <div className="welcome-actions">
        <ButtonLink href="/" icon="arrow" iconEnd>
          <UiText text={uiCopy.welcome.toToday} inline />
        </ButtonLink>
      </div>
    </div>
  );
}

/** The steps; mounted once the profile is known, so a goal or reason chosen earlier is where they start. */
function WelcomeSteps({ saved }: { saved: Profile | null }) {
  const client = useQueryClient();
  const { mode, setMode } = useLanguageSupport();
  const [step, setStep] = useState<Step>("taal");
  // the level is always asked; a goal or reason already set in Instellingen is kept unless changed here
  const [stage, setStage] = useState<string | null>(null);
  const [reason, setReason] = useState<string | null>(() =>
    REASONS.some((option) => option.value === saved?.stated_goal) ? (saved?.stated_goal ?? null) : null,
  );
  const [pace, setPace] = useState<Pace>(() =>
    saved?.daily_goal_points === 10 || saved?.daily_goal_points === 30 ? `${saved.daily_goal_points}` : "20",
  );
  const [submitting, setSubmitting] = useState(false);
  const [failed, setFailed] = useState(false);
  const [episode, setEpisode] = useState<QueuedEpisode | null>(null);
  const [finished, setFinished] = useState(false);
  const [alreadyChosen, setAlreadyChosen] = useState(false);

  const onboarded = Boolean(saved?.onboarded_at) && !finished;
  if (onboarded) return <Explanation notice={alreadyChosen ? uiCopy.welcome.alreadyChosen : undefined} />;

  const index = ORDER.indexOf(step);
  const go = (next: Step) => {
    setStep(next);
    document.getElementById("main")?.focus();
  };

  async function submit() {
    if (!stage) return;
    setSubmitting(true);
    setFailed(false);
    try {
      const result = await completeOnboarding({
        support_mode: mode,
        stage_id: stage,
        daily_goal_points: Number(pace) as DailyGoal,
        stated_goal: reason ?? "",
      });
      const me: Me = { learner: result.learner, profile: result.profile, features: result.features };
      client.setQueryData(queryKeys.me(), me);
      void client.invalidateQueries({ queryKey: queryKeys.today() });
      void client.invalidateQueries({ queryKey: queryKeys.curriculum.all() });
      if (result.already_onboarded) {
        // another tab got there first: nothing chosen here was stored, so say so instead of carrying on
        setAlreadyChosen(true);
        return;
      }
      setStage(result.profile.stage_id);
      setEpisode(result.episode);
      setFinished(true);
      go("uitleg");
    } catch {
      setFailed(true);
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="welcome-flow" data-accent="today" data-testid="welcome-flow">
      <header className="welcome-heading">
        <h1>
          <Trilingual text={uiCopy.welcome.title} />
        </h1>
        <p>
          <Trilingual text={uiCopy.welcome.intro} />
        </p>
      </header>
      <Stepper
        className="welcome-steps"
        label="Stappen"
        current={step}
        steps={ORDER.map((key, position) => ({
          key,
          title: <UiText text={STEP_COPY[key]} inline />,
          done: position < index,
        }))}
      />

      {step === "taal" && (
        <div className="welcome-step">
          <ChoiceCards
            name="support"
            legend={<Trilingual text={uiCopy.welcome.languageQuestion} />}
            choices={SUPPORT.map((option) => ({
              value: option.value,
              title: <Trilingual text={option.copy} autonym={option.autonym} />,
            }))}
            value={mode}
            onChange={setMode}
            columns={1}
          />
          <p className="muted">
            <UiText text={uiCopy.welcome.languageNote} tier="always" />
          </p>
          <div className="welcome-actions">
            <Button icon="arrow" iconEnd onClick={() => go("niveau")}>
              <UiText text={uiCopy.welcome.next} inline />
            </Button>
          </div>
        </div>
      )}

      {step === "niveau" && (
        <div className="welcome-step">
          <ChoiceCards
            name="level"
            legend={<UiText text={uiCopy.welcome.levelQuestion} tier="always" />}
            choices={PLACEMENT.map((option) => ({
              value: option.value,
              title: <UiText text={option.title} tier="always" />,
              detail: <UiText text={option.detail} tier="always" />,
            }))}
            value={stage && PLACEMENT.some((option) => option.value === stage) ? stage : null}
            onChange={setStage}
          />
          <Field label={<UiText text={uiCopy.welcome.levelOther} tier="always" inline />}>
            {(control) => (
              <Select
                {...control}
                value={stage ?? ""}
                onChange={(event) => setStage(event.target.value || null)}
              >
                <option value="">—</option>
                {STAGE_IDS.map((id) => (
                  <option key={id} value={id}>
                    {stageNames[id]} · {stageLabel(id)}
                  </option>
                ))}
              </Select>
            )}
          </Field>
          <Notice tone="info">
            <UiText text={uiCopy.welcome.levelNote} tier="always" />
          </Notice>
          <div className="welcome-actions">
            <Button variant="ghost" onClick={() => go("taal")}>
              <UiText text={uiCopy.welcome.back} inline />
            </Button>
            <Button icon="arrow" iconEnd disabled={!stage} onClick={() => go("doel")}>
              <UiText text={uiCopy.welcome.next} inline />
            </Button>
          </div>
        </div>
      )}

      {step === "doel" && (
        <div className="welcome-step">
          <ChoiceCards
            name="reason"
            legend={<UiText text={uiCopy.welcome.goalQuestion} tier="always" />}
            choices={REASONS.map((option) => ({
              value: option.value,
              title: <UiText text={option.copy} tier="always" />,
            }))}
            value={reason}
            onChange={setReason}
            columns={3}
          />
          <div className="welcome-pace">
            <ChoiceCards
              name="pace"
              legend={<UiText text={uiCopy.welcome.paceQuestion} tier="always" />}
              choices={PACE.map((option) => ({
                value: option.value,
                title: <UiText text={option.copy} tier="always" />,
              }))}
              value={pace}
              onChange={setPace}
              columns={3}
            />
            <p className="muted">
              <UiText text={uiCopy.honesty.noScore} tier="always" />{" "}
              <UiText text={uiCopy.welcome.paceNote} tier="always" />
            </p>
          </div>
          {failed && (
            <Notice tone="warning" role="alert">
              <UiText text={uiCopy.welcome.saveFailed} tier="always" />
            </Notice>
          )}
          <div className="welcome-actions">
            <Button variant="ghost" onClick={() => go("niveau")}>
              <UiText text={uiCopy.welcome.back} inline />
            </Button>
            <Button icon="check" disabled={!stage || submitting} onClick={() => void submit()}>
              <UiText text={submitting ? uiCopy.welcome.saving : uiCopy.welcome.begin} inline />
            </Button>
          </div>
        </div>
      )}

      {step === "uitleg" && (
        <div className="welcome-step">
          <HowItWorks />
          <div className="welcome-actions">
            <Button icon="arrow" iconEnd onClick={() => go("start")}>
              <UiText text={uiCopy.welcome.next} inline />
            </Button>
          </div>
        </div>
      )}

      {step === "start" && stage && <StartStep episode={episode} stage={stage} />}
    </div>
  );
}

/** The last step: what the writer is doing, said as it is, beside something to practise. */
function StartStep({ episode, stage }: { episode: QueuedEpisode | null; stage: string }) {
  const writing = useWriting(episode);
  const firstBeingWritten = episode?.number === 1 && writing.waiting;
  return (
    <div className="welcome-step">
      <section className="welcome-writer" aria-labelledby="writer-title">
        <h2 id="writer-title">
          <UiText
            text={firstBeingWritten ? uiCopy.welcome.startTitle : uiCopy.welcome.startTitleNeutral}
            tier="always"
          />
        </h2>
        {firstBeingWritten && (
          <p>
            <UiText text={uiCopy.welcome.startIntro} tier="always" />
          </p>
        )}
        <WritingProgress episode={episode} writing={writing} />
      </section>
      <FirstActivity stage={stage} />
      <div className="welcome-actions">
        <ButtonLink href="/" icon="arrow" iconEnd>
          <UiText text={uiCopy.welcome.toToday} inline />
        </ButtonLink>
      </div>
    </div>
  );
}
