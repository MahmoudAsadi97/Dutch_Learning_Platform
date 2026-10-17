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
  vocabulary: { id: string }[];
  topics: { id: string; title: { nl: string }; reading: { questions: Question[] } }[];
  stories: { id: string; title: { nl: string }; paragraphs: { nl: string }[] }[];
};
type Counts = { words: number; stories: number; topics: number };
const stages = ["pre-a1", "a1", "pre-a2", "a2", "pre-b1", "b1"];
const skills = { reading: "Lezen", listening: "Luisteren", speaking: "Spreken", writing: "Schrijven" };
const category = "Van woord naar gesprek";

async function sourcePack(stageId: string): Promise<Pack> {
  return JSON.parse(
    await readFile(path.resolve(__dirname, `../../../../content/source-lessons/${stageId}.json`), "utf8"),
  ) as Pack;
}

async function effectiveCounts(stageId: string, pack: Pack): Promise<Counts> {
  const [library, practice, units, reading] = await Promise.all([
    readFile(path.resolve(__dirname, `../../../../content/library/${stageId}.json`), "utf8"),
    readFile(path.resolve(__dirname, `../../../../content/practice/${stageId}.json`), "utf8"),
    readFile(path.resolve(__dirname, `../../../../content/learning-units/${stageId}.json`), "utf8"),
    readFile(path.resolve(__dirname, `../../../../content/reading-library/${stageId}.json`), "utf8"),
  ]);
  const baseLibrary = JSON.parse(library) as { vocabulary: unknown[]; stories: unknown[] };
  const basePractice = JSON.parse(practice) as { topics: unknown[] };
  const learningUnits = JSON.parse(units) as Pack;
  const readingLibrary = JSON.parse(reading) as Pack;
  return {
    words:
      baseLibrary.vocabulary.length +
      pack.vocabulary.length +
      learningUnits.vocabulary.length +
      readingLibrary.vocabulary.length,
    stories:
      baseLibrary.stories.length +
      pack.stories.length +
      learningUnits.stories.length +
      readingLibrary.stories.length,
    topics:
      basePractice.topics.length +
      pack.topics.length +
      learningUnits.topics.length +
      readingLibrary.topics.length,
  };
}

async function selectSkill(page: Page, skill: keyof typeof skills, counts: Counts, sourceTopics: number) {
  await page
    .getByRole("navigation", { name: "Onderdelen van dit niveau" })
    .getByRole("button", { name: skills[skill], exact: true })
    .click();
  await expect(page.locator(".skill-topic-library h3")).toHaveText(
    `${counts.topics} onderwerpen voor ${skills[skill].toLowerCase()}`,
  );
  await page.getByLabel("Thema", { exact: true }).selectOption(category);
  await expect(page.locator(".topic-tile")).toHaveCount(sourceTopics);
}

// These journeys use actual authored content, filtering, sessions and persistence. Only the server's
// CI model/speech providers are fixtures; there are no library or topic route mocks in this file.
for (const stageId of stages) {
  test(`${stageId}: source-linked practice is reachable in every skill`, async ({ page }) => {
    const pack = await sourcePack(stageId);
    const counts = await effectiveCounts(stageId, pack);
    expect(pack.topics.map((topic) => topic.id)).toEqual([
      `${stageId}-t-source-01`,
      `${stageId}-t-source-02`,
    ]);
    await page.goto(`/learn/${stageId}`);
    for (const skill of Object.keys(skills) as (keyof typeof skills)[]) {
      await selectSkill(page, skill, counts, pack.topics.length);
      for (const topic of pack.topics) {
        await page.getByRole("button", { name: `Oefen ${topic.title.nl}`, exact: true }).click();
        await expect(page.locator(".topic-reader h3").first()).toContainText(topic.title.nl);
        await expect(page.locator(".topic-reader")).toContainText(category);
        await page.getByRole("button", { name: "← Alle onderwerpen", exact: true }).click();
      }
    }
  });
}

test("A1 source words and story open, and first-try reading answers persist independently", async ({
  page,
}) => {
  const pack = await sourcePack("a1");
  const counts = await effectiveCounts("a1", pack);
  const topic = pack.topics.find((entry) => entry.id === "a1-t-source-02")!;
  const story = pack.stories.find((entry) => entry.id === "a1-s-source-02")!;
  expect(topic).toBeTruthy();
  expect(story).toBeTruthy();
  await page.goto("/learn/a1");
  await expect(page.getByRole("heading", { name: /^150 woorden om zelf te gebruiken/ })).toBeVisible();
  await page.getByRole("button", { name: "Bekijk alle woordkaarten" }).click();
  await expect(
    page
      .locator(".word-library")
      .getByRole("heading", { name: `${counts.words} woorden en uitdrukkingen`, exact: true }),
  ).toHaveText(`${counts.words} woorden en uitdrukkingen`);
  const nav = page.getByRole("navigation", { name: "Onderdelen van dit niveau" });
  await nav.getByRole("button", { name: "Story Time", exact: true }).click();
  await expect(page.locator(".library-count")).toContainText(`${counts.stories} verhalen`);
  await page.getByLabel("Onderwerp", { exact: true }).selectOption(category);
  await expect(page.locator(".story-tile")).toHaveCount(pack.stories.length);
  await page.getByRole("button", { name: `Lees ${story.title.nl}`, exact: true }).click();
  await expect(page.locator(".story-reader h3")).toContainText(story.title.nl);
  await expect(page.locator(".story-paper .story-paragraph")).toHaveCount(2);
  for (const paragraph of story.paragraphs) {
    await expect(page.locator(".story-paper")).toContainText(paragraph.nl);
  }

  const beforeListening = await (await page.request.get("/api/curriculum/a1/topics?skill=listening")).json();
  const beforeFirstTopic = await (
    await page.request.get("/api/curriculum/a1/topics/a1-t-source-01?skill=reading")
  ).json();
  await selectSkill(page, "reading", counts, pack.topics.length);
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
      await expect(page.locator(".exercise-passage-text")).toContainText(story.paragraphs[0].nl);
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
  const afterFirstTopic = await (
    await page.request.get("/api/curriculum/a1/topics/a1-t-source-01?skill=reading")
  ).json();
  expect(afterFirstTopic.progress).toEqual(beforeFirstTopic.progress);
  await selectSkill(page, "reading", counts, pack.topics.length);
  const completedTile = page.locator(".topic-tile").filter({ hasText: topic.title.nl });
  await expect(completedTile).toContainText("Geoefend");
});
