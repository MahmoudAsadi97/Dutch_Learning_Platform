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

test("the dialog keeps focus inside, closes on Escape, and a toast is announced", async ({ page }) => {
  await page.goto("/dev/ui");
  await page.getByTestId("ui-open-dialog").click();
  const dialog = page.getByRole("dialog", { name: "Voorbeelddialoog" });
  await expect(dialog).toBeVisible();
  // A modal <dialog> makes the page behind it inert. Tab may pass through the browser's own controls
  // (the body, in a headless run) on its way round, but it never reaches an element behind the dialog.
  const inside = new Set<string>();
  for (let i = 0; i < 8; i += 1) {
    await page.keyboard.press("Tab");
    const where = await page.evaluate(() => {
      const active = document.activeElement;
      if (!active || active === document.body) return "browser";
      return active.closest("dialog") ? `dialog:${active.textContent ?? ""}` : "behind";
    });
    expect(where).not.toBe("behind");
    if (where !== "browser") inside.add(where);
  }
  expect(inside.size).toBeGreaterThanOrEqual(2);
  await page.keyboard.press("Escape");
  await expect(dialog).toBeHidden();
  await expect(page.getByTestId("ui-open-dialog")).toBeFocused();
  await page.getByTestId("ui-notify").click();
  await expect(page.getByRole("status").filter({ hasText: "Opgeslagen" })).toBeVisible();
});

test("animations are off when the system asks for less motion", async ({ page }) => {
  await page.emulateMedia({ reducedMotion: "reduce" });
  await page.goto("/dev/ui");
  await expect(page.getByTestId("ui-gallery")).toBeVisible();
  const animated = await page.evaluate(() =>
    [...document.querySelectorAll("[data-anim], [data-anim] > *")]
      .map((element) => getComputedStyle(element).animationName)
      .filter((name) => name !== "none"),
  );
  expect(animated).toEqual([]);
});
