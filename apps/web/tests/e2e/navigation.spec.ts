import AxeBuilder from "@axe-core/playwright";
import { expect, test } from "./fixtures/test";

/** Four stable destinations: bottom tabs on a phone, sidebar on desktop, one current item at a time. */

const tabs = ["Dashboard", "Leren", "Voortgang", "Instellingen"];

for (const width of [390, 320]) {
  test(`four tabs fit at ${width}px with 44px targets and no axe violations`, async ({ page }) => {
    await page.setViewportSize({ width, height: 844 });
    await page.goto("/");
    await expect(page.getByTestId("study-dashboard")).toBeVisible();
    const nav = page.getByRole("navigation", { name: "Mobiel hoofdmenu" });
    await expect(nav.getByRole("link")).toHaveCount(4);
    for (const name of tabs) await expect(nav.getByRole("link", { name })).toBeVisible();
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
    expect(await nav.evaluate((element) => element.getBoundingClientRect().right <= window.innerWidth)).toBe(
      true,
    );
    for (const link of await nav.getByRole("link").all()) {
      const box = await link.boundingBox();
      expect(box?.width ?? 0).toBeGreaterThanOrEqual(44);
      expect(box?.height ?? 0).toBeGreaterThanOrEqual(44);
      // a centred label that is wider than its tab spills out on both sides without moving scrollWidth;
      // measure the text itself (the Dutch and any gloss), since the wrapper has no box without a gloss
      const fits = await link.evaluate((element) => {
        const tab = element.getBoundingClientRect();
        const lines = [...element.querySelectorAll(".ui-text-nl, .ui-gloss")].map((span) =>
          span.getBoundingClientRect(),
        );
        return (
          lines.length > 0 &&
          lines.every(
            (line) => line.width === 0 || (line.left >= tab.left - 0.5 && line.right <= tab.right + 0.5),
          )
        );
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
    ["/videos", "Leren"],
    ["/missions/appointment-change", "Leren"],
    ["/speech-check", "Leren"],
    ["/woorden", "Leren"],
  ] as const) {
    await page.goto(path);
    await expect(nav.getByRole("link", { name })).toHaveAttribute("aria-current", "page");
    await expect(nav.locator('a[aria-current="page"]')).toHaveCount(1);
  }
  await page.goto("/settings");
  await expect(nav.getByRole("link")).toHaveCount(4);
  await expect(nav.getByRole("link", { name: "Instellingen" })).toHaveAttribute("aria-current", "page");
  await expect(nav.locator('a[aria-current="page"]')).toHaveCount(1);
});

test("on a phone account and progress are available from the profile and the main navigation", async ({
  page,
}) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto("/");
  await page.getByRole("link", { name: "Mijn account en instellingen" }).click();
  await expect(page).toHaveURL(/\/settings$/);
  const mobile = page.getByRole("navigation", { name: "Mobiel hoofdmenu" });
  await expect(mobile.getByRole("link", { name: "Instellingen" })).toHaveAttribute("aria-current", "page");
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
  await expect(menu.getByRole("link", { name: "Leren" })).toHaveAttribute("aria-current", "page");
  await expect(page).toHaveURL(/\/learn\/a1\?skill=reading/);
  await expect(page.getByRole("link", { name: "Video's", exact: true })).toHaveCount(0);
});

for (const width of [1440, 390, 320]) {
  test(`legacy speaking links preserve level and lead to the four-skill workspace at ${width}px`, async ({
    page,
  }) => {
    await page.setViewportSize({ width, height: width <= 390 ? 844 : 1000 });
    await page.goto("/spreken?stage=pre-a2");
    await expect(page).toHaveURL(/\/learn\/pre-a2\?skill=speaking/);
    const stage = page.locator("#study-stage");
    await expect(stage).toHaveValue("pre-a2");
    await expect(stage.locator("option")).toHaveCount(12);
    const skills = page.getByRole("navigation", { name: "Kies een vaardigheid" });
    await expect(skills.getByRole("link")).toHaveCount(4);
    await expect(skills.getByRole("link", { name: /^Spreken/ })).toHaveAttribute("aria-current", "page");
    await stage.selectOption("a2");
    await expect(page).toHaveURL(/\/learn\/a2\?skill=speaking/);
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
    const results = await new AxeBuilder({ page })
      .withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"])
      .analyze();
    expect(results.violations).toEqual([]);
  });
}
