import { readFile } from "node:fs/promises";
import path from "node:path";
import { expect, test } from "./fixtures/test";

type Copy = { nl: string; en: string; fa: string };
type UnitPack = {
  stories: { id: string; title: Copy; lines: Copy[]; topic_id: string }[];
  topics: { id: string; title: Copy }[];
};
const stages = [
  "pre-a1",
  "a1",
  "pre-a2",
  "a2",
  "pre-b1",
  "b1",
  "pre-b2",
  "b2",
  "pre-c1",
  "c1",
  "pre-c2",
  "c2",
];
const skills = { reading: "Lezen", listening: "Luisteren", speaking: "Spreken", writing: "Schrijven" };
const actions: Record<string, string> = {
  reading: "Lees",
  listening: "Luister",
  speaking: "Spreek",
  writing: "Schrijf",
};

// Authored content and actual API routes; only CI model/speech providers are fixtures.
for (const stageId of stages) {
  test(`${stageId}: connected story lines and four-skill navigation use the same authored unit`, async ({
    page,
  }) => {
    const pack = JSON.parse(
      await readFile(path.resolve(__dirname, `../../../../content/learning-units/${stageId}.json`), "utf8"),
    ) as UnitPack;
    const story = pack.stories[0];
    const topic = pack.topics.find((item) => item.id === story.topic_id);
    expect(topic, "story must link to a real topic in its own pack").toBeTruthy();
    expect(story.lines.length).toBeGreaterThanOrEqual(8);
    expect(story.lines.length).toBeLessThanOrEqual(12);
    await page.goto(`/learn/${stageId}`);
    await page
      .getByRole("navigation", { name: "Onderdelen van dit niveau" })
      .getByRole("button", { name: "Verhalen", exact: true })
      .click();
    await expect(page.getByLabel("Onderwerp", { exact: true })).toHaveValue("Verhaal naar gesprek");
    await page.getByRole("button", { name: /^Ontdek de nieuwe verhalen/ }).click();
    await page.getByRole("button", { name: `Lees ${story.title.nl}`, exact: true }).click();
    const authored = page.getByRole("list", { name: "Regels van het verhaal" });
    await expect(authored.locator(":scope > li")).toHaveCount(story.lines.length);
    for (const line of story.lines) await expect(authored).toContainText(line.nl);
    expect(await authored.locator(".phrase-audio-button").count()).toBeGreaterThanOrEqual(story.lines.length);
    const routes = new Map<string, string>();
    for (const skill of Object.keys(skills)) {
      const link = page
        .locator(".story-skill-links")
        .getByRole("link", { name: new RegExp(`^${actions[skill]}`) });
      const href = await link.getAttribute("href");
      expect(href).toBe(`/learn/${stageId}?skill=${skill}&topic=${story.topic_id}`);
      routes.set(skill, href!);
    }
    await page
      .locator(".story-skill-links")
      .getByRole("link", { name: /^Luister/ })
      .click();
    await expect(page.locator(".topic-reader h3").first()).toContainText(topic!.title.nl);
    await expect(
      page
        .getByRole("navigation", { name: "Onderdelen van dit niveau" })
        .getByRole("button", { name: "Luisteren", exact: true }),
    ).toHaveAttribute("aria-current", "step");
    for (const [skill, label] of Object.entries(skills)) {
      if (skill === "listening") continue;
      await page.goto(routes.get(skill)!);
      await expect(
        page
          .getByRole("navigation", { name: "Onderdelen van dit niveau" })
          .getByRole("button", { name: label, exact: true }),
      ).toHaveAttribute("aria-current", "step");
      await expect(page.locator(".topic-reader h3").first()).toContainText(topic!.title.nl);
    }
  });
}

test("reading playback records help through the real API before asking the speech provider", async ({
  page,
}) => {
  const pack = JSON.parse(
    await readFile(path.resolve(__dirname, "../../../../content/learning-units/a1.json"), "utf8"),
  ) as UnitPack;
  const topicId = pack.stories[0].topic_id;
  await page.goto(`/learn/a1?skill=reading&topic=${topicId}`);
  await page.getByRole("button", { name: "Begin met lezen", exact: true }).click();
  const requests: string[] = [];
  page.on("request", (request) => {
    if (request.url().endsWith("/assistance")) requests.push("assistance");
    if (request.url().endsWith("/speech/synthesize")) requests.push("synthesis");
  });
  const saved = page.waitForResponse((response) => response.url().endsWith("/assistance"));
  const audio = page.waitForResponse((response) => response.url().endsWith("/speech/synthesize"));
  await page.locator(".exercise-passage-text .phrase-audio-button").first().click();
  const supportResponse = await saved;
  expect(supportResponse.ok()).toBe(true);
  expect((await supportResponse.json()).hint_used).toBe(true);
  expect((await audio).ok()).toBe(true);
  expect(requests.slice(0, 2)).toEqual(["assistance", "synthesis"]);
  const sessionPath = new URL(supportResponse.url()).pathname.split("/items/")[0];
  const current = await page.request.get(sessionPath);
  expect(current.ok()).toBe(true);
  const session = await current.json();
  expect(session.items.find((item: { kind: string }) => item.kind === "read_passage").hint_used).toBe(true);
  const questions = session.items.filter((item: { kind: string }) => item.kind === "choice");
  expect(questions.length).toBeGreaterThan(0);
  expect(questions.every((item: { hint_used: boolean }) => item.hint_used)).toBe(true);
});
