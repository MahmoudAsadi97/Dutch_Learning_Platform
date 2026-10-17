import AxeBuilder from "@axe-core/playwright";
import { expect, test } from "./fixtures/test";

/** One honesty chip per generated or unreviewed surface, each leading to the same explanation. */

for (const [path, kind] of [
  ["/", "generated"],
  ["/leerpad", "check"],
  ["/learn/a1/test", "check"],
] as const) {
  test(`${path} carries one ${kind} chip`, async ({ page }) => {
    await page.goto(path);
    await expect(page.locator(`[data-honesty="${kind}"]`)).toHaveCount(1);
    await expect(page.locator(".course-note", { hasText: /taalmodel|nagekeken|certificaat/ })).toHaveCount(0);
  });
}

test("the chip explains itself in the support languages and leads to /over", async ({ page }) => {
  await page.goto("/");
  await page.locator('[data-honesty="generated"]').click();
  const dialog = page.getByRole("dialog", { name: /Taalmodel · niet nagekeken/ });
  await expect(dialog).toBeVisible();
  await expect(dialog).toContainText("Een taalmodel schreef deze tekst.");
  await expect(dialog).toContainText("A language model wrote this text.");
  await dialog.getByRole("link", { name: /Meer over de inhoud/ }).click();
  await expect(page).toHaveURL(/\/over$/);
  await expect(page.getByTestId("about-content").locator(".about-section")).toHaveCount(5);
});

for (const width of [1440, 390, 320]) {
  test(`/over is accessible and fits at ${width}px`, async ({ page }) => {
    await page.setViewportSize({ width, height: width <= 390 ? 844 : 1000 });
    await page.goto("/over");
    await expect(page.getByRole("heading", { level: 1 })).toContainText("Over de inhoud");
    await expect
      .poll(() => page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth))
      .toBe(true);
    const results = await new AxeBuilder({ page })
      .withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"])
      .analyze();
    expect(results.violations).toEqual([]);
  });
}
