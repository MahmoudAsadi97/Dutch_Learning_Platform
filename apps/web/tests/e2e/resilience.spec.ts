import { expect, test } from "./fixtures/test";

/** Disconnected state and recovery: the banner appears when the API stops answering and clears on retry. */
test.describe("resilience", () => {
  test("the connection banner appears when calls fail and clears after a successful retry", async ({
    page,
  }) => {
    await page.goto("/");
    await expect(page.getByTestId("study-dashboard")).toBeVisible();
    await expect(page.getByTestId("connection-banner")).toHaveCount(0);

    await page.route("**/api/**", (route) => route.abort("connectionrefused"));
    await page
      .getByRole("navigation", { name: "Hoofdmenu", exact: true })
      .getByRole("link", { name: /^Leren/ })
      .click();
    await page.getByRole("link", { name: "A2 · Lezen", exact: true }).click();
    const banner = page.getByTestId("connection-banner");
    await expect(banner).toBeVisible();
    await expect(banner).toHaveAttribute("data-state", "api-down");
    // Failed catalogue requests must not pretend that the chosen level has no topics.
    const topics = page.locator(".study-topic-library");
    await expect(topics.getByRole("alert")).toBeVisible();
    await expect(topics.locator(".study-empty")).toHaveCount(0);
    await expect(topics.locator(".study-topic-card")).toHaveCount(0);

    await page.locator("#study-stage").selectOption("a1");
    await expect(page.locator("#study-stage")).toHaveValue("a1");
    await expect(topics.getByRole("alert")).toBeVisible();
    await expect(topics.locator(".study-empty")).toHaveCount(0);
    await page.unroute("**/api/**");
    await banner.getByRole("button", { name: "Opnieuw proberen" }).click();
    await expect(page.getByTestId("connection-banner")).toHaveCount(0);
    await topics.getByRole("button", { name: /^Opnieuw proberen/ }).click();
    await expect(topics.getByRole("alert")).toHaveCount(0);
    await expect(topics.locator(".study-topic-card").first()).toBeVisible();
  });

  test("settings shows the budget counters and the empty pricing table", async ({ page }) => {
    await page.goto("/settings");
    const usage = page.getByTestId("usage-panel");
    await expect(usage).toContainText("modeloproepen");
    await expect(usage).toContainText("seconden audio");
    await expect(page.getByTestId("pricing-note")).toContainText("Prijstabel leeg");
  });
});
