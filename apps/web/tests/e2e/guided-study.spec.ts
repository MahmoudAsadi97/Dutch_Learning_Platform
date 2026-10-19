import type { Page } from "@playwright/test";
import { readFileSync } from "node:fs";
import path from "node:path";
import { expect, test } from "./fixtures/test";
import type { StudyCatalog, StudyLesson } from "../../lib/client/study";

type Skill = "reading" | "listening" | "speaking" | "writing";

for (const stage of ["a2", "c2"] as const) {
  test(`${stage} original stories stay in Reading and switching stories clears temporary answers`, async ({
    page,
  }) => {
    await page.setViewportSize({ width: 390, height: 844 });
    const index = JSON.parse(
      readFileSync(path.resolve(__dirname, "../../../../content/study/stage-index.json"), "utf8"),
    );
    const selected = Object.entries(
      index.stages[stage].reading as Record<string, { source: string; id: string }[]>,
    ).find(([, sources]) => sources.length > 1 && sources.some((source) => source.source === "reading"));
    expect(selected, "an original reading shares a topic with another selectable story").toBeTruthy();
    const [topic, sources] = selected!;
    const targetId = sources.find((source) => source.source === "reading")!.id;
    const beforeId = sources.find((source) => source.id !== targetId)!.id;
    const targetResponse = await page.request.get(
      `/api/study/${stage}/topics/${topic}?skill=reading&activity_id=${targetId}`,
    );
    expect(targetResponse.ok()).toBe(true);
    const target = (await targetResponse.json()) as StudyLesson;
    await page.goto(`/learn/${stage}?skill=reading&topic=${topic}&activity=${beforeId}&step=practise`);
    const firstQuestion = page.locator(".study-question").first();
    await expect(firstQuestion).toBeVisible();
    for (const question of await page.locator(".study-question").all())
      await question.getByRole("radio").first().check();
    await page.getByRole("button", { name: /^Bekijk mijn feedback/ }).click();
    await expect(page.getByRole("region", { name: "Tijdelijke oefenfeedback" })).toBeVisible();
    await page.getByRole("button", { name: /^Kies een verhaal/ }).click();
    const picker = page.getByRole("region", { name: /^Verhalen in dit onderwerp/ });
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
    await picker.getByRole("searchbox").fill(target.title.nl);
    await picker.locator(`button[data-activity-id="${targetId}"]`).click();
    await expect(page).toHaveURL(new RegExp(`activity=${targetId}`));
    await expect(page.getByRole("heading", { level: 1 })).toContainText(target.title.nl);
    await expect(page.getByRole("region", { name: "Tijdelijke oefenfeedback" })).toHaveCount(0);
    await page.getByRole("button", { name: /^Ik ben klaar om te oefenen/ }).click();
    const lines = page.locator(".study-story-line");
    await expect(lines).toHaveCount(target.parts[0].text.length);
    await expect(lines.getByRole("button", { name: /^Luister:/ })).toHaveCount(target.parts[0].text.length);
    await expect(lines.first()).toContainText(target.parts[0].text[0].nl);
    await expect(page.locator('.study-question input[type="radio"]:checked')).toHaveCount(0);
    const [audio] = await Promise.all([
      page.waitForResponse(
        (response) => response.request().method() === "POST" && response.url().includes("/speech/synthesize"),
      ),
      lines
        .first()
        .getByRole("button", { name: /^Luister:/ })
        .click(),
    ]);
    expect(audio.ok()).toBe(true);
    await expect
      .poll(() => page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth))
      .toBe(true);
  });
}

async function catalogue(page: Page, stage: string, skill: Skill): Promise<StudyCatalog> {
  const response = await page.request.get(`/api/study/${stage}/topics?skill=${skill}`);
  expect(response.ok()).toBe(true);
  const result = (await response.json()) as StudyCatalog;
  expect(result.stage_id).toBe(stage);
  expect(result.skill).toBe(skill);
  expect(result.total_topics).toBeGreaterThanOrEqual(50);
  return result;
}

async function availableLesson(page: Page, stage: string, skill: Skill) {
  const topics = await catalogue(page, stage, skill);
  const topic = topics.topics.find((item) => item.available);
  expect(topic, `${stage} ${skill} has a selectable authored activity`).toBeTruthy();
  const response = await page.request.get(`/api/study/${stage}/topics/${topic!.id}?skill=${skill}`);
  expect(response.ok()).toBe(true);
  return { topic: topic!, lesson: (await response.json()) as StudyLesson };
}

test("dashboard, level, skill and topic form one discoverable learning route", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByTestId("study-dashboard")).toBeVisible();
  const menu = page.getByRole("navigation", { name: "Hoofdmenu", exact: true });
  await expect(menu.getByRole("link")).toHaveCount(4);
  await expect(menu.getByRole("link", { name: /^Leren/ })).toBeVisible();
  await expect(menu.locator('a[href="/verhalen"],a[href="/spreken"],a[href="/woorden"]')).toHaveCount(0);
  await page.getByRole("link", { name: /^Kies een ander niveau/ }).click();
  await expect(page.getByTestId("curriculum-path").locator(".study-level-card")).toHaveCount(12);
  await page.getByRole("link", { name: "A2 · Lezen", exact: true }).click();
  await expect(page.locator("#study-stage")).toHaveValue("a2");
  const skills = page.getByRole("navigation", { name: "Kies een vaardigheid" });
  await expect(skills.getByRole("link")).toHaveCount(4);
  const { topic } = await availableLesson(page, "a2", "reading");
  await page.getByLabel("Zoek een onderwerp").fill(topic.title.nl);
  const choice = page.locator(`.study-topic-card[href*="topic=${topic.id}"]`);
  await expect(choice).toBeVisible();
  await choice.click();
  await expect(page).toHaveURL(new RegExp(`/learn/a2\\?skill=reading&topic=${topic.id}`));
  await expect(
    page.getByRole("navigation", { name: "Stappen van de oefening" }).getByRole("button"),
  ).toHaveCount(3);
  await expect(page.locator(".study-word").first()).toBeVisible();
  await page.getByRole("button", { name: /^Ik ben klaar om te oefenen/ }).click();
  await expect(page.getByTestId("study-practice")).toBeVisible();
  const lines = page.locator(".study-story-line");
  expect(await lines.count()).toBeGreaterThanOrEqual(8);
  expect(await lines.count()).toBeLessThanOrEqual(12);
  await expect(lines.first().getByRole("button", { name: /^Luister:/ })).toBeVisible();
  await page
    .getByRole("navigation", { name: "Stappen van de oefening" })
    .getByRole("button", { name: /Zelf proberen/ })
    .click();
  await expect(page).toHaveURL(/step=check/);
});

test("practice marks disappear when leaving, returning, or reloading", async ({ page }) => {
  const { topic } = await availableLesson(page, "a2", "reading");
  await page.goto(`/learn/a2?skill=reading&topic=${topic.id}&step=practise`);
  const questions = page.locator(".study-question");
  await expect(questions.first()).toBeVisible();
  for (const question of await questions.all()) {
    const choices = question.getByRole("radio");
    if (await choices.count()) await choices.first().check();
    else await question.getByRole("textbox").fill("een antwoord");
  }
  const [response] = await Promise.all([
    page.waitForResponse(
      (value) => value.request().method() === "POST" && /\/study\/.+\/feedback$/.test(value.url()),
    ),
    page.getByRole("button", { name: /^Bekijk mijn feedback/ }).click(),
  ]);
  expect(response.ok()).toBe(true);
  expect((await response.json()).ephemeral).toBe(true);
  const feedback = page.getByRole("region", { name: "Tijdelijke oefenfeedback" });
  await expect(feedback).toBeVisible();
  await expect(feedback.locator(".study-score")).toContainText("/10");
  await page
    .getByRole("navigation", { name: "Kies een vaardigheid" })
    .getByRole("link", { name: /^Schrijven/ })
    .click();
  await expect(page).toHaveURL(/skill=writing/);
  await page.goBack();
  await expect(page.getByTestId("study-practice")).toBeVisible();
  await expect(feedback).toHaveCount(0);
  await expect(page.locator('.study-question input[type="radio"]:checked')).toHaveCount(0);
  await expect(page.getByRole("button", { name: /^Bekijk mijn feedback/ })).toBeDisabled();
  await page.reload();
  await expect(page.getByTestId("study-practice")).toBeVisible();
  await expect(feedback).toHaveCount(0);
});

test("speaking examples are hidden and language changes preserve the learner's answer", async ({ page }) => {
  const { topic } = await availableLesson(page, "a2", "speaking");
  await page.goto(`/learn/a2?skill=speaking&topic=${topic.id}&step=practise`);
  await expect(
    page.getByRole("navigation", { name: "Onderdelen van deze vaardigheid" }).getByRole("button"),
  ).toHaveCount(3);
  await expect(page.locator(".study-example-answer")).toHaveCount(0);
  const answer = page.getByLabel(/^Je herkende woorden/);
  await answer.fill("Ik speel graag voetbal met mijn vrienden.");
  await page.getByRole("button", { name: /^Bekijk een voorbeeldantwoord/ }).click();
  await expect(page.locator(".study-example-answer")).toBeVisible();
  const languages = page.getByLabel("Taalhulp / language");
  expect(
    await languages
      .locator("option")
      .evaluateAll((items) => items.map((item) => (item as HTMLOptionElement).value)),
  ).toEqual(["nl", "nl-en"]);
  await languages.selectOption("nl");
  await expect(page.locator('.study-example-answer [lang="en"]')).toHaveCount(0);
  await expect(page.locator('[lang="fa"]')).toHaveCount(0);
  await expect(answer).toHaveValue("Ik speel graag voetbal met mijn vrienden.");
  await languages.selectOption("nl-en");
  await expect(page.locator('.study-example-answer [lang="en"]').first()).toBeVisible();
  await expect(answer).toHaveValue("Ik speel graag voetbal met mijn vrienden.");
  await page.getByRole("button", { name: /^Voorbeeld verbergen/ }).click();
  await expect(page.locator(".study-example-answer")).toHaveCount(0);
});

test("listening has three answer formats and one continuous recording per part", async ({ page }) => {
  const { topic } = await availableLesson(page, "pre-a1", "listening");
  await page.goto(`/learn/pre-a1?skill=listening&topic=${topic.id}&step=practise`);
  const parts = page.getByRole("navigation", { name: "Onderdelen van deze vaardigheid" });
  await expect(parts.getByRole("button")).toHaveCount(3);
  await expect(page.getByRole("textbox", { name: "Antwoord op vraag 1" })).toBeVisible();
  const [audio] = await Promise.all([
    page.waitForResponse(
      (value) => value.request().method() === "POST" && /\/study\/.+\/audio\?/.test(value.url()),
    ),
    page.getByRole("button", { name: /^Start de opname/ }).click(),
  ]);
  expect(audio.ok()).toBe(true);
  expect(audio.headers()["content-type"]).toContain("audio/wav");
  await expect(page.locator(".study-listen-player audio")).toHaveCount(1);
  await parts.getByRole("button").nth(1).click();
  await expect(page.locator(".study-question").first().getByRole("radio").first()).toBeVisible();
  await parts.getByRole("button").nth(2).click();
  await expect(page.getByRole("textbox", { name: "Antwoord op vraag 1" })).toBeVisible();
  await expect(page.locator(".study-listen-player details")).not.toHaveAttribute("open", "");
});

test("writing offers short and extended practice with temporary feedback and no pronunciation claim", async ({
  page,
}) => {
  const { topic } = await availableLesson(page, "a1", "writing");
  await page.goto(`/learn/a1?skill=writing&topic=${topic.id}&step=practise`);
  const parts = page.getByRole("navigation", { name: "Onderdelen van deze vaardigheid" });
  await expect(parts.getByRole("button")).toHaveCount(2);
  await expect(page.locator(".study-example-answer")).toHaveCount(0);
  const answer = page.getByLabel(/^Jouw antwoord/);
  await answer.fill("Ik woon in Gent. Mijn familie woont ook in Gent.");
  const [response] = await Promise.all([
    page.waitForResponse(
      (value) => value.request().method() === "POST" && /\/study\/.+\/feedback$/.test(value.url()),
    ),
    page.getByRole("button", { name: /^Bekijk mijn feedback/ }).click(),
  ]);
  expect(response.ok()).toBe(true);
  const report = await response.json();
  expect(report.ephemeral).toBe(true);
  expect(report.dimensions.pronunciation).toBeNull();
  await expect(page.getByRole("region", { name: "Tijdelijke oefenfeedback" })).toBeVisible();
  await parts.getByRole("button").nth(1).click();
  await expect(answer).toHaveValue("");
  await expect(page.getByRole("region", { name: "Tijdelijke oefenfeedback" })).toHaveCount(0);
});

test("the same workspace keeps its level and fits on a 390px phone", async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto("/learn/pre-a1?skill=reading");
  await expect(page.getByRole("button", { name: /^Alfabet & getallen/ })).toBeVisible();
  await page.getByRole("button", { name: /^Alfabet & getallen/ }).click();
  await expect(page.getByRole("heading", { name: /^Eerste woorden en klanken/ })).toBeVisible();
  const skills = page.getByRole("navigation", { name: "Kies een vaardigheid" });
  for (const name of ["Lezen", "Luisteren", "Spreken", "Schrijven"]) {
    await skills.getByRole("link", { name: new RegExp(`^${name}`) }).click();
    await expect(page.locator("#study-stage")).toHaveValue("pre-a1");
    await expect(page.getByRole("heading", { name: /^Waar wil je over leren/ })).toBeVisible();
    await expect
      .poll(() => page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth))
      .toBe(true);
  }
  await expect(page.getByRole("navigation", { name: "Mobiel hoofdmenu" }).getByRole("link")).toHaveCount(4);
});
