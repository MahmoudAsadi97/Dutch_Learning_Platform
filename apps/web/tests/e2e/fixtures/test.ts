import { test as base, expect, type Page } from "@playwright/test";

/**
 * Every spec starts from the same learner: onboarded at A1 with Dutch and English, a goal of 20 points and
 * glosses off, so no screen shows the first-run flow unless a spec asks for it. The reset endpoint exists
 * outside production only; the e2e servers run with APP_ENV=development.
 *
 * The calls go through the browser page, not the request fixture: in the pinned Linux container that
 * renders the visual baselines, only Chromium's resolver maps localhost to the host machine.
 */
export async function resetProfile(page: Page): Promise<void> {
  await page.goto("/health");
  await page.evaluate(async () => {
    const headers = { "X-Requested-With": "fetch", "Content-Type": "application/json" };
    async function call(path: string, method: string, body?: unknown) {
      const response = await fetch(`/api/${path}`, {
        method,
        headers,
        body: body === undefined ? undefined : JSON.stringify(body),
      });
      if (!response.ok) throw new Error(`${method} /api/${path} answered ${response.status}`);
    }
    await call("me/reset", "POST");
    await call("me/onboarding", "POST", { support_mode: "nl-en", stage_id: "a1", daily_goal_points: 20 });
    await call("me", "PATCH", { gloss_mode: "off" });
  });
}

export const test = base.extend({
  // Playwright calls the second argument "use"; a different name keeps the React hooks lint rule quiet
  page: async ({ page }, provide) => {
    await resetProfile(page);
    await provide(page);
  },
});

export { expect };
