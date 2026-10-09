"use client";

import { useMutation, useQuery, useQueryClient, type QueryClient } from "@tanstack/react-query";

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
  /** The stage whose passed check earned the offer below; null when there is no offer. */
  earned_stage_id: string | null;
  /** A stage the learner may move up to; offered, never applied without their say. */
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

/**
 * Per query client: saves still in flight and the last profile the server confirmed. A failed save rolls
 * back to what the server holds, never to another save's optimistic value that may fail too.
 */
const saves = new WeakMap<QueryClient, { pending: number; confirmed?: Me }>();

export function useUpdateProfile() {
  const client = useQueryClient();
  return useMutation({
    // one save at a time, in the order the learner made them
    scope: { id: "profile" },
    mutationFn: updateProfile,
    // the controls show the new value at once and fall back if the server refuses it
    onMutate: async (patch: ProfileUpdate) => {
      await client.cancelQueries({ queryKey: queryKeys.me() });
      const previous = client.getQueryData<Me>(queryKeys.me());
      const state = saves.get(client) ?? { pending: 0 };
      if (state.pending === 0) state.confirmed = previous;
      state.pending += 1;
      saves.set(client, state);
      if (previous) {
        client.setQueryData<Me>(queryKeys.me(), {
          ...previous,
          profile: { ...previous.profile, ...(patch as Partial<Profile>) },
        });
      }
    },
    onError: (_error, patch) => {
      const confirmed = saves.get(client)?.confirmed;
      const current = client.getQueryData<Me>(queryKeys.me());
      if (!confirmed || !current) return;
      // undo only what this save still shows; a later save's value stays until that save settles
      const profile: Record<string, unknown> = { ...current.profile };
      const server: Record<string, unknown> = { ...confirmed.profile };
      const own = patch as Record<string, unknown>;
      for (const key of Object.keys(own)) {
        if (key in profile && profile[key] === own[key]) profile[key] = server[key];
      }
      client.setQueryData<Me>(queryKeys.me(), { ...current, profile: profile as unknown as Profile });
    },
    onSuccess: (me) => {
      client.setQueryData(queryKeys.me(), me);
      const state = saves.get(client);
      if (state) state.confirmed = me;
      void client.invalidateQueries({ queryKey: queryKeys.today() });
      void client.invalidateQueries({ queryKey: queryKeys.curriculum.all() });
    },
    onSettled: (_me, error) => {
      const state = saves.get(client);
      if (state) state.pending = Math.max(0, state.pending - 1);
      // after a failure, a reachable server corrects whatever the cache still shows
      if (error && state?.pending === 0) void client.invalidateQueries({ queryKey: queryKeys.me() });
    },
  });
}
