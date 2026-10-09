import type { Page } from "@playwright/test";
import { expect, test } from "./fixtures/test";

/** The learning preferences in Instellingen are the one place the level, goal and glosses are set. */
async function me(page: Page) {
  const response = await page.request.get("/api/me", { headers: { "X-Requested-With": "fetch" } });
  return (await response.json()).profile as {
    stage_id: string;
    daily_goal_points: number;
    gloss_mode: string;
    support_mode: string | null;
  };
}

test("level, goal and glosses persist through the profile", async ({ page }) => {
  await page.goto("/settings");
  await expect(page.getByRole("heading", { name: "Mijn leerprofiel" })).toBeVisible();
  const preferences = page.getByTestId("learning-preferences");
  await preferences.getByLabel("Mijn niveau").selectOption("a2");
  await expect(preferences.getByText("Niveau aangepast.")).toBeVisible();
  await preferences.getByLabel("Mijn dagdoel").selectOption("30");
  await expect(preferences.getByText("Dagdoel aangepast.")).toBeVisible();
  await preferences.getByLabel("Vertalingen onder de knoppen").selectOption("on");
  await expect(preferences.getByText("Voorkeur bewaard.")).toBeVisible();
  await expect.poll(async () => (await me(page)).stage_id).toBe("a2");
  const profile = await me(page);
  expect(profile.daily_goal_points).toBe(30);
  expect(profile.gloss_mode).toBe("on");
  await page.reload();
  await expect(page.getByTestId("learning-preferences").getByLabel("Mijn niveau")).toHaveValue("a2");
  await expect(page.getByTestId("learning-preferences").getByLabel("Mijn dagdoel")).toHaveValue("30");
});

test("the support language in the preferences and in the header are the same setting", async ({ page }) => {
  await page.goto("/settings");
  await page.getByTestId("learning-preferences").getByLabel("Taal voor hulp").selectOption("nl-fa");
  await expect(page.getByLabel("Taalhulp / language")).toHaveValue("nl-fa");
  await expect.poll(async () => (await me(page)).support_mode).toBe("nl-fa");
});
