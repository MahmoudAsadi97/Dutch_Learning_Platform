import { readFile } from "node:fs/promises";
import path from "node:path";
import type { Page } from "@playwright/test";
import { expect, test } from "./fixtures/test";

type Question = {
  prompt: { nl: string };
  options: { nl: string }[];
  answer_index: number;
};
type Pack = {
  stage_id: string;
  topics: { id: string; title: { nl: string }; reading: { questions: Question[] } }[];
  stories: { title: { nl: string }; paragraphs: { nl: string }[] }[];
};
const stages = ["pre-a1", "a1", "pre-a2", "a2", "pre-b1", "b1"];
const skills = { reading: "Lezen", listening: "Luisteren", speaking: "Spreken", writing: "Schrijven" };
const category = "Van woord naar gesprek";

async function sourcePack(stageId: string): Promise<Pack> {
  return JSON.parse(
    await readFile(path.resolve(__dirname, `../../../../content/source-lessons/${stageId}.json`), "utf8"),
  ) as Pack;
}

async function selectSkill(page: Page, skill: keyof typeof skills) {
  await page
    .getByRole("navigation", { name: "Onderdelen van dit niveau" })
    .getByRole("button", { name: skills[skill], exact: true })
    .click();
  await expect(page.locator(".skill-topic-library h3")).toHaveText(
    `101 onderwerpen voor ${skills[skill].toLowerCase()}`,
  );
  await page.getByLabel("Thema", { exact: true }).selectOption(category);
  await expect(page.locator(".topic-tile")).toHaveCount(1);
}

// These journeys use actual authored content, filtering, sessions and persistence. Only the server's
// CI model/speech providers are fixtures; there are no library or topic route mocks in this file.
for (const stageId of stages) {
  test(`${stageId}: source-linked practice is reachable in every skill`, async ({ page }) => {
    const pack = await sourcePack(stageId);
    const topic = pack.topics[0];
    await page.goto(`/learn/${stageId}`);
    for (const skill of Object.keys(skills) as (keyof typeof skills)[]) {
      await selectSkill(page, skill);
      await page.getByRole("button", { name: `Oefen ${topic.title.nl}`, exact: true }).click();
      await expect(page.locator(".topic-reader h3").first()).toContainText(topic.title.nl);
      await expect(page.locator(".topic-reader")).toContainText(category);
      await page.getByRole("button", { name: "← Alle onderwerpen", exact: true }).click();
    }
  });
}

test("A1 source words and story open, and first-try reading answers persist independently", async ({
  page,
}) => {
  const pack = await sourcePack("a1");
  const topic = pack.topics[0];
  await page.goto("/learn/a1");
  await expect(page.locator(".word-library h3")).toHaveText("502 woorden en uitdrukkingen");
  const nav = page.getByRole("navigation", { name: "Onderdelen van dit niveau" });
  await nav.getByRole("button", { name: "Story Time", exact: true }).click();
  await expect(page.locator(".library-count")).toContainText("101 verhalen");
  await page.getByLabel("Onderwerp", { exact: true }).selectOption(category);
  await expect(page.locator(".story-tile")).toHaveCount(1);
  await page.getByRole("button", { name: `Lees ${pack.stories[0].title.nl}`, exact: true }).click();
  await expect(page.locator(".story-reader h3")).toContainText(pack.stories[0].title.nl);
  await expect(page.locator(".story-paper .story-paragraph")).toHaveCount(2);
  for (const paragraph of pack.stories[0].paragraphs) {
    await expect(page.locator(".story-paper")).toContainText(paragraph.nl);
  }

  const beforeListening = await (await page.request.get("/api/curriculum/a1/topics?skill=listening")).json();
  await selectSkill(page, "reading");
  await page.getByRole("button", { name: `Oefen ${topic.title.nl}`, exact: true }).click();
  await page.getByRole("button", { name: "Begin met lezen", exact: true }).click();
  const toQuestions = page.getByRole("button", { name: "Naar de vragen", exact: true });
  const stem = page.locator(".exercise-stage .exercise-prompt > [lang=nl]").first();
  const summary = page.locator(".exercise-summary");
  // A rerun can resume an open session. Identify authored questions by their prompt rather than relying
  // on their order or the opaque, shuffled option IDs issued by the real exercise API.
  for (let round = 0; round < 8; round += 1) {
    await expect(toQuestions.or(stem).or(summary).first()).toBeVisible();
    if (await summary.isVisible()) break;
    if (await toQuestions.isVisible()) {
      await expect(page.locator(".exercise-passage-text")).toContainText(pack.stories[0].paragraphs[0].nl);
      await toQuestions.click();
      continue;
    }
    const prompt = ((await stem.textContent()) ?? "").trim();
    const question = topic.reading.questions.find((entry) => entry.prompt.nl.trim() === prompt);
    expect(question, prompt).toBeTruthy();
    await page
      .getByRole("radio", { name: question!.options[question!.answer_index].nl, exact: true })
      .check();
    await page.getByRole("button", { name: "Controleer", exact: true }).click();
    await page.getByRole("button", { name: "Verder", exact: true }).click();
  }
  await expect(page.locator(".summary-completion[data-state=done]")).toBeVisible();
  await page.reload();
  const persisted = await (
    await page.request.get(`/api/curriculum/a1/topics/${topic.id}?skill=reading`)
  ).json();
  expect(persisted.progress).toEqual({ completed: true, attempted: true });
  const afterListening = await (await page.request.get("/api/curriculum/a1/topics?skill=listening")).json();
  expect(afterListening.completed_count).toBe(beforeListening.completed_count);
  await selectSkill(page, "reading");
  await expect(page.locator(".topic-tile")).toContainText("Geoefend");
});
