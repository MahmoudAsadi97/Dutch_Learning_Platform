import { expect, test } from "@playwright/test";

test("the library opens three different four-skill lessons on a phone width", async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto("/missions");
  const catalog = page.getByTestId("mission-catalog");
  await expect(catalog.locator("article")).toHaveCount(4);
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
  for (const [id, text] of [["lunch-order", "Lunchbar Linden"], ["shop-return", "Winkel Wilg"], ["course-message", "Beste cursist"]]) {
    await page.goto("/missions");
    await catalog.locator(`a[href="/missions/${id}"]`).click();
    await expect(page.getByTestId("reading-text")).toContainText(text);
    await expect(page.locator(".step-list li")).toHaveCount(5);
  }
});

test("lunch practice saves answers, a choice-based conversation and a message", async ({ page }) => {
  await page.goto("/missions/lunch-order");
  await page.getByLabel(/^€ 6/).check();
  await page.getByLabel(/^Aan de toonbank/).check();
  await page.getByTestId("read-check").click();
  await expect(page.getByTestId("score")).toHaveText("2 van 2 juist");

  await page.locator(".step-list button").nth(1).click();
  await page.getByTestId("play-clip").click();
  await expect(page.getByTestId("play-count")).toContainText("1× beluisterd");
  await page.getByLabel(/^Soep/).check();
  await page.getByLabel(/^Ja\b/).check();
  await page.getByTestId("listen-check").click();
  await expect(page.getByTestId("score")).toHaveText("2 van 2 juist");

  await page.locator(".step-list button").nth(2).click();
  // Reading already started this mission's shared practice session.
  await expect(page.getByTestId("conversation")).toBeVisible();
  const input = page.getByTestId("typed-input");
  for (const [index, text] of ["Ik wil lunchen.", "Een broodje kaas, alstublieft.", "Ja, dat is goed."].entries()) {
    await input.fill(text);
    await page.getByTestId("typed-send").click();
    await expect(page.getByTestId("turn-character")).toHaveCount(index + 2);
  }
  await expect(page.getByTestId("appointment-panel")).toContainText("✓ bevestigd");
  await expect(page.getByTestId("appointment-panel")).not.toContainText("nieuw moment");
  await expect(page.getByTestId("conversation")).not.toContainText("fixture-chat");

  await page.locator(".step-list button").nth(3).click();
  await page.getByTestId("writing-input").fill("Dag Sara, ik bestel vandaag een broodje kaas voor vijf euro. Ik eet hier in de lunchbar. Kom je ook?");
  await page.getByTestId("writing-submit").click();
  await expect(page.getByTestId("writing-done")).toBeVisible();
  await page.goto("/progress");
  await page.getByText("Voortgang in praktijkgesprekken", { exact: true }).click();
  await page.getByLabel("Oefenmissie", { exact: true }).selectOption("lunch-order");
  await expect(page.locator(".progress-card")).toHaveCount(4);
});
