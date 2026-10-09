"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { apiJson } from "./api";
import { queryKeys } from "./query-keys";

export type SupportMode = "nl-en" | "nl-fa" | "nl-fa-en";
export type GlossMode = "auto" | "on" | "off";
export type DailyGoal = 10 | 20 | 30;

export interface Profile {
  stage_id: string;
  daily_goal_points: DailyGoal;
  support_mode: SupportMode | null;
  gloss_mode: GlossMode;
  stated_goal: string;
  onboarded_at: string | null;
  suggested_stage_id: string | null;
}

export interface Me {
  learner: { email: string; display_name: string };
  profile: Profile;
  features: Record<string, boolean>;
}

export interface ProfileUpdate {
  stage_id?: string;
  daily_goal_points?: DailyGoal;
  support_mode?: SupportMode | null;
  gloss_mode?: GlossMode;
  stated_goal?: string;
}

export interface OnboardingInput {
  support_mode: SupportMode;
  stage_id: string;
  daily_goal_points?: DailyGoal;
  stated_goal?: string;
}

export interface OnboardingResult extends Me {
  already_onboarded: boolean;
  episode: { id: string; number: number; status: string } | null;
}

export function fetchMe(signal?: AbortSignal): Promise<Me> {
  return apiJson<Me>("me", { signal });
}

export function updateProfile(body: ProfileUpdate): Promise<Me> {
  return apiJson<Me>("me", { method: "PATCH", body });
}

export function completeOnboarding(body: OnboardingInput): Promise<OnboardingResult> {
  return apiJson<OnboardingResult>("me/onboarding", { method: "POST", body });
}

/** The learner profile: level, daily goal, support language and feature switches, one source for all screens. */
export function useProfile() {
  return useQuery({
    queryKey: queryKeys.me(),
    queryFn: ({ signal }) => fetchMe(signal),
    staleTime: 5 * 60_000,
  });
}

export function useUpdateProfile() {
  const client = useQueryClient();
  return useMutation({
    mutationFn: updateProfile,
    onSuccess: (me) => {
      client.setQueryData(queryKeys.me(), me);
      void client.invalidateQueries({ queryKey: queryKeys.today() });
      void client.invalidateQueries({ queryKey: queryKeys.curriculum.all() });
    },
  });
}
