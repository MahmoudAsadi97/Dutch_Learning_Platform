import { expect, test } from "@playwright/test";

const OWNER = process.env.E2E_OWNER_EMAIL ?? "owner@example.com";

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

    // questions are judged by the API (a session is started on first use) and stored as evidence
    await page.getByLabel(/Woensdag om 14.00 uur/).check();
    await page.getByLabel(/Eén dag op voorhand bellen/).check();
    await page.getByRole("button", { name: /Controleer/ }).click();
    await expect(page.getByTestId("score")).toHaveText("2 van 2 juist");
    await expect(page.getByTestId("read-reminder-done")).toBeVisible();
    await expect(page.getByTestId("session-id")).toContainText(/[0-9a-f-]{36}/);

    // four skill records exist for the learner and mission
    await expect(page.getByTestId("skill-records").locator("li")).toHaveCount(4);

    await page.screenshot({ path: testInfo.outputPath(`lesson-${testInfo.project.name}.png`), fullPage: true });
  });

  test("the session card starts a session through the CSRF-protected proxy path or shows the resumed one", async ({ page }) => {
    await page.goto("/missions/appointment-change");
    const start = page.getByRole("button", { name: "Start een oefensessie" });
    const id = page.getByTestId("session-id");
    await expect(start.or(id)).toBeVisible();
    if (await start.isVisible()) await start.click();
    await expect(id).toContainText(/[0-9a-f-]{36}/);
    await expect(id).toContainText(/stap: (read-reminder|speak-call)/);
  });

  test("the reading step offers feedback grounded in the recorded answers", async ({ page }) => {
    await page.goto("/missions/appointment-change");
    const panel = page.getByTestId("read-reminder-feedback");
    await panel.getByTestId("read-reminder-feedback-ask").click();
    const report = panel.getByTestId("read-reminder-feedback-report");
    await expect(report).toBeVisible({ timeout: 20_000 });
    await expect(page.getByTestId("read-reminder-feedback-points").locator("li")).toHaveCount(2);
    await expect(page.getByTestId("read-reminder-feedback-dropped")).toContainText("E99");
    await expect(report.locator('[data-kind="strength"]')).toBeVisible();
    await expect(report).toContainText("1 punt(en) weggelaten zonder geldig bewijs");
    await expect(report).toContainText("fixture · fixture-chat-v1 · feedback-v1");
    await expect(report.locator('[lang="fa"]').first()).toBeVisible();
  });
});

test.describe("settings", () => {
  test("shows the fixture principal and the preflight table", async ({ page }) => {
    await page.goto("/settings");
    await expect(page.getByTestId("principal")).toContainText(OWNER);
    await expect(page.getByTestId("principal")).toContainText("fixture");
    const rows = page.getByTestId("preflight").locator("tbody tr");
    await expect(rows).toHaveCount(10);
    await expect(page.getByTestId("preflight")).toContainText("ffmpeg");
  });
});
