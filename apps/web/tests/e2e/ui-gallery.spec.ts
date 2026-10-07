import AxeBuilder from "@axe-core/playwright";
import { expect, test } from "@playwright/test";

/** The gallery shows every primitive in every state; it is the accessibility and overflow gate for them. */
for (const width of [1440, 390, 320]) {
  test(`the UI gallery is accessible and fits at ${width}px`, async ({ page }) => {
    await page.setViewportSize({ width, height: 900 });
    await page.goto("/dev/ui");
    await expect(page.getByTestId("ui-gallery")).toBeVisible();
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
    const results = await new AxeBuilder({ page })
      .withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"])
      .analyze();
    expect(results.violations).toEqual([]);
  });
}
