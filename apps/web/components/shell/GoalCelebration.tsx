"use client";

import { useEffect } from "react";

import { useToast } from "@/components/ui/Toast";
import { UiText } from "@/components/ui/UiText";
import { GOAL_EVENT } from "@/lib/client/api";
import { playTone } from "@/lib/client/tones";
import { uiCopy } from "@/lib/ui-copy";

/** The screen's own answer tone (at most about 0.3 s) plays first; the fanfare follows it. */
const GOAL_TONE_DELAY_MS = 320;

let celebratedDay = "";

function brusselsDay(): string {
  return new Intl.DateTimeFormat("en-CA", { timeZone: "Europe/Brussels" }).format(new Date());
}

/**
 * Marks the moment the day's goal is reached, on whatever screen earned the last points: the API says so
 * on the award that crosses it (`goal_reached`, repeated when that request is retried), `apiJson` announces
 * it, and this plays the goal tone (when tones are on) and says it in words for everyone who does not hear
 * it, once a day.
 */
export function GoalCelebration() {
  const { notify } = useToast();
  useEffect(() => {
    const timers = new Set<number>();
    const onGoal = () => {
      const day = brusselsDay();
      if (day === celebratedDay) return;
      celebratedDay = day;
      timers.add(window.setTimeout(() => playTone("goal"), GOAL_TONE_DELAY_MS));
      notify(<UiText text={uiCopy.today.goalMet} tier="guide" />, { tone: "success" });
    };
    window.addEventListener(GOAL_EVENT, onGoal);
    return () => {
      window.removeEventListener(GOAL_EVENT, onGoal);
      timers.forEach((timer) => window.clearTimeout(timer));
    };
  }, [notify]);
  return null;
}
