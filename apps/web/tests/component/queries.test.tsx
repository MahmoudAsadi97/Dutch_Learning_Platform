import { QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { ApiError } from "@/lib/client/api";
import { makeQueryClient, shouldRetryQuery } from "@/lib/client/query-client";
import { useUsage } from "@/lib/client/queries/usage";

const usage = {
  period: "2026-10-06",
  counters: {
    model_calls: {
      daily: { used: 1, reserved: 0, limit: 20, remaining: 19 },
      total: { used: 1, reserved: 0, limit: 100, remaining: 99 },
    },
  },
  pricing_table_entries: 0,
  estimated_cost: null,
  note: "",
};

function Reader({ id }: { id: string }) {
  const { data } = useUsage();
  return <span data-testid={id}>{data ? `used ${data.counters.model_calls.daily.used}` : "…"}</span>;
}

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("query client", () => {
  it("retries only temporary failures, and never more than twice", () => {
    expect(shouldRetryQuery(0, new ApiError(503, "down", "r1"))).toBe(true);
    expect(shouldRetryQuery(0, new ApiError(504, "slow", "r1"))).toBe(true);
    expect(shouldRetryQuery(0, new ApiError(409, "conflict", "r1"))).toBe(false);
    expect(shouldRetryQuery(0, new ApiError(500, "boom", "r1"))).toBe(false);
    expect(shouldRetryQuery(2, new ApiError(503, "down", "r1"))).toBe(false);
    expect(shouldRetryQuery(0, new TypeError("network"))).toBe(false);
  });

  it("does not retry mutations and does not refetch on window focus", () => {
    const defaults = makeQueryClient().getDefaultOptions();
    expect(defaults.mutations?.retry).toBe(false);
    expect(defaults.queries?.refetchOnWindowFocus).toBe(false);
    expect(defaults.queries?.staleTime).toBe(30_000);
  });

  it("two readers of the same key make one request", async () => {
    const fetchMock = vi.fn(
      async () =>
        new Response(JSON.stringify(usage), { status: 200, headers: { "content-type": "application/json" } }),
    );
    vi.stubGlobal("fetch", fetchMock);
    render(
      <QueryClientProvider client={makeQueryClient()}>
        <Reader id="a" />
        <Reader id="b" />
      </QueryClientProvider>,
    );
    await waitFor(() => expect(screen.getByTestId("a")).toHaveTextContent("used 1"));
    expect(screen.getByTestId("b")).toHaveTextContent("used 1");
    expect(fetchMock).toHaveBeenCalledTimes(1);
  });
});
