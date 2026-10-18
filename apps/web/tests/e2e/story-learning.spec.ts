import { readFile } from "node:fs/promises";
import path from "node:path";
import { expect, test } from "./fixtures/test";
import { studyLesson } from "./fixtures/study";
import { STAGE_IDS } from "../../lib/domain/registry";

// Real content and API: a topic keeps the same coherent situation across all four skills.
for (const stage of STAGE_IDS) {
  test(`${stage}: authored reading and all four skills share their topic context`, async ({ page }) => {
    const pack = JSON.parse(
      await readFile(path.resolve(__dirname, `../../../../content/study/packs/${stage}.json`), "utf8"),
    );
    const source = pack.lessons[0];
    const lesson = await studyLesson(page, stage, "reading", source.topic_id);
    expect(lesson.parts[0].text.length).toBeGreaterThanOrEqual(8);
    expect(lesson.parts[0].text.length).toBeLessThanOrEqual(12);
    await page.goto(`/learn/${stage}?skill=reading&topic=${source.topic_id}&step=practise`);
    const story = page.locator(".study-story-line");
    await expect(story).toHaveCount(lesson.parts[0].text.length);
    for (const line of lesson.parts[0].text)
      await expect(page.locator(".study-story")).toContainText(line.nl);
    expect(await story.locator(".phrase-audio-button").count()).toBeGreaterThanOrEqual(
      lesson.parts[0].text.length,
    );
    const navigation = page.getByRole("navigation", { name: "Kies een vaardigheid" });
    for (const [skill, label] of [
      ["listening", "Luisteren"],
      ["speaking", "Spreken"],
      ["writing", "Schrijven"],
    ]) {
      await navigation.getByRole("link", { name: new RegExp(`^${label}`) }).click();
      await expect(page).toHaveURL(new RegExp(`skill=${skill}&topic=${source.topic_id}`));
      await expect(navigation.getByRole("link", { name: new RegExp(`^${label}`) })).toHaveAttribute(
        "aria-current",
        "page",
      );
      await expect(page.getByTestId("guided-lesson")).toBeVisible();
      const related = await studyLesson(page, stage, skill, source.topic_id);
      expect(related.activity_id).toBe(lesson.activity_id);
    }
  });
}

test("reading audio is an explicit choice and creates no saved reading evidence", async ({ page }) => {
  const requests: string[] = [];
  page.on("request", (request) => {
    if (request.method() === "POST") requests.push(new URL(request.url()).pathname);
  });
  await page.goto("/learn/a1?skill=reading&topic=family&step=practise");
  await expect(page.locator(".study-story-line").first()).toBeVisible();
  expect(requests.filter((value) => value.includes("synthesize"))).toEqual([]);
  const response = page.waitForResponse((value) => value.url().endsWith("/speech/synthesize"));
  await page.locator(".study-story-line .phrase-audio-button").first().click();
  expect((await response).ok()).toBe(true);
  expect(requests.some((value) => /assistance|\/practice|\/items/.test(value))).toBe(false);
});
