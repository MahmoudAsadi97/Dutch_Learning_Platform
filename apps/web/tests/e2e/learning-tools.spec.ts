import { expect, test } from "./fixtures/test";

test("pre-A1 alphabet names and its listening round remain available inside the level", async ({ page }) => {
  const before = await (await page.request.get("/api/curriculum/pre-a1")).json();
  await page.goto("/learn/pre-a1?skill=reading");
  await page.getByRole("button", { name: /^Alfabet & getallen(?:\s|$)/ }).click();
  const alphabet = page.getByTestId("alphabet-practice");
  const picker = alphabet.getByRole("group", { name: "Kies een letter", exact: true });
  await expect(picker.getByRole("button")).toHaveCount(26);
  await expect(picker.getByRole("button", { name: "A", exact: true })).toHaveAttribute(
    "aria-pressed",
    "true",
  );
  await picker.getByRole("button", { name: "Z", exact: true }).click();
  await expect(picker.getByRole("button", { name: "Z", exact: true })).toHaveAttribute(
    "aria-pressed",
    "true",
  );
  await expect(picker.getByRole("button", { name: "A", exact: true })).toHaveAttribute(
    "aria-pressed",
    "false",
  );
  await expect(alphabet.locator(".alphabet-spoken-name")).toContainText("zet");
  await expect(alphabet.locator(".alphabet-focus")).toContainText("zon");
  await expect(alphabet.locator(".alphabet-focus .phrase-audio-button")).toHaveCount(2);
  const options = alphabet.getByRole("group", { name: "Welke letter hoor je?", exact: true });
  await expect(options.getByRole("button")).toHaveCount(4);
  await options.getByRole("button", { name: "D", exact: true }).click();
  await expect(alphabet.locator(".alphabet-answer")).toContainText("Juist: D heet dee.");
  await alphabet.getByRole("button", { name: /Volgende letter/ }).click();
  await expect(alphabet.locator(".alphabet-answer")).toHaveCount(0);
  await expect(options.getByRole("button").first()).toBeEnabled();
  const after = await (await page.request.get("/api/curriculum/pre-a1")).json();
  expect(after.progress).toEqual(before.progress);
  await page.goto("/learn/a1?skill=reading");
  await expect(page.getByRole("button", { name: /^Alfabet & getallen(?:\s|$)/ })).toHaveCount(0);
});

test("grammar remains independently reachable without awarding four-skill completion", async ({ page }) => {
  const before = await (await page.request.get("/api/curriculum/a2")).json();
  await page.goto("/learn/a2?skill=reading");
  await page.getByRole("button", { name: /^Grammatica(?:\s|$)/ }).click();
  const grammar = page.getByRole("region", { name: "Grammaticaoefeningen", exact: true });
  await expect(grammar).toBeVisible();
  await expect(grammar.locator("#grammar-topic")).toBeVisible();
  const question = grammar.locator(".curriculum-question").first();
  await expect(question.getByRole("radio").first()).toBeVisible();
  await question.getByRole("radio").first().check();
  await grammar.getByRole("button", { name: "Controleer je antwoord", exact: true }).click();
  await expect(question.getByRole("status")).toBeVisible();
  await expect(grammar.getByRole("button", { name: "Volgende vraag", exact: true })).toBeEnabled();
  await grammar.getByRole("button", { name: "Volgende vraag", exact: true }).click();
  await expect(grammar.locator(".grammar-position")).toContainText("Vraag 2");
  const after = await (await page.request.get("/api/curriculum/a2")).json();
  expect(after.progress).toEqual(before.progress);
  await expect(page.locator("#study-stage")).toHaveValue("a2");
  await expect(page.getByRole("navigation", { name: "Kies een vaardigheid" }).getByRole("link")).toHaveCount(
    4,
  );
});

test("topic words stay available while composing and opening support never erases the answer", async ({
  page,
}) => {
  const catalog = await (await page.request.get("/api/study/b1/topics?skill=writing")).json();
  const topic = catalog.topics.find((item: { available: boolean }) => item.available);
  expect(topic).toBeTruthy();
  await page.goto("/learn/b1?skill=writing&topic=" + topic.id);
  await expect(page.locator(".study-preparation .study-word").first()).toBeVisible();
  await expect(page.locator(".study-preparation .study-grammar")).not.toHaveCount(0);
  await page.getByRole("button", { name: /^Ik ben klaar om te oefenen/ }).click();
  const draft = page.getByLabel(/^Jouw antwoord/);
  await draft.fill("Mijn eigen antwoord blijft behouden terwijl ik woorden opzoek.");
  await expect(page.locator(".study-example-answer")).toHaveCount(0);
  await page.getByRole("button", { name: /^Woorden erbij(?:\s|$)/ }).click();
  await expect(page.locator(".study-lesson > .study-word-grid .study-word").first()).toBeVisible();
  await expect(draft).toHaveValue("Mijn eigen antwoord blijft behouden terwijl ik woorden opzoek.");
  await page.getByLabel("Taalhulp / language").selectOption("nl-en");
  await page.getByRole("button", { name: /^Bekijk een voorbeeldantwoord/ }).click();
  await expect(page.locator(".study-example-answer")).toBeVisible();
  await expect(draft).toHaveValue("Mijn eigen antwoord blijft behouden terwijl ik woorden opzoek.");
  await page.getByRole("button", { name: /^Woorden erbij(?:\s|$)/ }).click();
  await expect(draft).toHaveValue("Mijn eigen antwoord blijft behouden terwijl ik woorden opzoek.");
  await expect(page.locator('[lang="fa"]')).toHaveCount(0);
});
