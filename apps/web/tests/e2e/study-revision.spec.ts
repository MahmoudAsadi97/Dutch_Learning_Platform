import AxeBuilder from "@axe-core/playwright";
import { expect, test } from "./fixtures/test";
import { exampleFeedback } from "./fixtures/study";

test("a learner revises beside grounded feedback and explicitly checks the new draft", async ({ page }) => {
  await page.setViewportSize({ width: 320, height: 844 });
  const requests: { text: string; assistance_used: boolean }[] = [];
  await page.route("**/api/study/a2/topics/family/feedback", (route) => {
    requests.push(route.request().postDataJSON());
    if (requests.length === 2)
      return route.fulfill({ status: 503, json: { detail: "temporary service failure" } });
    return route.fulfill({
      json: {
        ...exampleFeedback,
        corrected_text: "Ik woon in Gent.",
        ...(requests.length > 2
          ? { score: 8, corrections: [], summary: { nl: "Je werkwoord klopt nu." } }
          : {}),
      },
    });
  });
  await page.goto("/learn/a2?skill=writing&topic=family&step=practise");
  const input = page.getByLabel(/^Jouw antwoord/);
  const check = page.getByRole("button", { name: /^Bekijk mijn feedback/ });
  await input.fill("Ik woont in Gent.");
  await check.click();
  const current = page.getByRole("region", { name: "Tijdelijke oefenfeedback" });
  await expect(current).toContainText("7/10");
  await expect(page.getByTestId("study-corrected-draft")).toHaveCount(0);
  await current.getByRole("button", { name: /^Toon je tekst met deze correcties/ }).click();
  await expect(page.getByTestId("study-corrected-draft")).toContainText("Ik woon in Gent.");
  await expect(input).toHaveValue("Ik woont in Gent.");
  await input.fill("Ik woon in Gent.");
  const previous = page.getByRole("complementary", { name: "Feedback op je vorige versie" });
  await expect(current).toHaveCount(0);
  await expect(previous).toContainText("Bij ik gebruik je de stam.");
  await expect(previous).toContainText("Vorige versie");
  expect(requests).toHaveLength(1);
  await check.click();
  await expect(page.locator(".study-error")).toBeVisible();
  await expect(input).toHaveValue("Ik woon in Gent.");
  await expect(previous).toBeVisible();
  await check.click();
  await expect(current).toContainText("8/10");
  expect(requests.map((request) => request.assistance_used)).toEqual([false, true, true]);
  await expect.poll(() => page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
  const audit = await new AxeBuilder({ page }).include('[data-testid="guided-lesson"]').analyze();
  expect(audit.violations).toEqual([]);
  await page.reload();
  await expect(input).toHaveValue("");
  await expect(previous).toHaveCount(0);
  await expect(current).toHaveCount(0);
});

test("authored word situations invite an attempt before the example and keep drafts temporary", async ({
  page,
}) => {
  await page.setViewportSize({ width: 320, height: 844 });
  await page.goto("/learn/a2?skill=reading");
  await page.getByRole("button", { name: /^Woordenlijst/ }).click();
  await page.getByLabel("Zoek in de woordenlijst").fill("identiteitskaart");
  const word = page
    .getByRole("region", { name: "Woordenlijst van dit niveau" })
    .locator(".study-word")
    .first();
  await expect(word).toContainText("de identiteitskaart");
  await word.locator("summary").click();
  const draft = word.getByLabel(/^Jouw zin met/);
  await expect(draft).toBeVisible();
  await expect(word.locator(".study-word-transfer-example")).toBeHidden();
  await draft.fill("Ik toon mijn identiteitskaart aan het loket.");
  await word.getByRole("button", { name: /^Toon een mogelijk voorbeeld/ }).click();
  await expect(word.locator(".study-word-transfer-example")).toBeVisible();
  await expect(word.locator(".study-word-transfer-example button").first()).toBeVisible();
  await expect(draft).toHaveValue("Ik toon mijn identiteitskaart aan het loket.");
  await word.getByRole("button", { name: /^Volgende situatie/ }).click();
  await expect(draft).toHaveValue("");
  await expect(word.locator(".study-word-transfer-example")).toBeHidden();
  await draft.fill("Tijdelijke oefenzin.");
  await page.evaluate(() => window.dispatchEvent(new PageTransitionEvent("pageshow", { persisted: true })));
  await word.locator("summary").click();
  await expect(draft).toHaveValue("");
  await page.getByLabel("Taalhulp / language").selectOption("nl");
  await expect(word.locator('[lang="en"]')).toHaveCount(0);
  await expect.poll(() => page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
  const audit = await new AxeBuilder({ page }).include(".study-reference").analyze();
  expect(audit.violations).toEqual([]);
});

test("an indexed reading keeps its source example and authored verb forms together", async ({ page }) => {
  const endpoint = "/api/study/a2/topics/photography?skill=reading&activity_id=a2-s-reading-wrong-size-file";
  const response = await page.request.get(endpoint);
  expect(response.ok()).toBe(true);
  const lesson = await response.json();
  const prepared = lesson.preparation.words.find((word: { id: string }) => word.id === "a2-v156");
  expect(prepared.forms).toHaveLength(3);
  expect(prepared.contexts).toHaveLength(3);
  await page.goto("/learn/a2?skill=reading&topic=photography&activity=a2-s-reading-wrong-size-file");
  const word = page.getByTestId("guided-lesson").locator(".study-word").filter({ hasText: "vergelijken" });
  await expect(word.locator(".study-word-example")).toContainText(prepared.example.nl);
  await word.locator("summary").click();
  await expect(word.locator(".study-word-transfer-forms dd")).toHaveCount(3);
  await expect(word.locator(".study-word-transfer-forms")).toContainText(prepared.forms[1].text.nl);
  await expect(word.getByLabel(/^Jouw zin met/)).toBeVisible();
  const collapsed = page.getByTestId("guided-lesson").locator(".study-word").filter({ hasText: "de prijs" });
  expect((await collapsed.boundingBox())!.height).toBeLessThan((await word.boundingBox())!.height);
});
