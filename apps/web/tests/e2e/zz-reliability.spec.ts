import { expect, test } from "@playwright/test";

test("a failed hint request reveals nothing and offers a safe retry", async ({ page }) => {
  await page.goto("/missions/appointment-change");
  const ladder = page.locator('[data-step="read-reminder"] .help-ladder').last();
  await page.route("**/api/practice/sessions/*/help", (route) => route.abort(), { times: 1 });
  await ladder.getByRole("button", { name: /Hulp niveau 1/ }).click();
  await expect(ladder.getByRole("alert")).toContainText("nog niet getoond");
  await expect(ladder).toHaveAttribute("data-help-revealed", "0");
  await expect(ladder.locator(".rung")).toHaveCount(0);
  await ladder.getByRole("button", { name: /Hulp niveau 1/ }).click();
  await expect(ladder).toHaveAttribute("data-help-revealed", "1");
});

test("clearing the draft stays cleared after reload", async ({ page }) => {
  await page.goto("/missions/appointment-change");
  await page.getByRole("button", { name: /Schrijven: het bericht/ }).click();
  await page.getByTestId("writing-input").fill("Dit is een tijdelijk bericht.");
  await expect(page.getByTestId("autosave-status")).toHaveText(/^bewaard /);
  await page.getByTestId("writing-input").fill("");
  await expect(page.getByTestId("autosave-status")).toHaveText(/^bewaard /);
  await page.reload();
  await page.getByRole("button", { name: /Schrijven: het bericht/ }).click();
  await expect(page.getByTestId("writing-input")).toHaveValue("");
});

test("changing lesson step flushes the latest draft before navigation", async ({ page }) => {
  await page.goto("/missions/appointment-change");
  await page.getByRole("button", { name: /Schrijven: het bericht/ }).click();
  let saves = 0;
  await page.route("**/api/practice/sessions/*/drafts/write-message", async (route) => {
    saves++;
    await new Promise((resolve) => setTimeout(resolve, 300));
    await route.continue();
  });
  await page.getByTestId("writing-input").fill("Eerste versie van het bericht.");
  await expect.poll(() => saves).toBeGreaterThan(0);
  const latest = "Dit is de laatste versie van mijn bericht.";
  await page.getByTestId("writing-input").fill(latest);
  await page.getByRole("button", { name: /Lezen: de herinnering/ }).click();
  await expect(page.getByTestId("reading-text")).toBeVisible();
  await page.getByRole("button", { name: /Schrijven: het bericht/ }).click();
  await expect(page.getByTestId("writing-input")).toHaveValue(latest);
  await page.reload();
  await page.getByRole("button", { name: /Schrijven: het bericht/ }).click();
  await expect(page.getByTestId("writing-input")).toHaveValue(latest);
});

test("a failed draft save keeps the learner on the writing step", async ({ page }) => {
  await page.goto("/missions/appointment-change");
  await page.getByRole("button", { name: /Schrijven: het bericht/ }).click();
  await page.route("**/api/practice/sessions/*/drafts/write-message", (route) => route.abort());
  await page.getByTestId("writing-input").fill("Bewaar dit bericht voordat ik verderga.");
  await page.getByRole("button", { name: /Lezen: de herinnering/ }).click();
  await expect(page.getByTestId("writing-input")).toBeVisible();
  await expect(page.getByRole("button", { name: "Opnieuw bewaren" })).toBeVisible();
  await page.unroute("**/api/practice/sessions/*/drafts/write-message");
  await page.getByRole("button", { name: "Opnieuw bewaren" }).click();
  await expect(page.getByTestId("autosave-status")).toHaveText(/^bewaard /);
});

test("home shows the staged learning path without a fabricated aggregate score", async ({ page }, testInfo) => {
  await page.goto("/");
  const overview = page.getByTestId("learning-overview");
  await expect(overview.getByTestId("curriculum-path").locator("li")).toHaveCount(12);
  await expect(overview).not.toContainText("Laden…");
  await expect(page.getByRole("link", { name: /Open pre-A1:/ })).toBeVisible();
  await expect(overview).not.toContainText(/A3|totaalscore|azure-small|feedback-v1/);
  await expect(page.getByRole("heading", { name: "Kleine stappen. Echte gesprekken." })).toBeVisible();
  await testInfo.attach("home-desktop", { body: await page.screenshot({ fullPage: true }), contentType: "image/png" });
  await page.setViewportSize({ width: 390, height: 844 });
  await testInfo.attach("home-phone-width", { body: await page.screenshot({ fullPage: true }), contentType: "image/png" });
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
});
