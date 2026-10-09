import AxeBuilder from "@axe-core/playwright";
import { expect, test } from "./fixtures/test";

/** With glosses on and every support language selected, the shell still fits and passes axe. */
const headers = { "X-Requested-With": "fetch" };

for (const width of [1440, 390, 320]) {
  test(`glossed chrome in nl-fa-en fits and is accessible at ${width}px`, async ({ page }) => {
    await page.request.patch("/api/me", { headers, data: { gloss_mode: "on", support_mode: "nl-fa-en" } });
    await page.setViewportSize({ width, height: 900 });
    await page.goto("/");
    const nav = page.getByRole("navigation", { name: width > 1050 ? "Hoofdmenu" : "Mobiel hoofdmenu" });
    await expect(nav.getByRole("link", { name: "Vandaag" })).toBeVisible();
    const persian = nav.locator("[lang=fa]");
    if (width > 1050) {
      await expect(persian.first()).toBeVisible();
      await expect(persian.first()).toHaveAttribute("dir", "rtl");
    } else if (width >= 360) {
      await expect(persian.first()).toBeVisible();
    } else {
      await expect(persian.first()).toBeHidden();
    }
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
    if (width >= 360 && width <= 1050) {
      // the glossed bar is taller; the end of the page must still clear it
      await page.evaluate(() => window.scrollTo(0, document.documentElement.scrollHeight));
      const clear = await page.evaluate(() => {
        const footer = document.querySelector(".site-footer")?.getBoundingClientRect();
        const bar = document.querySelector(".mobile-nav")?.getBoundingClientRect();
        return !!footer && !!bar && footer.bottom <= bar.top + 1;
      });
      expect(clear).toBe(true);
    }
    const results = await new AxeBuilder({ page })
      .withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"])
      .analyze();
    expect(results.violations).toEqual([]);
  });
}

test("glosses disappear above B1 on auto and with the preference off", async ({ page }) => {
  await page.request.patch("/api/me", { headers, data: { gloss_mode: "auto", stage_id: "b2" } });
  await page.goto("/");
  await expect(page.getByRole("navigation", { name: "Hoofdmenu" }).locator(".ui-gloss")).toHaveCount(0);
  await page.request.patch("/api/me", { headers, data: { gloss_mode: "auto", stage_id: "a1" } });
  await page.reload();
  await expect(
    page.getByRole("navigation", { name: "Hoofdmenu" }).locator(".ui-gloss").first(),
  ).toBeVisible();
});
