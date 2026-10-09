import { act, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { GoalCelebration } from "@/components/shell/GoalCelebration";
import { ToastProvider } from "@/components/ui/Toast";
import { apiJson, GOAL_EVENT } from "@/lib/client/api";

const playTone = vi.fn();
vi.mock("@/lib/client/tones", () => ({ playTone: (tone: string) => playTone(tone) }));

function respond(body: unknown) {
  vi.stubGlobal(
    "fetch",
    vi
      .fn()
      .mockResolvedValue(
        new Response(JSON.stringify(body), { status: 200, headers: { "content-type": "application/json" } }),
      ),
  );
}

afterEach(() => {
  vi.unstubAllGlobals();
  playTone.mockClear();
});

describe("reaching the daily goal", () => {
  it("is announced by the API client only when the award crossed the goal", async () => {
    const heard = vi.fn();
    window.addEventListener(GOAL_EVENT, heard);
    respond({ id: "episode-1", goal_reached: true });
    await apiJson("stories/episodes/episode-1/read", { method: "POST" });
    respond({ id: "episode-1" });
    await apiJson("stories/episodes/episode-1/read", { method: "POST" });
    window.removeEventListener(GOAL_EVENT, heard);
    expect(heard).toHaveBeenCalledTimes(1);
  });

  it("plays the goal tone and says it in words", async () => {
    render(
      <ToastProvider>
        <GoalCelebration />
      </ToastProvider>,
    );
    act(() => {
      window.dispatchEvent(new CustomEvent(GOAL_EVENT));
    });
    expect(playTone).toHaveBeenCalledWith("goal");
    expect((await screen.findAllByText(/Dagdoel gehaald/)).length).toBeGreaterThan(0);
  });
});
