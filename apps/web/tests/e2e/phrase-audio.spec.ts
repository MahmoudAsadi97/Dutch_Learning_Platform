import AxeBuilder from "@axe-core/playwright";
import { expect, test } from "@playwright/test";
import { readFile } from "node:fs/promises";
import path from "node:path";

test("alphabet audio requires a click, says Dutch letter names and reuses replay audio", async ({ page }) => {
  const audio = await readFile(path.resolve("tests/e2e/fixtures/speech-input.wav"));
  const spoken: string[] = [];
  await page.route("**/api/speech/synthesize", async route => {
    spoken.push(route.request().postDataJSON().text);
    await route.fulfill({ body: audio, contentType: "audio/wav", headers: { "x-audio-voice": "fixture-tone" } });
  });
  await page.goto("/learn/pre-a1");
  await page.getByRole("navigation", { name: "Onderdelen van dit niveau" }).getByRole("button", { name: "Alfabet", exact: true }).click();
  const alphabet = page.getByTestId("alphabet-practice");
  await expect(alphabet).toBeVisible();
  expect(spoken).toEqual([]);
  const play = alphabet.getByRole("button", { name: /^Luister: De naam van de letter A/ });
  await play.click();
  await expect.poll(() => spoken).toEqual(["aa"]);
  // Wait for the response to become a playable clip. Cancelling on request dispatch alone can
  // abort before the cache is populated, legitimately requiring another request on replay.
  await expect(alphabet.getByText("Testtoon; dit is geen uitspraakvoorbeeld.")).toBeVisible();
  await expect(alphabet.locator(".alphabet-focus .phrase-audio-button").first()).toHaveAttribute("aria-pressed", "false");
  await play.click();
  await expect(alphabet.getByText("Testtoon; dit is geen uitspraakvoorbeeld.")).toBeVisible();
  expect(spoken).toEqual(["aa"]);
});

test("alphabet listening recognition and support text work on a narrow screen", async ({ page }) => {
  await page.setViewportSize({ width: 320, height: 850 });
  await page.goto("/learn/pre-a1");
  await page.getByRole("navigation", { name: "Onderdelen van dit niveau" }).getByRole("button", { name: "Alfabet", exact: true }).click();
  const alphabet = page.getByTestId("alphabet-practice");
  await page.getByLabel("Taalhulp / language").selectOption("nl-fa-en");
  await expect(alphabet.locator('[lang="fa"]').first()).toHaveAttribute("dir", "rtl");
  await alphabet.getByRole("group", { name: "Welke letter hoor je?", exact: true }).getByRole("button", { name: "D", exact: true }).click();
  await expect(alphabet.getByRole("status")).toContainText("Juist: D heet dee.");
  await alphabet.getByRole("button", { name: /Volgende letter/ }).click();
  await expect(alphabet.getByRole("group", { name: "Welke letter hoor je?", exact: true }).getByRole("button")).toHaveCount(4);
  await alphabet.getByText("Letters die samenwerken", { exact: true }).click();
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
  const result = await new AxeBuilder({ page }).include('[data-testid="alphabet-practice"]').withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"]).analyze();
  expect(result.violations).toEqual([]);
});

test("starting the microphone stops pronunciation and disables replay until capture ends", async ({ page }) => {
  const audio = await readFile(path.resolve("tests/e2e/fixtures/speech-input.wav"));
  await page.route("**/api/speech/synthesize", route => route.fulfill({ body: audio, contentType: "audio/wav", headers: { "x-audio-voice": "fixture-tone" } }));
  await page.route("**/api/speech/transcribe", route => route.fulfill({ json: { audio: { asset_id: "58bd4ab4-f0b2-4b1a-87aa-d16d8c51d5fb" }, transcript: { text: "Hallo. Ik heet Noor. Ik woon in Gent." } } }));
  await page.goto("/learn/pre-a1");
  await page.getByRole("navigation", { name: "Onderdelen van dit niveau" }).getByRole("button", { name: "Spreken", exact: true }).click();
  await page.locator(".communication-coach summary").click();
  const pronunciation = page.locator(".communication-coach .phrase-audio-button").first();
  await pronunciation.click();
  await page.getByRole("button", { name: "Start de opname", exact: true }).click();
  await expect(page.getByRole("button", { name: "Stop de opname", exact: true })).toBeVisible();
  await expect(pronunciation).toBeDisabled();
  await expect(pronunciation).toHaveAttribute("aria-pressed", "false");
  await page.getByRole("button", { name: "Stop de opname", exact: true }).click();
  await expect(pronunciation).toBeEnabled();
});
