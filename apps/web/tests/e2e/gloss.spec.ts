import AxeBuilder from "@axe-core/playwright";
import type { Page } from "@playwright/test";
import { expect, test } from "./fixtures/test";

/** With glosses on and every support language selected, the shell still fits and passes axe. */
// Persian appears here once the owner marks the navigation batch reviewed in lib/copy/review.ts (O2).
const headers = { "X-Requested-With": "fetch" };

async function profile(page: Page, data: Record<string, unknown>) {
  const response = await page.request.patch("/api/me", { headers, data });
  expect(response.ok()).toBe(true);
}

async function accessible(page: Page) {
  const results = await new AxeBuilder({ page })
    .withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"])
    .analyze();
  expect(results.violations).toEqual([]);
}

for (const width of [1440, 390, 320]) {
  test(`glossed chrome in nl-fa-en fits and is accessible at ${width}px`, async ({ page }) => {
    await profile(page, { gloss_mode: "on", support_mode: "nl-fa-en" });
    await page.setViewportSize({ width, height: 900 });
    await page.goto("/");
    const nav = page.getByRole("navigation", { name: width > 1050 ? "Hoofdmenu" : "Mobiel hoofdmenu" });
    await expect(nav.getByRole("link", { name: /^Vandaag/ })).toBeVisible();
    // the navigation's Persian waits for review (O2), so learners who also chose English see English
    await expect(nav.locator("[lang=fa]")).toHaveCount(0);
    const glosses = nav.locator("a .ui-gloss[lang=en]");
    // the glosses are there at every width; under 360px they are hidden, not missing
    await expect(glosses).toHaveCount(width > 1050 ? 7 : 5);
    if (width >= 360) await expect(glosses.first()).toBeVisible();
    else await expect(glosses.first()).toBeHidden();
    await expect
      .poll(() => page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth))
      .toBe(true);
    if (width >= 360 && width <= 1050) {
      // the glossed bar is taller; the end of the page must still clear it. Today loads its plan after the
      // shell, so measure once it is there and the page has stopped growing.
      await expect(page.getByRole("heading", { level: 1 })).toBeVisible();
      await expect
        .poll(() =>
          page.evaluate(() => {
            window.scrollTo(0, document.documentElement.scrollHeight);
            const footer = document.querySelector(".site-footer")?.getBoundingClientRect();
            const bar = document.querySelector(".mobile-nav")?.getBoundingClientRect();
            return !!footer && !!bar && footer.bottom <= bar.top + 1;
          }),
        )
        .toBe(true);
    }
    await accessible(page);
  });
}

test("glossed navigation fits every destination on a phone", async ({ page }) => {
  await profile(page, { gloss_mode: "on", support_mode: "nl-fa-en" });
  await page.setViewportSize({ width: 390, height: 844 });
  for (const path of ["/leerpad", "/verhalen", "/spreken", "/woorden", "/progress", "/settings"]) {
    await page.goto(path);
    await expect(page.getByRole("heading", { level: 1 }).first()).toBeVisible();
    await expect(
      page.getByRole("navigation", { name: "Mobiel hoofdmenu" }).locator(".ui-gloss").first(),
    ).toBeVisible();
    await expect
      .poll(() => page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth), {
        message: path,
      })
      .toBe(true);
    await accessible(page);
  }
});

test("glosses follow the level on auto and disappear with the preference off", async ({ page }) => {
  const glosses = page.getByRole("navigation", { name: "Hoofdmenu", exact: true }).locator(".ui-gloss");
  await profile(page, { gloss_mode: "auto", stage_id: "a1" });
  await page.goto("/");
  await expect(glosses.first()).toBeVisible();
  await profile(page, { gloss_mode: "auto", stage_id: "b2" });
  await page.reload();
  await expect(
    page.getByRole("navigation", { name: "Hoofdmenu", exact: true }).getByRole("link").first(),
  ).toBeVisible();
  await expect(glosses).toHaveCount(0);
  await profile(page, { gloss_mode: "off", stage_id: "a1" });
  await page.reload();
  await expect(
    page.getByRole("navigation", { name: "Hoofdmenu", exact: true }).getByRole("link").first(),
  ).toBeVisible();
  await expect(glosses).toHaveCount(0);
});
