import AxeBuilder from "@axe-core/playwright";
import type { Page } from "@playwright/test";
import { expect, test } from "./fixtures/test";

/**
 * The first visit. The fixture onboards every learner; these tests undo that through the reset endpoint
 * (development only) and walk the real flow against the real API.
 */
async function forgetOnboarding(page: Page) {
  await page.evaluate(async () => {
    const response = await fetch("/api/me/reset", {
      method: "POST",
      headers: { "X-Requested-With": "fetch" },
    });
    if (!response.ok) throw new Error(`reset answered ${response.status}`);
  });
}

async function profile(page: Page) {
  return page.evaluate(async () => {
    const response = await fetch("/api/me", { headers: { "X-Requested-With": "fetch" } });
    return (await response.json()).profile as Record<string, unknown>;
  });
}

/** The learner is shared by every spec; words kept here would change later screens, so they go again. */
async function removeLibraryWords(page: Page) {
  await page.evaluate(async () => {
    const headers = { "X-Requested-With": "fetch" };
    const response = await fetch("/api/words?limit=500", { headers });
    const { items } = (await response.json()) as { items: { id: string; source_kind: string }[] };
    for (const item of items.filter((word) => word.source_kind === "library"))
      await fetch(`/api/words/${item.id}`, { method: "DELETE", headers });
  });
}

const next = /^Volgende stap/;

test.afterEach(async ({ page }) => {
  await removeLibraryWords(page);
});

test("a new learner is sent to the welcome, chooses a start and finishes it once", async ({ page }) => {
  await forgetOnboarding(page);
  const todayCalls: string[] = [];
  const wordPosts: Record<string, unknown>[] = [];
  page.on("request", (request) => {
    if (/\/api\/today(?:[?/]|$)/.test(request.url())) todayCalls.push(request.url());
    if (request.method() === "POST" && /\/api\/words$/.test(request.url()))
      wordPosts.push(request.postDataJSON() as Record<string, unknown>);
  });

  await page.goto("/");
  await expect(page).toHaveURL(/\/welkom$/);
  const heading = page.getByRole("heading", { level: 1 });
  await expect(heading).toContainText("Welkom bij Taalstudio");
  await expect(heading).toContainText("Welcome to Taalstudio");
  // Only Dutch and optional English are offered, including before a preference is saved.
  await expect(page.locator('.welcome-heading [lang="fa"]')).toHaveCount(0);
  await expect(page.getByRole("radio", { name: /^Alleen Nederlands/ })).toBeVisible();
  await expect(page.getByRole("radio", { name: /Perzische|فارسی/ })).toHaveCount(0);
  await expect(page.getByRole("navigation", { name: "Hoofdmenu", exact: true })).toHaveCount(0);
  await expect(page.getByRole("navigation", { name: "Mobiel hoofdmenu" })).toHaveCount(0);

  await page.getByRole("radio", { name: /^Alleen Nederlands/ }).check();
  await expect(page.getByLabel("Taalhulp / language")).toHaveValue("nl");
  await expect(heading.locator('[lang="en"]')).toHaveCount(0);
  await page.getByRole("button", { name: next }).click();

  await expect(page.getByRole("button", { name: next })).toBeDisabled();
  await page.getByRole("radio", { name: /^Ik ken een paar woorden/ }).check();
  await page.getByRole("button", { name: next }).click();

  await page.getByRole("radio", { name: /^Voor mijn werk/ }).check();
  await page.getByRole("radio", { name: /^Stevig/ }).check();
  const [onboarding] = await Promise.all([
    page.waitForRequest(
      (request) => request.method() === "POST" && request.url().endsWith("/api/me/onboarding"),
    ),
    page.getByRole("button", { name: /^Start met leren/ }).click(),
  ]);
  expect(onboarding.postDataJSON()).toEqual({
    support_mode: "nl",
    stage_id: "a1",
    daily_goal_points: 30,
    stated_goal: "werk",
  });
  await expect(page.getByTestId("how-it-works").locator(".how-card")).toHaveCount(4);
  expect(todayCalls).toEqual([]);

  await page.getByRole("button", { name: next }).click();
  await expect(
    page.getByTestId("writing-progress").or(page.getByText(/aflevering verschijnt op Vandaag/)),
  ).toBeVisible();
  const starter = page.getByTestId("starter-words");
  await expect(starter.getByRole("checkbox").first()).toBeVisible();
  await expect(starter.getByRole("button", { name: /^Kies woorden om te bewaren/ })).toBeDisabled();
  await starter.getByRole("checkbox").nth(0).check();
  await starter.getByRole("checkbox").nth(1).check();
  await starter.getByRole("button", { name: /^Bewaar 2 woorden/ }).click();
  await expect(starter.getByRole("status")).toContainText("2 woorden bewaard.");
  expect(wordPosts).toHaveLength(2);
  for (const body of wordPosts) {
    expect(body.source_kind).toBe("library");
    expect(String(body.source_id)).not.toBe("");
  }

  const stored = await profile(page);
  expect(stored.onboarded_at).not.toBeNull();
  expect(stored).toMatchObject({
    stage_id: "a1",
    daily_goal_points: 30,
    support_mode: "nl",
    stated_goal: "werk",
  });

  await page.getByRole("link", { name: /^Naar Vandaag/ }).click();
  await expect(page).toHaveURL(/\/$/);
  await expect(page.getByTestId("study-dashboard")).toBeVisible();
  await expect(page.getByRole("link", { name: /^Verder met A1/ })).toBeVisible();
  await page.goto("/welkom");
  await expect(page.getByTestId("how-it-works")).toBeVisible();
  await expect(page.getByTestId("welcome-flow")).toHaveCount(0);
});

test("at pre-A1 the first activity is the alphabet", async ({ page }) => {
  await forgetOnboarding(page);
  await page.goto("/welkom");
  await page.getByRole("radio", { name: /^Nederlands met Engelse hulp/ }).check();
  await page.getByRole("button", { name: next }).click();
  await page.getByRole("radio", { name: /^Ik begin bij nul/ }).check();
  await page.getByRole("button", { name: next }).click();
  await page.getByRole("button", { name: /^Start met leren/ }).click();
  await page.getByRole("button", { name: next }).click();
  await expect(page.getByRole("heading", { name: /^Het alfabet/ })).toBeVisible();
  expect((await profile(page)).stage_id).toBe("pre-a1");
});

test("a daily goal set in Instellingen before the welcome is kept", async ({ page }) => {
  await forgetOnboarding(page);
  await page.evaluate(async () => {
    await fetch("/api/me", {
      method: "PATCH",
      headers: { "X-Requested-With": "fetch", "Content-Type": "application/json" },
      body: JSON.stringify({ daily_goal_points: 30 }),
    });
  });
  await page.goto("/welkom");
  await page.getByRole("radio", { name: /^Nederlands met Engelse hulp/ }).check();
  await page.getByRole("button", { name: next }).click();
  await page.getByRole("radio", { name: /^Ik ken een paar woorden/ }).check();
  await page.getByRole("button", { name: next }).click();
  await expect(page.getByRole("radio", { name: /^Stevig/ })).toBeChecked();
  await page.getByRole("button", { name: /^Start met leren/ }).click();
  await expect(page.getByTestId("how-it-works")).toBeVisible();
  expect((await profile(page)).daily_goal_points).toBe(30);
});

test("settings stays open before the welcome is finished", async ({ page }) => {
  await forgetOnboarding(page);
  await page.goto("/settings");
  await expect(page).toHaveURL(/\/settings$/);
  await expect(page.getByTestId("learning-preferences")).toBeVisible();
});

test("the explanation can be opened again from settings", async ({ page }) => {
  await page.goto("/settings");
  await page.getByRole("link", { name: "Hoe werkt Taalstudio?" }).click();
  await expect(page).toHaveURL(/\/welkom\?stap=uitleg$/);
  await expect(page.getByTestId("how-it-works")).toBeVisible();
  await expect(page.getByRole("navigation", { name: "Hoofdmenu", exact: true })).toHaveCount(0);
});

for (const width of [1440, 390, 320]) {
  test(`the welcome is accessible and fits at ${width}px`, async ({ page }) => {
    await forgetOnboarding(page);
    await page.setViewportSize({ width, height: width <= 390 ? 844 : 1000 });
    await page.goto("/welkom");
    await expect(page.getByTestId("welcome-flow")).toBeVisible();
    for (const step of ["taal", "niveau"]) {
      await expect
        .poll(() => page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth))
        .toBe(true);
      for (const card of await page.locator(".choice-card").all()) {
        expect((await card.boundingBox())?.height ?? 0).toBeGreaterThanOrEqual(44);
      }
      const results = await new AxeBuilder({ page })
        .withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"])
        .analyze();
      expect(results.violations, step).toEqual([]);
      if (step === "taal") await page.getByRole("button", { name: next }).click();
    }
    await page.goto("/welkom?stap=uitleg");
    await expect(page.getByTestId("how-it-works")).toBeVisible();
    await expect
      .poll(() => page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth))
      .toBe(true);
    const results = await new AxeBuilder({ page })
      .withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"])
      .analyze();
    expect(results.violations).toEqual([]);
  });
}
