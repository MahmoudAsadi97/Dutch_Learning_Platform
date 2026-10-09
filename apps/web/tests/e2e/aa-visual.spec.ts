import { expect, test } from "./fixtures/test";
import { episodeId, storyFixture, wordsFixture } from "./fixtures/stories";

/**
 * Screenshot baselines of the learner-facing screens at three widths. They freeze the look of the app so
 * that the design-system work can prove which steps change pixels and which do not.
 *
 * Baselines are rendered on Linux only (font rasterisation differs per platform): CI's runner, or the pinned
 * Playwright container started by `python scripts/run.py e2e-visual`, which sets VISUAL_LOCAL=1. On a
 * developer machine the spec is skipped. The file name starts with "aa" so it runs first, on the learner that
 * the e2e task has just reset; the daily plan, the episode and the word bank come from route fixtures because
 * the real ones depend on a background writer.
 */

const onLinux = process.platform === "linux" || process.env.VISUAL_LOCAL === "1";
test.skip(!onLinux, "screenshot baselines are rendered on Linux (CI or `python scripts/run.py e2e-visual`)");

test.use({
  colorScheme: "light",
  locale: "nl-BE",
  timezoneId: "Europe/Brussels",
  contextOptions: { reducedMotion: "reduce" },
});

const fixedTime = new Date("2026-10-02T09:30:00+02:00");

const screens: { name: string; path: string; ready: string }[] = [
  { name: "today", path: "/", ready: '[data-testid="today-home"] [data-testid="episode-card"]' },
  { name: "leerpad", path: "/leerpad", ready: '[data-testid="curriculum-path"] li' },
  { name: "learn-a1", path: "/learn/a1", ready: ".vocabulary-card" },
  { name: "progress", path: "/progress", ready: ".course-progress-row" },
  { name: "mission", path: "/missions/appointment-change", ready: '[data-testid="reading-text"]' },
  { name: "speech", path: "/speech-check", ready: '[data-testid="talk-button"]' },
  { name: "episode", path: `/verhalen/${episodeId}`, ready: '[data-testid="episode-paragraph"]' },
  { name: "woorden", path: "/woorden", ready: '[data-testid="word-review"] [data-testid="reveal-word"]' },
  { name: "gallery", path: "/dev/ui", ready: '[data-testid="ui-gallery"]' },
  { name: "welkom", path: "/welkom?stap=uitleg", ready: '[data-testid="how-it-works"]' },
];

for (const screen of screens) {
  for (const width of [1440, 390, 320]) {
    test(`${screen.name} at ${width}px`, async ({ page }) => {
      await page.clock.setFixedTime(fixedTime);
      await page.setViewportSize({ width, height: width <= 390 ? 844 : 1000 });
      await storyFixture(page);
      await wordsFixture(page);
      await page.goto(screen.path);
      await expect(page.locator(screen.ready).first()).toBeVisible();
      await page.evaluate(() => document.fonts.ready.then(() => undefined));
      await expect(page).toHaveScreenshot(`${screen.name}-${width}.png`, {
        fullPage: true,
        animations: "disabled",
        caret: "hide",
        maxDiffPixelRatio: 0.002,
      });
    });
  }
}
