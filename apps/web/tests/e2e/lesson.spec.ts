import { expect, test } from "@playwright/test";

test.describe("lesson shell: reading step", () => {
  test("renders the fixture reading step through the proxy with labels, help and questions", async ({ page }, testInfo) => {
    await page.goto("/missions/appointment-change");

    const text = page.getByTestId("reading-text");
    await expect(text).toContainText("tandarts De Smet");
    await expect(text).toHaveAttribute("lang", "nl");

    // every fixed text is labelled unreviewed until the reviewer approves it
    await expect(page.locator('[data-review="unreviewed"]').first()).toBeVisible();
    await expect(page.locator('[data-review="reviewed"]')).toHaveCount(0);

    // Persian rendering is right-to-left and hidden until asked for
    await expect(page.getByTestId("reading-text-fa")).toHaveCount(0);
    await page.getByRole("button", { name: /Perzische vertaling/ }).click();
    const persian = page.getByTestId("reading-text-fa");
    await expect(persian).toBeVisible();
    await expect(persian).toHaveAttribute("dir", "rtl");
    await expect(persian).toHaveAttribute("lang", "fa");

    // help ladder reveals rungs one at a time
    const ladder = page.locator('[data-step="read-reminder"] .help-ladder').last();
    await expect(ladder).toHaveAttribute("data-help-revealed", "0");
    await ladder.getByRole("button", { name: /Hulp niveau 1/ }).click();
    await expect(ladder).toHaveAttribute("data-help-revealed", "1");
    await ladder.getByRole("button", { name: /Hulp niveau 2/ }).click();
    await expect(ladder.locator(".rung").nth(1)).toHaveAttribute("lang", "fa");
    await ladder.getByRole("button", { name: /Hulp niveau 3/ }).click();
    await expect(ladder.locator(".rung").nth(2)).toHaveAttribute("dir", "rtl");

    // questions can be answered and checked locally
    await page.getByLabel(/Woensdag om 14.00 uur/).check();
    await page.getByLabel(/Eén dag op voorhand bellen/).check();
    await page.getByRole("button", { name: /Controleer/ }).click();
    await expect(page.getByTestId("score")).toHaveText("2 van 2 juist");

    // four skill records exist for the learner and mission
    await expect(page.getByTestId("skill-records").locator("li")).toHaveCount(4);

    await page.screenshot({ path: testInfo.outputPath(`lesson-${testInfo.project.name}.png`), fullPage: true });
  });

  test("starting a session goes through the CSRF-protected proxy path and is idempotent", async ({ page }) => {
    await page.goto("/missions/appointment-change");
    await page.getByRole("button", { name: "Start een oefensessie" }).click();
    const id = page.getByTestId("session-id");
    await expect(id).toContainText(/[0-9a-f-]{36}/);
    await expect(id).toContainText("stap: read-reminder");
  });

  test("other steps show their loaded content and an M2 notice", async ({ page }) => {
    await page.goto("/missions/appointment-change");
    await page.getByRole("button", { name: /Controle: de kapper/ }).click();
    const step = page.locator('[data-step="checkpoint-transfer"]');
    await expect(step).toContainText("geen hulp en geen herkansing");
    await expect(step).toContainText("milestone M2");
  });
});

test.describe("home", () => {
  test("shows the fixture principal and the preflight table", async ({ page }) => {
    await page.goto("/");
    await expect(page.getByTestId("principal")).toContainText("owner@example.com");
    await expect(page.getByTestId("principal")).toContainText("fixture");
    const rows = page.getByTestId("preflight").locator("tbody tr");
    await expect(rows).toHaveCount(10);
    await expect(page.getByTestId("preflight")).toContainText("ffmpeg");
  });
});
