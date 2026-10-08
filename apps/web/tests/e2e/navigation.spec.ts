import AxeBuilder from "@axe-core/playwright";
import { expect, test } from "@playwright/test";

/** The five destinations: bottom tabs on a phone, sidebar on a desktop, one current item at a time. */

const tabs = ["Vandaag", "Leren", "Verhalen", "Spreken", "Woorden"];

for (const width of [390, 320]) {
  test(`five tabs fit at ${width}px with 44px targets and no axe violations`, async ({ page }) => {
    await page.setViewportSize({ width, height: 844 });
    await page.goto("/");
    // measure once Today has rendered, so the layout under the bar is the real one
    await expect(page.getByRole("img", { name: /dag(en)? op rij/ })).toBeVisible();
    const nav = page.getByRole("navigation", { name: "Mobiel hoofdmenu" });
    await expect(nav.getByRole("link")).toHaveCount(5);
    for (const name of tabs) await expect(nav.getByRole("link", { name })).toBeVisible();
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
    expect(await nav.evaluate((element) => element.getBoundingClientRect().right <= window.innerWidth)).toBe(
      true,
    );
    for (const link of await nav.getByRole("link").all()) {
      const box = await link.boundingBox();
      expect(box?.width ?? 0).toBeGreaterThanOrEqual(44);
      expect(box?.height ?? 0).toBeGreaterThanOrEqual(44);
      // a centred label that is wider than its tab spills out on both sides without moving scrollWidth
      const fits = await link.evaluate((element) => {
        const tab = element.getBoundingClientRect();
        const label = element.querySelector("span")?.getBoundingClientRect();
        return !!label && label.left >= tab.left - 0.5 && label.right <= tab.right + 0.5;
      });
      expect(fits).toBe(true);
    }
    const home = page.getByRole("link", { name: "Taalstudio, startpagina" });
    const homeBox = await home.boundingBox();
    expect(homeBox?.width ?? 0).toBeGreaterThanOrEqual(44);
    expect(homeBox?.height ?? 0).toBeGreaterThanOrEqual(44);
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
  await expect(nav.getByRole("link")).toHaveCount(5);
  await expect(nav.locator('a[aria-current="page"]')).toHaveCount(0);
});

test("on a phone the rooms are reached through the profile button and their tabs", async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto("/");
  await page.getByRole("link", { name: "Mijn account en instellingen" }).click();
  await expect(page).toHaveURL(/\/settings$/);
  const rooms = page.getByRole("navigation", { name: "Voortgang en instellingen" });
  await expect(rooms.getByRole("link", { name: "Instellingen" })).toHaveAttribute("aria-current", "page");
  await rooms.getByRole("link", { name: "Voortgang" }).click();
  await expect(page).toHaveURL(/\/progress$/);
  await expect(rooms.getByRole("link", { name: "Voortgang" })).toHaveAttribute("aria-current", "page");
  await expect(rooms.locator('a[aria-current="page"]')).toHaveCount(1);
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

test("the Verhalen tabs stay while the library is loading or has failed", async ({ page }) => {
  await page.route(/\/api\/videos(?:\?|$)/, (route) => route.abort("connectionrefused"));
  await page.goto("/videos");
  const media = page.getByRole("navigation", { name: "Verhalen en video's" });
  await expect(media.getByRole("link", { name: "Verhalen" })).toBeVisible();
  await expect(media.getByRole("link", { name: "Video's" })).toHaveAttribute("aria-current", "page");
});

for (const width of [1440, 390, 320]) {
  test(`the Spreken hub gathers conversations, missions and the studio at ${width}px`, async ({ page }) => {
    await page.setViewportSize({ width, height: width <= 390 ? 844 : 1000 });
    await page.goto("/spreken");
    await expect(page.getByRole("heading", { level: 1 })).toHaveText("Zeg het in het Nederlands.");
    const first = page.locator(".speak-choices a").first();
    await expect(first).toBeVisible();
    await expect(first).toHaveAttribute("href", /^\/learn\/[^/?]+\?(?:.*&)?skill=speaking(?:&|$)/);
    await expect(page.getByTestId("mission-catalog").locator("article")).toHaveCount(4);
    await expect(page.getByRole("link", { name: /spraakstudio/i })).toHaveAttribute("href", "/speech-check");
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
    const results = await new AxeBuilder({ page })
      .withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"])
      .analyze();
    expect(results.violations).toEqual([]);
  });
}
