import { expect, test } from "@playwright/test";

/** The proxy is the trust boundary: these checks talk to it directly, without the UI. */
test.describe("api proxy", () => {
  test("issues an assertion for the fixture principal and echoes request ids", async ({ request }) => {
    const response = await request.get("/api/health/preflight", { headers: { "X-Request-Id": "e2e-preflight-0001" } });
    expect(response.status()).toBe(200);
    expect(response.headers()["x-request-id"]).toBe("e2e-preflight-0001");
    const body = await response.json();
    expect(body.principal).toEqual({ email: "owner@example.com", identity_provider: "fixture" });
    expect(JSON.stringify(body)).not.toContain("ASSERTION");
  });

  test("refuses state-changing requests without the anti-CSRF header or from another origin", async ({ request }) => {
    const missing = await request.post("/api/practice/sessions", { data: { mission_id: "appointment-change" } });
    expect(missing.status()).toBe(403);
    const crossSite = await request.post("/api/practice/sessions", {
      data: { mission_id: "appointment-change" },
      headers: { "X-Requested-With": "fetch", Origin: "https://elsewhere.example" },
    });
    expect(crossSite.status()).toBe(403);
    const ok = await request.post("/api/practice/sessions", {
      data: { mission_id: "appointment-change" },
      headers: { "X-Requested-With": "fetch", "X-Request-Id": "e2e-session-0001" },
    });
    expect(ok.status()).toBe(201);
  });

  test("ignores client-supplied identity and binds the fixture to localhost", async ({ request }) => {
    const spoofed = await request.get("/api/progress", {
      headers: { Authorization: "Bearer forged", "X-MS-CLIENT-PRINCIPAL-ID": "someone" },
    });
    expect(spoofed.status()).toBe(200);
    expect((await spoofed.json()).learner.email).toBe("owner@example.com");

    const wrongHost = await request.get("/api/health", { headers: { Host: "example.com" } });
    expect(wrongHost.status()).toBe(403);
  });

  test("malformed request ids are replaced, never trusted", async ({ request }) => {
    const response = await request.get("/api/health/preflight", { headers: { "X-Request-Id": "<script>" } });
    expect(response.status()).toBe(200);
    expect(response.headers()["x-request-id"]).toMatch(/^[0-9a-f]{32}$/);
  });
});
