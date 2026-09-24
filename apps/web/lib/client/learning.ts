"use client";

import { useEffect, useState } from "react";
import { apiJson } from "./api";
import type {
  MissionResponse,
  PracticeSessionView,
  SkillRecordView,
} from "@/lib/types";

export interface LearningData {
  learner: {
    display_name: string;
    email: string;
    support_language: string;
    target_language: string;
  };
  skill_records: SkillRecordView[];
  sessions: PracticeSessionView[];
  mission: MissionResponse;
  missions: MissionResponse[];
}

export function useLearningData() {
  const [data, setData] = useState<LearningData | null>(null);
  const [error, setError] = useState(false);
  const [attempt, setAttempt] = useState(0);
  useEffect(() => {
    const controller = new AbortController();
    Promise.all([
      apiJson<Pick<LearningData, "learner" | "skill_records">>("progress", {
        signal: controller.signal,
      }),
      apiJson<{ sessions: PracticeSessionView[] }>(
        "practice/sessions",
        { signal: controller.signal },
      ),
      apiJson<MissionResponse>("missions/appointment-change", {
        signal: controller.signal,
      }),
      apiJson<{ missions: MissionResponse[] }>("missions", { signal: controller.signal }),
    ])
      .then(([progress, sessions, mission, catalog]) => {
        setData({ ...progress, ...sessions, mission, ...catalog });
        setError(false);
      })
      .catch(() => {
        if (!controller.signal.aborted) setError(true);
      });
    return () => controller.abort();
  }, [attempt]);
  return {
    data,
    error,
    retry: () => {
      setError(false);
      setAttempt((n) => n + 1);
    },
  };
}

export const skillNames = {
  reading: "Lezen",
  listening: "Luisteren",
  speaking: "Spreken",
  writing: "Schrijven",
};
export const recordStatus: Record<string, string> = {
  not_started: "Nog te ontdekken",
  in_progress: "Aan het oefenen",
  practised: "Geoefend",
};
export const sessionStatus: Record<string, string> = {
  active: "In uitvoering",
  completed: "Afgerond",
  ended: "Afgesloten",
  abandoned: "Opnieuw gestart",
};
export function localDate(value: string) {
  return new Intl.DateTimeFormat("nl-BE", {
    day: "numeric",
    month: "short",
    year: "numeric",
  }).format(new Date(value));
}
