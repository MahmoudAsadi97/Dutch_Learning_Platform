import { expect, test } from "@playwright/test";

/** Disconnected state and recovery: the banner appears when the API stops answering and clears on retry. */
test.describe("resilience", () => {
  test("the connection banner appears when calls fail and clears after a successful retry", async ({ page }) => {
    await page.goto("/settings");
    await expect(page.getByTestId("usage-panel")).toBeVisible();
    await expect(page.getByTestId("connection-banner")).toHaveCount(0);

    await page.route("**/api/**", (route) => route.abort("connectionrefused"));
    await page.getByRole("navigation", { name: "Hoofdmenu", exact: true }).getByRole("link", { name: "Praktijkgesprekken" }).click();
    const banner = page.getByTestId("connection-banner");
    await expect(banner).toBeVisible();
    await expect(banner).toHaveAttribute("data-state", "api-down");

    await page.unroute("**/api/**");
    await banner.getByRole("button", { name: "Opnieuw proberen" }).click();
    await expect(page.getByTestId("connection-banner")).toHaveCount(0);
  });

  test("settings shows the budget counters and the empty pricing table", async ({ page }) => {
    await page.goto("/settings");
    const usage = page.getByTestId("usage-panel");
    await expect(usage).toContainText("modeloproepen");
    await expect(usage).toContainText("seconden audio");
    await expect(page.getByTestId("pricing-note")).toContainText("Prijstabel leeg");
  });
});
