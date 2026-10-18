import AxeBuilder from "@axe-core/playwright";
import { expect, test } from "./fixtures/test";

test("learner path has twelve open stages without awarding test passes", async ({ page }) => {
  await page.goto("/leerpad");
  const path = page.getByTestId("curriculum-path");
  await expect(path.locator("li")).toHaveCount(12);
  await expect(path).not.toContainText(/A3/);
  await expect(path.getByRole("link", { name: "pre-A1 · Lezen", exact: true })).toBeVisible();
  await expect(path.locator(".stage-locked")).toHaveCount(0);
  await page.goto("/learn/a1");
  await expect(page.getByRole("heading", { name: /^Waar wil je over leren/ })).toBeVisible();
  await expect(page.getByRole("button", { name: "Start de eindtoets" })).toHaveCount(0);
});

test("support languages switch in place and persist after reload", async ({ page }) => {
  await page.goto("/learn/pre-a1?view=vocabulary");
  await expect(page.locator(".study-word").first()).toBeVisible();
  await expect(page.locator('.study-word [lang="en"]').first()).toBeVisible();
  await page.getByLabel("Taalhulp / language").selectOption("nl");
  await expect(page.locator('.study-word [lang="en"]')).toHaveCount(0);
  await expect(page.locator('[lang="fa"]')).toHaveCount(0);
  await page.reload();
  await expect(page.getByLabel("Taalhulp / language")).toHaveValue("nl");
  const me = await page.request.get("/api/me");
  expect((await me.json()).profile.support_mode).toBe("nl");
});

test("grammar stays a local tool beside reading without submitting answers or progress", async ({ page }) => {
  const submissions: string[] = [];
  page.on("request", (request) => {
    if (request.method() === "POST") submissions.push(new URL(request.url()).pathname);
  });
  await page.goto("/learn/pre-a1?skill=reading&topic=family&step=practise&view=grammar");
  const stage = await (await page.request.get("/api/curriculum/pre-a1")).json();
  const round = stage.grammar.find((item: { id: string }) => item.id.startsWith("practice-"));
  const question = round.practice[0];
  const grammar = page.getByRole("region", { name: "Grammaticaoefeningen", exact: true });
  await expect(grammar).toBeVisible();
  await grammar.locator(`input[name="q-${question.id}"]`).nth(question.answer_index).check();
  await grammar.getByRole("button", { name: /^Controleer je antwoord/ }).click();
  await expect(grammar.locator(".practice-correct")).toBeVisible();
  await expect(page.locator('.study-question input[type="radio"]:checked')).toHaveCount(0);
  expect(submissions.some((value) => /practice|feedback|attempt/.test(value))).toBe(false);
});

test("writing and its context remain accessible at desktop and narrow phone widths", async ({ page }) => {
  await page.goto("/learn/a2?skill=writing&topic=family&step=practise");
  await page.getByLabel(/^Jouw antwoord/).fill("Mijn familie woont in Gent.");
  await page.getByLabel("Taalhulp / language").selectOption("nl-en");
  for (const width of [1440, 390, 320]) {
    await page.setViewportSize({ width, height: 900 });
    await expect
      .poll(() => page.evaluate(() => document.documentElement.scrollWidth <= innerWidth))
      .toBe(true);
    const results = await new AxeBuilder({ page })
      .withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"])
      .analyze();
    expect(results.violations).toEqual([]);
  }
  await page.reload();
  await expect(page.getByLabel(/^Jouw antwoord/)).toHaveValue("");
});

test("a blocked final test cannot be started from a direct link", async ({ page }) => {
  await page.goto("/learn/a1/test");
  await page.getByRole("button", { name: "Start de eindtoets" }).click();
  await expect(page.getByRole("main").getByRole("alert")).toContainText(
    "Oefen eerst lezen, luisteren, spreken en schrijven",
  );
  await expect(page.getByRole("button", { name: "Dien de eindtoets in" })).toHaveCount(0);
});

test("test interface protects a recording and retries an unchanged submitted snapshot after reload", async ({
  page,
}) => {
  const copy = (nl: string) => ({ nl, en: "", fa: "" });
  const task = {
    prompt: copy("Vertel wie je bent."),
    criteria: [copy("Stel jezelf voor.")],
    min_words: 1,
    max_words: 30,
  };
  const attempt = {
    id: "b1b03f44-d38d-47eb-9f32-8c593420f6bb",
    stage_id: "pre-a1",
    status: "in_progress",
    admin_preview: false,
    test: {
      reading: {
        text: copy("Noor woont in Gent."),
        questions: [{ id: "r1", prompt: copy("Waar woont Noor?"), options: [copy("Gent"), copy("Brugge")] }],
      },
      listening: {
        audio_parts: 1,
        questions: [{ id: "l1", prompt: copy("Wat hoor je?"), options: [copy("Hallo"), copy("Tot morgen")] }],
      },
      speaking: task,
      writing: task,
    },
    results: null,
  };
  let submitted: Record<string, unknown> | null = null;
  let submissions = 0;
  await page.route("**/api/curriculum/pre-a1/test", (route) => route.fulfill({ json: attempt }));
  await page.route(`**/api/curriculum/attempts/${attempt.id}`, (route) =>
    route.fulfill({ json: { ...attempt, submission: submitted } }),
  );
  await page.route("**/api/speech/transcribe", async (route) => {
    await new Promise((resolve) => setTimeout(resolve, 200));
    await route.fulfill({
      json: {
        audio: { asset_id: "d3479e43-457b-4ab5-80c9-c2488db2b474" },
        transcript: { text: "Ik heet Noor en ik woon in Gent." },
      },
    });
  });
  await page.route(`**/api/curriculum/attempts/${attempt.id}/submit`, async (route) => {
    const body = route.request().postDataJSON();
    submissions++;
    if (submitted) expect(body).toEqual(submitted);
    submitted = body;
    await new Promise((resolve) => setTimeout(resolve, 200));
    if (submissions === 1)
      await route.fulfill({ status: 503, json: { detail: "temporary service failure" } });
    else
      await route.fulfill({
        json: {
          ...attempt,
          status: "needs_practice",
          submission: submitted,
          results: Object.fromEntries(
            ["reading", "listening", "speaking", "writing"].map((skill) => [
              skill,
              { passed: false, feedback: copy("Oefen nog eens met een nieuwe situatie.") },
            ]),
          ),
        },
      });
  });
  await page.goto("/learn/pre-a1/test");
  await page.getByRole("button", { name: "Start de eindtoets" }).click();
  await page.locator('input[name="q-r1"]').first().check();
  const tabs = page.getByRole("navigation", { name: "Onderdelen van de eindtoets" });
  await tabs.getByRole("button", { name: /Luisteren/ }).click();
  await page.locator('input[name="q-l1"]').first().check();
  await expect(page.getByText("Lees mee als je hulp nodig hebt")).toHaveCount(0);
  await tabs.getByRole("button", { name: /Spreken/ }).click();
  await page.getByRole("button", { name: "Start de opname", exact: true }).click();
  await expect(page.getByRole("button", { name: "Stop de opname", exact: true })).toBeVisible();
  await expect(tabs.getByRole("button", { name: /Schrijven/ })).toBeDisabled();
  await page.getByRole("button", { name: "Stop de opname", exact: true }).click();
  await expect(page.getByText("Je opname is klaar om in te dienen.")).toBeVisible();
  await tabs.getByRole("button", { name: /Schrijven/ }).click();
  await page.getByLabel("Jouw antwoord in het Nederlands").fill("Ik heet Noor.");
  await page.getByRole("button", { name: "Dien de eindtoets in" }).click();
  await expect(page.getByRole("button", { name: "Probeer dezelfde inzending opnieuw" })).toBeVisible();
  await expect(page.getByLabel("Jouw antwoord in het Nederlands")).toBeDisabled();
  await page.reload();
  await expect(page.getByRole("button", { name: "Probeer dezelfde inzending opnieuw" })).toBeEnabled();
  await page.getByRole("button", { name: "Probeer dezelfde inzending opnieuw" }).click();
  await expect(page.locator(".skill-result")).toHaveCount(4);
  await expect(page.locator(".result-banner")).toContainText("verder kunt oefenen");
  expect(submissions).toBe(2);
});

test("grammar rounds stay manageable and accessible on a narrow phone", async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto("/learn/a2?view=grammar");
  const practice = page.getByRole("region", { name: "Grammaticaoefeningen", exact: true });
  await expect(practice.locator(".curriculum-question")).toHaveCount(1);
  await expect(practice.locator("#grammar-topic option")).not.toHaveCount(0);
  await expect(practice.getByRole("button", { name: /Controleer je antwoord/ })).toBeDisabled();
  await expect.poll(() => page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
  const results = await new AxeBuilder({ page })
    .withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"])
    .analyze();
  expect(results.violations).toEqual([]);
});
