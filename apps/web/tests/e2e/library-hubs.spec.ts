import AxeBuilder from "@axe-core/playwright";
import { expect, test } from "./fixtures/test";
import type { StudyCatalog } from "../../lib/client/study";

/** Real content is discoverable through the level workspace; inventories are kept off learner pages. */
for (const width of [1440, 390]) {
  test(`word discovery preserves its stage and vocabulary view at ${width}px`, async ({ page }) => {
    await page.setViewportSize({ width, height: 900 });
    await page.goto("/woorden?stage=pre-a2");
    await expect(page).toHaveURL(/\/learn\/pre-a2\?skill=reading&view=vocabulary/);
    await expect(page.getByTestId("word-review")).toHaveCount(0);
    await expect(page.locator("#study-stage")).toHaveValue("pre-a2");
    await expect(page.locator("#study-stage option")).toHaveCount(12);
    const reference = page.locator(".study-reference");
    await expect(reference.locator(".study-word").first()).toBeVisible();
    const response = await page.request.get("/api/library/pre-a2/vocabulary?limit=18");
    expect(response.ok()).toBe(true);
    const bank = await response.json();
    expect(bank.total).toBeGreaterThanOrEqual(500);
    await expect(reference.locator(".study-word")).toHaveCount(bank.items.length);
    await expect(page.locator(".library-hub-counts,.coverage-summary")).toHaveCount(0);
    await page.locator("#study-stage").selectOption("c2");
    await expect(page).toHaveURL(/\/learn\/c2\?skill=reading&view=vocabulary/);
    await expect(reference.locator(".study-word").first()).toBeVisible();
    await page.reload();
    await expect(reference.locator(".study-word").first()).toBeVisible();
    await expect(page.locator("#study-stage")).toHaveValue("c2");
    await expect
      .poll(() => page.evaluate(() => document.documentElement.scrollWidth <= innerWidth))
      .toBe(true);
  });
}

test("reading discovery opens a coherent story while personal episodes stay nested", async ({ page }) => {
  await page.goto("/verhalen?stage=pre-a2");
  await expect(page).toHaveURL(/\/learn\/pre-a2\?skill=reading/);
  await expect(page.getByTestId("story-library")).toHaveCount(0);
  const response = await page.request.get("/api/study/pre-a2/topics?skill=reading");
  expect(response.ok()).toBe(true);
  const catalogue = (await response.json()) as StudyCatalog;
  const topic = catalogue.topics.find((item) => item.available);
  expect(topic).toBeTruthy();
  await page.locator(`.study-topic-card[href*="topic=${topic!.id}"]`).click();
  await page.getByRole("button", { name: /^Ik ben klaar om te oefenen/ }).click();
  const lines = page.locator(".study-story-line");
  await expect(lines.first()).toBeVisible();
  expect(await lines.count()).toBeGreaterThanOrEqual(8);
  expect(await lines.count()).toBeLessThanOrEqual(12);
  const results = await new AxeBuilder({ page }).include("#main").analyze();
  expect(results.violations.filter((issue) => ["critical", "serious"].includes(issue.impact ?? ""))).toEqual(
    [],
  );
  await page.goto("/verhalen?stage=pre-a2&view=personal");
  await expect(page).toHaveURL(/\/learn\/pre-a2\?skill=reading&view=personal-stories/);
  await expect(page.getByTestId("study-personal-stories")).toBeVisible();
  await expect(page.getByTestId("story-library")).toBeVisible();
});

for (const width of [1440, 390]) {
  test(`grammar stays selected on stage change and reload at ${width}px`, async ({ page }) => {
    await page.setViewportSize({ width, height: 900 });
    await page.goto("/learn/a1?skill=reading&view=grammar");
    const grammar = page.locator(".grammar-practice");
    await expect(grammar.locator(".curriculum-question")).toHaveCount(1);
    await expect(page.locator("#study-stage option")).toHaveCount(12);
    await page.locator("#study-stage").selectOption("pre-a2");
    await expect(page).toHaveURL(/\/learn\/pre-a2\?skill=reading&view=grammar/);
    await expect(grammar.locator(".curriculum-question")).toHaveCount(1);
    await expect(grammar.locator(".grammar-position")).toContainText("Vraag 1 van 10");
    await page.reload();
    await expect(page.locator("#study-stage")).toHaveValue("pre-a2");
    await expect(grammar.locator(".curriculum-question")).toHaveCount(1);
    await expect
      .poll(() => page.evaluate(() => document.documentElement.scrollWidth <= innerWidth))
      .toBe(true);
  });
}

test("grammar keeps previous answers and resets position for another topic", async ({ page }) => {
  await page.goto("/learn/pre-a2?skill=reading&view=grammar");
  const response = await page.request.get("/api/curriculum/pre-a2");
  expect(response.ok()).toBe(true);
  const stage = await response.json();
  const round = stage.grammar.find((topic: { id: string }) => topic.id.startsWith("practice-"));
  expect(round.practice).toHaveLength(10);
  const [first, second] = round.practice;
  const grammar = page.locator(".grammar-practice");
  await expect(grammar.locator(".curriculum-question")).toHaveCount(1);
  await expect(grammar.getByRole("button", { name: /^Vorige vraag/ })).toBeDisabled();
  await expect(grammar.getByRole("button", { name: /^Controleer je antwoord/ })).toBeDisabled();
  const choice = grammar.locator(`input[name="q-${first.id}"]`).nth(first.answer_index);
  await choice.check();
  await grammar.getByRole("button", { name: /^Controleer je antwoord/ }).click();
  await expect(grammar.locator(".practice-correct")).toContainText("Goed gedaan.");
  await grammar.getByRole("button", { name: /^Volgende vraag/ }).click();
  await expect(grammar.locator(".grammar-position")).toContainText("Vraag 2 van 10");
  await expect(grammar.locator(`input[name="q-${first.id}"]`)).toHaveCount(0);
  await expect(grammar.locator(`input[name="q-${second.id}"]`).first()).toBeVisible();
  await grammar.getByRole("button", { name: /^Vorige vraag/ }).click();
  await expect(choice).toBeChecked();
  await expect(grammar.locator(".practice-correct")).toContainText("Goed gedaan.");
  await grammar.getByRole("button", { name: /^Volgend onderwerp/ }).click();
  await expect(grammar.locator(".grammar-position")).toContainText("Vraag 1 van 10");
  await expect(grammar.locator(".curriculum-question")).toHaveCount(1);
  await expect(grammar.getByRole("button", { name: /^Vorige vraag/ })).toBeDisabled();
});

test("the directory has twelve levels with four skills each and opens pre-A2 reading", async ({ page }) => {
  await page.goto("/leerpad");
  const cards = page.getByTestId("curriculum-path").locator(":scope > li");
  await expect(cards).toHaveCount(12);
  for (const card of await cards.all()) await expect(card.locator(".study-level-skills a")).toHaveCount(4);
  const target = cards.filter({ has: page.locator(".study-stage-code").filter({ hasText: /^pre-A2$/ }) });
  for (const [label, skill] of [
    ["Lezen", "reading"],
    ["Luisteren", "listening"],
    ["Spreken", "speaking"],
    ["Schrijven", "writing"],
  ]) {
    await expect(target.getByRole("link", { name: `pre-A2 · ${label}`, exact: true })).toHaveAttribute(
      "href",
      `/learn/pre-a2?skill=${skill}`,
    );
  }
  await expect(page.locator(".coverage-summary,.library-hub-counts")).toHaveCount(0);
  await target.getByRole("link", { name: "pre-A2 · Lezen", exact: true }).click();
  await expect(page).toHaveURL(/\/learn\/pre-a2\?skill=reading/);
  await expect(page.locator("#study-stage")).toHaveValue("pre-a2");
  await expect(page.locator(".study-topic-card[href]").first()).toBeVisible();
});

test("320px level cards keep all skill labels within their card without totals", async ({ page }) => {
  await page.setViewportSize({ width: 320, height: 900 });
  await page.goto("/leerpad");
  const target = page
    .getByTestId("curriculum-path")
    .locator(":scope > li")
    .filter({ has: page.locator(".study-stage-code").filter({ hasText: /^C2$/ }) });
  await expect(target).toHaveCount(1);
  await target.scrollIntoViewIfNeeded();
  await expect(target.locator(".study-level-skills a")).toHaveCount(4);
  await expect(target.locator(".coverage-summary")).toHaveCount(0);
  await expect
    .poll(() =>
      target.evaluate((card) => {
        const box = card.getBoundingClientRect();
        return [...card.querySelectorAll<HTMLElement>(".study-level-skills a")].every((link) => {
          const rect = link.getBoundingClientRect();
          return link.scrollWidth <= link.clientWidth + 1 && rect.left >= box.left && rect.right <= box.right;
        });
      }),
    )
    .toBe(true);
  await expect.poll(() => page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
});
