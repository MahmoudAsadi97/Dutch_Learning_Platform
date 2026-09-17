import { expect, test } from "@playwright/test";

test.describe("microphone check", () => {
  test("push-to-talk records, uploads, canonicalises and transcribes", async ({ page, browserName }) => {
    test.skip(browserName !== "chromium", "fake audio capture is a Chromium feature");
    await page.goto("/speech-check");

    await expect(page.getByTestId("mime-type")).toContainText(/audio\/(webm|ogg|mp4)|standaardformaat/);

    const button = page.getByTestId("talk-button");
    const box = await button.boundingBox();
    if (!box) throw new Error("talk button not visible");
    await page.mouse.move(box.x + box.width / 2, box.y + box.height / 2);
    await page.mouse.down();
    await expect(button).toHaveAttribute("aria-pressed", "true");
    await page.waitForTimeout(1500);
    await page.mouse.up();

    await expect(page.getByTestId("phase")).toHaveText("Klaar.", { timeout: 30_000 });
    const result = page.getByTestId("transcript-result");
    await expect(result).toContainText("fixture");
    await expect(result).toContainText(/opus|pcm/);
    await expect(result).toContainText("16000 Hz");
    await expect(page.getByTestId("transcript-text")).not.toHaveText("(leeg)");
  });

  test("synthetic playback is labelled", async ({ page }) => {
    await page.goto("/speech-check");
    await page.getByTestId("tts-button").click();
    await expect(page.getByTestId("tts-label")).toContainText("synthetic-development");
    const src = await page.getByTestId("tts-audio").getAttribute("src");
    expect(src).toMatch(/^blob:/);
  });
});
