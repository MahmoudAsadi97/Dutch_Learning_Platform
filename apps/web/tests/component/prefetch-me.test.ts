// @vitest-environment node
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

/**
 * The server prefetch of /me may only make the first paint better: every failure returns null so the
 * client loads the profile itself, and a slow API cannot hold the page longer than the cap.
 */
const resolvePrincipal = vi.fn();
vi.mock("server-only", () => ({}));
vi.mock("next/headers", () => ({ headers: async () => new Headers({ host: "localhost:3000" }) }));
vi.mock("@/lib/server/config", () => ({
  serverConfig: () => ({ apiInternalUrl: "http://api.internal" }),
}));
vi.mock("@/lib/server/identity", () => ({
  resolvePrincipal: (...args: unknown[]) => resolvePrincipal(...args),
}));
vi.mock("@/lib/server/assertion", () => ({ issueAssertion: async () => "signed" }));

const me = {
  learner: { email: "owner@example.com", display_name: "Owner" },
  profile: { stage_id: "a1" },
  features: {},
};

beforeEach(() => {
  resolvePrincipal.mockReset();
  resolvePrincipal.mockReturnValue({ ok: true, principal: { subject: "s", email: "owner@example.com" } });
});

afterEach(() => {
  vi.unstubAllGlobals();
  vi.useRealTimers();
});

describe("prefetchMe", () => {
  it("returns the profile and sends a signed assertion to the internal API", async () => {
    const fetch = vi.fn().mockResolvedValue(new Response(JSON.stringify(me), { status: 200 }));
    vi.stubGlobal("fetch", fetch);
    const { prefetchMe } = await import("@/lib/server/me");
    await expect(prefetchMe()).resolves.toEqual(me);
    const [url, init] = fetch.mock.calls[0] as [string, RequestInit & { headers: Record<string, string> }];
    expect(url).toBe("http://api.internal/me");
    expect(init.headers.authorization).toBe("Bearer signed");
    expect(init.cache).toBe("no-store");
  });

  it("returns null without asking the API when there is no principal", async () => {
    resolvePrincipal.mockReturnValue({ ok: false, status: 401, reason: "no identity" });
    const fetch = vi.fn();
    vi.stubGlobal("fetch", fetch);
    const { prefetchMe } = await import("@/lib/server/me");
    await expect(prefetchMe()).resolves.toBeNull();
    expect(fetch).not.toHaveBeenCalled();
  });

  it("returns null when the API refuses or cannot be reached", async () => {
    const { prefetchMe } = await import("@/lib/server/me");
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response("{}", { status: 503 })));
    await expect(prefetchMe()).resolves.toBeNull();
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new TypeError("connection refused")));
    await expect(prefetchMe()).resolves.toBeNull();
  });

  it("gives up after its time cap instead of holding the page", async () => {
    const fetch = vi.fn(
      (_url: string, init: RequestInit) =>
        new Promise<Response>((_resolve, reject) => {
          init.signal?.addEventListener("abort", () => reject(new DOMException("timed out", "TimeoutError")));
        }),
    );
    vi.stubGlobal("fetch", fetch);
    const { prefetchMe } = await import("@/lib/server/me");
    const started = Date.now();
    await expect(prefetchMe()).resolves.toBeNull();
    expect(Date.now() - started).toBeLessThan(3000);
  });
});
