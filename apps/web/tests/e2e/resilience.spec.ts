import { expect, test } from "./fixtures/test";

/** Disconnected state and recovery: the banner appears when the API stops answering and clears on retry. */
test.describe("resilience", () => {
  test("the connection banner appears when calls fail and clears after a successful retry", async ({
    page,
  }) => {
    await page.goto("/settings");
    await expect(page.getByTestId("usage-panel")).toBeVisible();
    await expect(page.getByTestId("connection-banner")).toHaveCount(0);

    await page.route("**/api/**", (route) => route.abort("connectionrefused"));
    await page
      .getByRole("navigation", { name: "Hoofdmenu", exact: true })
      .getByRole("link", { name: "Spreken" })
      .click();
    const banner = page.getByTestId("connection-banner");
    await expect(banner).toBeVisible();
    await expect(banner).toHaveAttribute("data-state", "api-down");
    // the Spreken hub says the conversations failed to load instead of pretending there are none
    const conversations = page.locator("section", {
      has: page.getByRole("heading", { name: "Korte gesprekken met een gesprekspartner" }),
    });
    await expect(conversations.getByRole("alert")).toContainText(
      "De extra gesprekken konden niet worden geladen.",
    );
    await expect(page.getByText(/Voor dit niveau staan hier nog geen extra gesprekken/)).toHaveCount(0);

    await page.locator("#library-hub-stage").selectOption("a1");
    await expect(conversations.getByRole("alert")).toContainText(
      "De extra gesprekken konden niet worden geladen.",
    );
    await page.unroute("**/api/**");
    await banner.getByRole("button", { name: "Opnieuw proberen" }).click();
    await expect(page.getByTestId("connection-banner")).toHaveCount(0);
    await conversations.getByRole("button", { name: "Opnieuw proberen" }).click();
    await expect(conversations.locator(".speak-choices a").first()).toBeVisible();
  });

  test("settings shows the budget counters and the empty pricing table", async ({ page }) => {
    await page.goto("/settings");
    const usage = page.getByTestId("usage-panel");
    await expect(usage).toContainText("modeloproepen");
    await expect(usage).toContainText("seconden audio");
    await expect(page.getByTestId("pricing-note")).toContainText("Prijstabel leeg");
  });
});
