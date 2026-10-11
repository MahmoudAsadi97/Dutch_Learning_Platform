import AxeBuilder from "@axe-core/playwright";
import { expect, test } from "./fixtures/test";

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
  const toast = page.locator(".toast").filter({ hasText: "Opgeslagen" });
  await expect(toast).toBeVisible();
  // the announcement is the message alone, in one status region
  await expect(page.getByRole("status").filter({ hasText: "Opgeslagen" })).toHaveCount(1);
  const close = toast.getByRole("button", { name: "Melding sluiten" });
  const box = await close.boundingBox();
  expect(box?.width ?? 0).toBeGreaterThanOrEqual(44);
  expect(box?.height ?? 0).toBeGreaterThanOrEqual(44);
  await close.click();
  await expect(toast).toHaveCount(0);
});

test("segmented choices are 44px targets and the chosen one is a solid fill", async ({ page }) => {
  await page.goto("/dev/ui");
  const segments = page.locator(".segment");
  expect(await segments.count()).toBeGreaterThan(1);
  for (const segment of await segments.all()) {
    const box = await segment.boundingBox();
    expect(box?.height ?? 0).toBeGreaterThanOrEqual(44);
  }
  const chosen = page.locator('.segment[aria-pressed="true"]').first();
  const fill = await chosen.evaluate((element) => getComputedStyle(element).backgroundColor);
  expect(fill).not.toBe("rgba(0, 0, 0, 0)");
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

test("every answer state shows in words and an icon, never in colour alone", async ({ page }) => {
  await page.goto("/dev/ui");
  const options = page.getByTestId("ui-answer-states").locator(".answer-option");
  await expect(options).toHaveCount(6);
  expect(await options.evaluateAll((all) => all.map((option) => option.getAttribute("data-state")))).toEqual([
    "default",
    "selected",
    "correct",
    "incorrect",
    "reveal",
    "idle",
  ]);
  for (const state of ["correct", "incorrect", "reveal"]) {
    const mark = page
      .getByTestId("ui-answer-states")
      .locator(`.answer-option[data-state="${state}"] .answer-option-mark`);
    await expect(mark.locator("svg")).toHaveCount(1);
    await expect(mark).toHaveText(/\S/);
  }
  await expect(page.getByRole("radio", { name: /het huis Het juiste antwoord/ })).toBeDisabled();
});
