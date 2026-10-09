import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { LearningPreferences } from "@/components/LearningPreferences";
import type { Me } from "@/lib/client/profile";
import { queryKeys } from "@/lib/client/query-keys";

function me(profile: Partial<Me["profile"]>): Me {
  return {
    learner: { email: "owner@example.com", display_name: "Owner" },
    profile: {
      stage_id: "a1",
      daily_goal_points: 20,
      support_mode: "nl-en",
      gloss_mode: "auto",
      stated_goal: "",
      onboarded_at: "2026-10-09T10:00:00Z",
      earned_stage_id: null,
      suggested_stage_id: null,
      ...profile,
    },
    features: {},
  };
}

function renderWith(value: Me) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false, staleTime: Infinity } } });
  client.setQueryData(queryKeys.me(), value);
  return render(
    <QueryClientProvider client={client}>
      <LearningPreferences />
    </QueryClientProvider>,
  );
}

describe("LearningPreferences", () => {
  it("names the stage the learner passed and offers the next one", () => {
    renderWith(me({ stage_id: "a1", earned_stage_id: "a1", suggested_stage_id: "pre-a2" }));
    expect(screen.getByText("Je hebt A1 gehaald.")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Ga naar pre-A2/ })).toBeInTheDocument();
  });

  it("shows no offer when nothing was earned", () => {
    renderWith(me({}));
    expect(screen.queryByText(/gehaald/)).toBeNull();
    expect(screen.getByLabelText("Mijn niveau")).toHaveValue("a1");
  });
});
