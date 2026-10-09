"use client";

import { useEffect } from "react";

import { useToast } from "@/components/ui/Toast";
import { UiText } from "@/components/ui/UiText";
import { GOAL_EVENT } from "@/lib/client/api";
import { playTone } from "@/lib/client/tones";
import { uiCopy } from "@/lib/ui-copy";

/**
 * Marks the moment the day's goal is reached, on whatever screen earned the last points: the API says so
 * on the award that crosses it (`goal_reached`), `apiJson` announces it, and this plays the goal tone (when
 * tones are on) and says it in words for everyone who does not hear it.
 */
export function GoalCelebration() {
  const { notify } = useToast();
  useEffect(() => {
    const onGoal = () => {
      playTone("goal");
      notify(<UiText text={uiCopy.today.goalMet} tier="guide" />, { tone: "success" });
    };
    window.addEventListener(GOAL_EVENT, onGoal);
    return () => window.removeEventListener(GOAL_EVENT, onGoal);
  }, [notify]);
  return null;
}
