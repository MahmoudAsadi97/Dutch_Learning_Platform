import { render, screen } from "@testing-library/react";
import { beforeEach, expect, test, vi } from "vitest";
import { UsagePanel } from "@/components/UsagePanel";
import type { Usage } from "@/lib/client/queries/usage";
import { uiCopy } from "@/lib/ui-copy";

const state = vi.hoisted(() => ({ data: null as Usage | null, error: null }));
vi.mock("@/lib/client/queries/usage", () => ({ useUsage: () => state }));
vi.mock("@/components/ui/UiText", () => ({
  UiText: ({ text }: { text: { nl: string } }) => <span>{text.nl}</span>,
}));

beforeEach(() => {
  const scopes = { used: 2, reserved: 0, limit: 10, remaining: 8 };
  state.data = {
    period: "2026-10-17",
    counters: {
      model_calls: { daily: scopes, total: scopes },
      audio_seconds: { daily: scopes, total: scopes },
      video_seconds: {
        daily: { used: 30, reserved: 0, limit: 0, remaining: 0 },
        total: { used: 60, reserved: 0, limit: 0, remaining: 0 },
      },
    },
    pricing_table_entries: 0,
    estimated_cost: null,
    note: "",
  };
});

test("the learner sees active allowances without advertising retired video time", () => {
  render(<UsagePanel />);
  expect(screen.getByRole("rowheader", { name: "modeloproepen" })).toBeVisible();
  expect(screen.getByRole("rowheader", { name: "seconden audio" })).toBeVisible();
  expect(screen.queryByRole("rowheader", { name: /video/i })).not.toBeInTheDocument();
  expect(screen.getAllByRole("rowheader")).toHaveLength(2);
  expect(state.data?.counters.video_seconds.total.used).toBe(60);
});

test("the active content explanation does not advertise generated videos", () => {
  for (const language of ["nl", "en", "fa"] as const) {
    expect(uiCopy.about.model[language]).not.toMatch(/video|ویدیو/i);
    expect(uiCopy.about.voices[language]).not.toMatch(/video|ویدیو/i);
  }
});
