"use client";

import { useState } from "react";

import { useLanguageSupport, type SupportMode } from "@/components/LanguageSupport";
import { Button, Field, Notice, Select } from "@/components/ui";
import { useProfile, useUpdateProfile, type DailyGoal, type GlossMode } from "@/lib/client/profile";
import { STAGE_IDS, stageLabel, stageNames } from "@/lib/domain/registry";

const GOALS: { value: DailyGoal; label: string }[] = [
  { value: 10, label: "Kort · 10 punten" },
  { value: 20, label: "Gewoon · 20 punten" },
  { value: 30, label: "Stevig · 30 punten" },
];

const GLOSS: { value: GlossMode; label: string }[] = [
  { value: "auto", label: "Automatisch (meer hulp op lage niveaus)" },
  { value: "on", label: "Altijd" },
  { value: "off", label: "Nooit" },
];

/**
 * The one place a learner sets the level, the daily goal, the support language and the gloss preference.
 * A level earned by passing checks is offered, never applied without the learner's say.
 */
export function LearningPreferences() {
  const profile = useProfile();
  const update = useUpdateProfile();
  const { mode, setMode } = useLanguageSupport();
  const [saved, setSaved] = useState("");

  const data = profile.data?.profile;
  // a failed refresh keeps the preferences already on screen; only a first load that fails says so
  if (profile.isError && !data) {
    return (
      <Notice tone="warning" role="status">
        Je leervoorkeuren zijn nu niet beschikbaar.{" "}
        <button type="button" className="linklike" onClick={() => void profile.refetch()}>
          Opnieuw proberen
        </button>
      </Notice>
    );
  }
  if (!data) {
    return (
      <p className="muted" role="status">
        Voorkeuren laden…
      </p>
    );
  }
  const save = (patch: Parameters<typeof update.mutate>[0], message: string) => {
    setSaved("");
    update.mutate(patch, { onSuccess: () => setSaved(message) });
  };

  return (
    <div className="learning-preferences" data-testid="learning-preferences">
      {data.suggested_stage_id && (
        <Notice
          tone="info"
          title={`Je hebt ${stageLabel(data.earned_stage_id ?? data.stage_id)} gehaald.`}
          role="status"
        >
          <p>Wil je vanaf nu op dat niveau oefenen? Je verhalen en onderwerpen volgen mee.</p>
          <Button
            variant="secondary"
            size="small"
            onClick={() => save({ stage_id: data.suggested_stage_id ?? data.stage_id }, "Niveau aangepast.")}
          >
            Ga naar {stageLabel(data.suggested_stage_id)}
          </Button>
        </Notice>
      )}
      <div className="preference-grid">
        <Field label="Mijn niveau" hint="Dit niveau bepaalt je verhalen en oefenonderwerpen.">
          {(control) => (
            <Select
              {...control}
              value={data.stage_id}
              onChange={(event) => save({ stage_id: event.target.value }, "Niveau aangepast.")}
            >
              {STAGE_IDS.map((id) => (
                <option key={id} value={id}>
                  {stageNames[id]} · {stageLabel(id)}
                </option>
              ))}
            </Select>
          )}
        </Field>
        <Field label="Mijn dagdoel" hint="Punten belonen oefenen, nooit je Nederlands.">
          {(control) => (
            <Select
              {...control}
              value={String(data.daily_goal_points)}
              onChange={(event) =>
                save({ daily_goal_points: Number(event.target.value) as DailyGoal }, "Dagdoel aangepast.")
              }
            >
              {GOALS.map((goal) => (
                <option key={goal.value} value={goal.value}>
                  {goal.label}
                </option>
              ))}
            </Select>
          )}
        </Field>
        <Field label="Taal voor hulp">
          {(control) => (
            <Select
              {...control}
              value={mode}
              onChange={(event) => setMode(event.target.value as SupportMode)}
            >
              <option value="nl-en">Nederlands · English</option>
              <option value="nl-fa">Nederlands · فارسی</option>
              <option value="nl-fa-en">Nederlands · فارسی · English</option>
            </Select>
          )}
        </Field>
        <Field label="Vertalingen onder de knoppen" hint="Een korte vertaling onder de Nederlandse labels.">
          {(control) => (
            <Select
              {...control}
              value={data.gloss_mode}
              onChange={(event) => save({ gloss_mode: event.target.value as GlossMode }, "Voorkeur bewaard.")}
            >
              {GLOSS.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </Select>
          )}
        </Field>
      </div>
      {/* always present, so a screen reader hears each confirmation */}
      <p className="muted small-text" role="status">
        {update.isError ? "" : saved}
      </p>
      {update.isError && (
        <Notice tone="danger" role="alert">
          Bewaren lukte niet. Probeer het opnieuw.
        </Notice>
      )}
    </div>
  );
}
