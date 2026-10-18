import { readFile } from "node:fs/promises";
import path from "node:path";
import { expect, test } from "./fixtures/test";

type Question = {
  prompt: { nl: string };
  options: { nl: string }[];
  answer_index: number;
};
type Pack = {
  stage_id: string;
  vocabulary: { id: string; term: string }[];
  topics: {
    id: string;
    title: { nl: string };
    reading: { questions: Question[] };
  }[];
};
type SourceRef = { source: string; id: string };
type StageIndex = {
  stages: Record<string, Record<string, Record<string, SourceRef[]>>>;
};
const stages = ["pre-a1", "a1", "pre-a2", "a2", "pre-b1", "b1"];
const skills = ["listening", "speaking", "writing"] as const;

async function sourcePack(stage: string): Promise<Pack> {
  return JSON.parse(
    await readFile(path.resolve(__dirname, "../../../../content/source-lessons/" + stage + ".json"), "utf8"),
  ) as Pack;
}

async function sourceIndex(): Promise<StageIndex> {
  return JSON.parse(
    await readFile(path.resolve(__dirname, "../../../../content/study/stage-index.json"), "utf8"),
  ) as StageIndex;
}

// These tests keep real source-linked activities reachable through the new topic-first workspace.
// Recordings and models use the server's explicitly labelled CI fixtures, not live provider claims.
for (const stage of stages) {
  test(
    stage + ": source-linked listening, speaking and writing remain discoverable in their topic",
    async ({ page }) => {
      const pack = await sourcePack(stage);
      const index = await sourceIndex();
      expect(pack.topics.map((topic) => topic.id)).toEqual([stage + "-t-source-01", stage + "-t-source-02"]);
      for (const skill of skills) {
        for (const source of pack.topics) {
          const mapped = Object.entries(index.stages[stage][skill])
            .filter(([, references]) =>
              references.some((reference) => reference.source === "practice" && reference.id === source.id),
            )
            .sort((a, b) => b[1].length - a[1].length)[0];
          expect(mapped, source.id + " has an indexed " + skill + " destination").toBeTruthy();
          const topicId = mapped![0];
          const url =
            "/learn/" +
            stage +
            "?skill=" +
            skill +
            "&topic=" +
            topicId +
            "&activity=" +
            source.id +
            "&step=practise";
          await page.goto(url);
          await expect(page.getByTestId("guided-lesson").getByRole("heading", { level: 1 })).toContainText(
            source.title.nl,
          );
          await expect(page.locator("#study-stage")).toHaveValue(stage);
          await expect(
            page.getByRole("navigation", { name: "Stappen van de oefening" }).getByRole("button"),
          ).toHaveCount(3);
          const selection = page.getByRole("combobox", { name: "Kies een situatie" });
          await expect(selection).toHaveValue(source.id);
          if (skill === "listening") {
            await expect(page.locator(".study-listen-player")).toBeVisible();
            await expect(
              page.getByRole("navigation", { name: "Onderdelen van deze vaardigheid" }).getByRole("button"),
            ).toHaveCount(3);
          } else {
            await page.locator(".study-context summary").click();
            await expect(page.locator(".study-context h3")).toContainText(source.title.nl);
            await expect(page.locator(".study-example-answer")).toHaveCount(0);
            await page.getByRole("button", { name: /^Bekijk een voorbeeldantwoord/ }).click();
            await expect(page.locator(".study-example-answer")).toBeVisible();
          }
        }
      }
      // Eligible readings use connected 8–12-line sources; the old short fragments are not reintroduced.
      const catalog = await (await page.request.get("/api/study/" + stage + "/topics?skill=reading")).json();
      const available = catalog.topics.find((topic: { available: boolean }) => topic.available);
      expect(available).toBeTruthy();
      await page.goto("/learn/" + stage + "?skill=reading&topic=" + available.id + "&step=practise");
      const lines = page.locator(".study-story-line");
      await expect(lines.first()).toBeVisible();
      expect(await lines.count()).toBeGreaterThanOrEqual(8);
      expect(await lines.count()).toBeLessThanOrEqual(12);
    },
  );
}

test("A1 source words remain searchable in the complete level reference", async ({ page }) => {
  const pack = await sourcePack("a1");
  expect(pack.vocabulary.length).toBeGreaterThan(0);
  const sourceWord = pack.vocabulary[0];
  const response = await page.request.get(
    "/api/library/a1/vocabulary?q=" + encodeURIComponent(sourceWord.term) + "&limit=100",
  );
  expect(response.ok()).toBe(true);
  const words = await response.json();
  expect(words.items.some((item: { id: string }) => item.id === sourceWord.id)).toBe(true);
  await page.goto("/learn/a1?skill=reading&view=vocabulary");
  const reference = page.getByRole("region", { name: "Woordenlijst van dit niveau" });
  await reference.getByLabel("Zoek in de woordenlijst").fill(sourceWord.term);
  await expect(
    reference.locator(".study-word-top strong").filter({ hasText: sourceWord.term }).first(),
  ).toBeVisible();
});

test("new reading feedback never awards credit to legacy source activities or another skill", async ({
  page,
}) => {
  const topicId = "a1-t-source-02";
  const beforeReading = await (
    await page.request.get("/api/curriculum/a1/topics/" + topicId + "?skill=reading")
  ).json();
  const beforeListening = await (await page.request.get("/api/curriculum/a1/topics?skill=listening")).json();
  const catalog = await (await page.request.get("/api/study/a1/topics?skill=reading")).json();
  const topic = catalog.topics.find((item: { available: boolean }) => item.available);
  await page.goto("/learn/a1?skill=reading&topic=" + topic.id + "&step=practise");
  const questions = page.locator(".study-question");
  await expect(questions.first()).toBeVisible();
  for (const question of await questions.all()) {
    await question.getByRole("radio").first().check();
  }
  const [response] = await Promise.all([
    page.waitForResponse(
      (value) => value.request().method() === "POST" && /\/study\/.+\/feedback$/.test(value.url()),
    ),
    page.getByRole("button", { name: /^Bekijk mijn feedback/ }).click(),
  ]);
  expect(response.ok()).toBe(true);
  expect((await response.json()).ephemeral).toBe(true);
  await expect(page.getByRole("region", { name: "Tijdelijke oefenfeedback" })).toBeVisible();
  await page.reload();
  await expect(page.getByRole("region", { name: "Tijdelijke oefenfeedback" })).toHaveCount(0);
  const afterReading = await (
    await page.request.get("/api/curriculum/a1/topics/" + topicId + "?skill=reading")
  ).json();
  const afterListening = await (await page.request.get("/api/curriculum/a1/topics?skill=listening")).json();
  expect(afterReading.progress).toEqual(beforeReading.progress);
  expect(afterListening.completed_count).toBe(beforeListening.completed_count);
});
