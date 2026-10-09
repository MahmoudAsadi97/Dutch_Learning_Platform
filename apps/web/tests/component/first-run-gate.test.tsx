import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor } from "@testing-library/react";
import type { ReactNode } from "react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { FirstRunGate } from "@/components/shell/FirstRunGate";
import { queryKeys } from "@/lib/client/query-keys";

const replace = vi.fn();
let pathname = "/";
vi.mock("next/navigation", () => ({
  usePathname: () => pathname,
  useRouter: () => ({ replace, push: vi.fn() }),
}));

function me(onboardedAt: string | null) {
  return {
    learner: { email: "owner@example.com", display_name: "Owner" },
    profile: {
      stage_id: "a1",
      daily_goal_points: 20,
      support_mode: "nl-en",
      gloss_mode: "auto",
      stated_goal: "",
      onboarded_at: onboardedAt,
      suggested_stage_id: null,
    },
    features: {},
  };
}

function renderGate(client: QueryClient, enabled = true, child: ReactNode = <p>Vandaag</p>) {
  return render(
    <QueryClientProvider client={client}>
      <FirstRunGate enabled={enabled}>{child}</FirstRunGate>
    </QueryClientProvider>,
  );
}

function client() {
  return new QueryClient({ defaultOptions: { queries: { retry: false } } });
}

beforeEach(() => {
  replace.mockClear();
  pathname = "/";
  window.matchMedia ??= ((query: string) => ({
    matches: false,
    media: query,
    addEventListener() {},
    removeEventListener() {},
  })) as unknown as typeof window.matchMedia;
});

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("FirstRunGate", () => {
  it("sends a learner who has not onboarded to the welcome and shows no page meanwhile", async () => {
    const cache = client();
    cache.setQueryData(queryKeys.me(), me(null));
    renderGate(cache);
    expect(screen.queryByText("Vandaag")).toBeNull();
    await waitFor(() => expect(replace).toHaveBeenCalledWith("/welkom"));
  });

  it("lets an onboarded learner through", () => {
    const cache = client();
    cache.setQueryData(queryKeys.me(), me("2026-10-09T10:00:00Z"));
    renderGate(cache);
    expect(screen.getByText("Vandaag")).toBeInTheDocument();
    expect(replace).not.toHaveBeenCalled();
  });

  it("waits while the profile loads, so no page starts work before the learner has chosen", () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(() => new Promise(() => undefined)),
    );
    renderGate(client());
    expect(screen.queryByText("Vandaag")).toBeNull();
    expect(replace).not.toHaveBeenCalled();
  });

  it("opens when the profile cannot be loaded", async () => {
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new TypeError("network down")));
    const cache = client();
    renderGate(cache);
    expect(screen.queryByText("Vandaag")).toBeNull();
    await waitFor(() => expect(cache.getQueryState(queryKeys.me())?.status).toBe("error"));
    expect(await screen.findByText("Vandaag")).toBeInTheDocument();
    expect(replace).not.toHaveBeenCalled();
  });

  it("does nothing when switched off or on an exempt page", () => {
    const cache = client();
    cache.setQueryData(queryKeys.me(), me(null));
    renderGate(cache, false);
    expect(screen.getByText("Vandaag")).toBeInTheDocument();
    pathname = "/settings";
    renderGate(cache, true, <p>Instellingen</p>);
    expect(screen.getByText("Instellingen")).toBeInTheDocument();
    expect(replace).not.toHaveBeenCalled();
  });
});
