import AxeBuilder from "@axe-core/playwright";
import { expect, test } from "@playwright/test";

/** The five destinations: bottom tabs on a phone, sidebar on a desktop, one current item at a time. */

const tabs = ["Vandaag", "Leren", "Verhalen", "Spreken", "Woorden"];

for (const width of [390, 320]) {
  test(`five tabs fit at ${width}px with 44px targets and no axe violations`, async ({ page }) => {
    await page.setViewportSize({ width, height: 844 });
    await page.goto("/");
    const nav = page.getByRole("navigation", { name: "Mobiel hoofdmenu" });
    for (const name of tabs) await expect(nav.getByRole("link", { name })).toBeVisible();
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
    for (const link of await nav.getByRole("link").all()) {
      const box = await link.boundingBox();
      expect(box?.width ?? 0).toBeGreaterThanOrEqual(44);
      expect(box?.height ?? 0).toBeGreaterThanOrEqual(44);
    }
    await expect(page.getByRole("link", { name: "Mijn account en instellingen" })).toBeVisible();
    const results = await new AxeBuilder({ page })
      .withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"])
      .analyze();
    expect(results.violations).toEqual([]);
  });
}

test("the current destination follows the route", async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  const nav = page.getByRole("navigation", { name: "Mobiel hoofdmenu" });
  for (const [path, name] of [
    ["/learn/a1", "Leren"],
    ["/videos", "Verhalen"],
    ["/missions/appointment-change", "Spreken"],
    ["/speech-check", "Spreken"],
    ["/woorden", "Woorden"],
  ] as const) {
    await page.goto(path);
    await expect(nav.getByRole("link", { name })).toHaveAttribute("aria-current", "page");
    await expect(nav.locator('a[aria-current="page"]')).toHaveCount(1);
  }
  await page.goto("/settings");
  await expect(nav.locator('a[aria-current="page"]')).toHaveCount(0);
});

test("the sidebar marks the rooms and keeps 44px links", async ({ page }) => {
  await page.goto("/settings");
  const menu = page.getByRole("navigation", { name: "Hoofdmenu", exact: true });
  await expect(menu.getByRole("link", { name: "Instellingen" })).toHaveAttribute("aria-current", "page");
  await expect(menu.locator('a[aria-current="page"]')).toHaveCount(1);
  for (const link of await menu.getByRole("link").all()) {
    const box = await link.boundingBox();
    expect(box?.height ?? 0).toBeGreaterThanOrEqual(44);
  }
  await page.goto("/videos");
  await expect(menu.getByRole("link", { name: "Verhalen" })).toHaveAttribute("aria-current", "page");
  await expect(
    page.getByRole("navigation", { name: "Verhalen en video's" }).getByRole("link", { name: "Video's" }),
  ).toHaveAttribute("aria-current", "page");
});

test("the Spreken hub gathers conversations, missions and the studio", async ({ page }) => {
  await page.goto("/spreken");
  await expect(page.getByRole("heading", { level: 1 })).toContainText("Nederlands");
  await expect(page.getByTestId("mission-catalog").locator("article")).toHaveCount(4);
  await expect(page.getByRole("link", { name: /spraakstudio/i })).toBeVisible();
  const results = await new AxeBuilder({ page })
    .withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"])
    .analyze();
  expect(results.violations).toEqual([]);
});
