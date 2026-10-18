import AxeBuilder from "@axe-core/playwright";
import { expect, test } from "./fixtures/test";

/** Content status belongs beside the material, rather than on navigation-only screens. */

for (const path of ["/", "/leerpad"]) {
  test(`${path} keeps content warnings out of the navigation overview`, async ({ page }) => {
    await page.goto(path);
    await expect(page.getByRole("heading", { level: 1 })).toBeVisible();
    await expect(page.locator("[data-honesty]")).toHaveCount(0);
    await expect(page.locator(".course-note", { hasText: /taalmodel|nagekeken|certificaat/ })).toHaveCount(0);
  });
}

test("a final check has one explanation and a guided lesson discloses its pending language review", async ({
  page,
}) => {
  await page.goto("/learn/a1/test");
  await expect(page.locator('[data-honesty="check"]')).toHaveCount(1);
  await page.goto("/learn/a2?skill=reading&topic=family");
  await expect(page.locator(".study-review-note")).toHaveCount(1);
  await expect(page.locator(".study-review-note")).toContainText("Taalreview in voorbereiding");
  await expect(page.locator(".study-review-note")).toContainText("Language review pending");
});

test("the chip explains itself in the support languages and leads to /over", async ({ page }) => {
  await page.goto("/learn/pre-a1?view=alphabet");
  await page.locator('[data-honesty="unreviewed"]').click();
  const dialog = page.getByRole("dialog", { name: /Nog niet nagekeken/ });
  await expect(dialog).toBeVisible();
  await expect(dialog).toContainText("een taaldocent heeft ze nog niet nagekeken");
  await expect(dialog).toContainText("a language teacher has not reviewed it yet");
  await expect(dialog.locator('[lang="fa"]')).toHaveCount(0);
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
