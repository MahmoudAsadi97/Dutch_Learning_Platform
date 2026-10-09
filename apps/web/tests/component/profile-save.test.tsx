import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { act, renderHook, waitFor } from "@testing-library/react";
import type { ReactNode } from "react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { useUpdateProfile, type Me } from "@/lib/client/profile";
import { queryKeys } from "@/lib/client/query-keys";

const apiJson = vi.fn();
vi.mock("@/lib/client/api", () => ({ apiJson: (...args: unknown[]) => apiJson(...args) }));

const server: Me = {
  learner: { email: "owner@example.com", display_name: "Owner" },
  profile: {
    stage_id: "a1",
    daily_goal_points: 20,
    support_mode: "nl-en",
    gloss_mode: "auto",
    stated_goal: "",
    onboarded_at: "2026-10-09T08:00:00Z",
    earned_stage_id: null,
    suggested_stage_id: null,
  },
  features: {},
};

function setup() {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false, staleTime: Infinity } } });
  client.setQueryData(queryKeys.me(), server);
  const wrapper = ({ children }: { children: ReactNode }) => (
    <QueryClientProvider client={client}>{children}</QueryClientProvider>
  );
  return { client, ...renderHook(() => useUpdateProfile(), { wrapper }) };
}

const stage = (client: QueryClient) => client.getQueryData<Me>(queryKeys.me())?.profile.stage_id;

beforeEach(() => {
  apiJson.mockReset();
});

describe("saving the profile", () => {
  it("shows the new value at once and keeps the server's answer", async () => {
    const { client, result } = setup();
    let answer: (me: Me) => void = () => undefined;
    apiJson.mockImplementation(() => new Promise((resolve) => (answer = resolve)));
    act(() => result.current.mutate({ stage_id: "a2" }));
    await waitFor(() => expect(stage(client)).toBe("a2"));
    await act(async () => answer({ ...server, profile: { ...server.profile, stage_id: "a2" } }));
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(stage(client)).toBe("a2");
  });

  it("falls back to what the server holds when two saves in a row both fail", async () => {
    let fail: (reason: Error) => void = () => undefined;
    apiJson.mockImplementation(() => new Promise((_resolve, reject) => (fail = reject)));
    const { client, result } = setup();
    act(() => {
      result.current.mutate({ stage_id: "b1" });
      result.current.mutate({ stage_id: "b2" });
    });
    await waitFor(() => expect(stage(client)).toBe("b2"));
    await act(async () => fail(new Error("offline")));
    await waitFor(() => expect(apiJson).toHaveBeenCalledTimes(2));
    await act(async () => fail(new Error("offline")));
    await waitFor(() => expect(stage(client)).toBe("a1"));
  });
});
