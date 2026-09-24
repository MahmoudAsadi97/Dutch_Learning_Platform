import AxeBuilder from "@axe-core/playwright";
import { expect, test } from "@playwright/test";

test("learner path has twelve open stages without awarding test passes", async ({ page }) => {
  await page.goto("/");
  const path = page.getByTestId("curriculum-path");
  await expect(path.locator("li")).toHaveCount(12);
  await expect(path).not.toContainText(/A3/);
  await expect(path.getByRole("link", { name: /Open pre-A1:/ })).toBeVisible();
  await expect(path.locator('.stage-locked')).toHaveCount(0);
  await expect(path.getByRole("link", { name: /Open A1:/ })).toBeVisible();
  await page.goto("/learn/a1");
  await expect(page.getByRole("heading", {name: /Woorden die je kunt gebruiken/})).toBeVisible();
  await expect(page.getByRole("button", { name: "Start de eindtoets" })).toHaveCount(0);
});

test("support languages switch without losing the exercise and persist after reload", async ({ page }) => {
  await page.goto("/learn/pre-a1");
  await expect(page.locator(".vocabulary-card")).not.toHaveCount(0);
  await page.locator(".word-reveal").first().click();
  await expect(page.locator(".word-answer [lang=en]").first()).toBeVisible();
  await expect(page.locator(".word-answer [lang=fa]")).toHaveCount(0);
  await page.getByLabel("Taalhulp / language").selectOption("nl-fa");
  await expect(page.locator(".word-answer [lang=fa]").first()).toBeVisible();
  await expect(page.locator(".word-answer [lang=en]")).toHaveCount(0);
  await page.getByLabel("Taalhulp / language").selectOption("nl-fa-en");
  await expect(page.locator(".word-answer [lang=en]").first()).toBeVisible();
  await expect(page.locator(".word-answer [lang=fa]").first()).toHaveAttribute("dir", "rtl");
  await page.reload();
  await expect(page.getByLabel("Taalhulp / language")).toHaveValue("nl-fa-en");
});

test("grammar answers do not pollute the submitted reading answers", async ({ page }) => {
  await page.goto("/learn/pre-a1");
  const response = await page.request.get("/api/curriculum/pre-a1");
  expect(response.status()).toBe(200);
  const stage = await response.json();
  const nav = page.getByRole("navigation", { name: "Onderdelen van dit niveau" });
  await nav.getByRole("button", { name: "Grammatica", exact: true }).click();
  const grammar = stage.grammar[0].practice[0];
  await page.locator(`input[name="q-${grammar.id}"]`).nth(grammar.answer_index).check();
  await page.getByRole("button", { name: "Controleer je zin" }).first().click();
  await expect(page.locator(".practice-correct").first()).toBeVisible();
  await nav.getByRole("button", { name: "Lezen", exact: true }).click();
  await page.getByRole("button", { name: "Startles", exact: true }).click();
  for (const question of stage.lesson.reading_questions) {
    await page.locator(`input[name="q-${question.id}"]`).nth(question.answer_index).check();
  }
  await page.getByRole("button", { name: "Rond lezen af" }).click();
  await expect(page.locator(".practice-feedback")).toContainText("Een stap verder.");
  await expect(page.locator(".unit-test-card")).toContainText("1 van 4");
  await expect(page.getByRole("link", { name: "Naar de eindtoets" })).toHaveCount(0);
});

test("new level retains writing within the tab and stays usable at phone widths", async ({ page }) => {
  await page.goto("/learn/pre-a1");
  const nav = page.getByRole("navigation", { name: "Onderdelen van dit niveau" });
  await nav.getByRole("button", { name: "Schrijven", exact: true }).click();
  await page.getByRole("button", { name: "Startles", exact: true }).click();
  await page.getByLabel("Jouw tekst", { exact: true }).fill("Ik heet Noor. Ik woon in Gent.");
  await page.reload();
  await nav.getByRole("button", { name: "Schrijven", exact: true }).click();
  await page.getByRole("button", { name: "Startles", exact: true }).click();
  await expect(page.getByLabel("Jouw tekst", { exact: true })).toHaveValue("Ik heet Noor. Ik woon in Gent.");
  await page.getByLabel("Taalhulp / language").selectOption("nl-fa-en");
  for (const width of [1440, 390, 320]) {
    await page.setViewportSize({ width, height: 900 });
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
    const results = await new AxeBuilder({ page }).withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"]).analyze();
    expect(results.violations).toEqual([]);
  }
});

test("a blocked final test cannot be started from a direct link", async ({ page }) => {
  await page.goto("/learn/a1/test");
  await page.getByRole("button", { name: "Start de eindtoets" }).click();
  await expect(page.getByRole("main").getByRole("alert")).toContainText("Oefen eerst lezen, luisteren, spreken en schrijven");
  await expect(page.getByRole("button", { name: "Dien de eindtoets in" })).toHaveCount(0);
});

test("completed practice protects a replacement recording and submission before moving on", async ({ page }) => {
  let recordings = 0;
  let submissions = 0;
  let releaseTranscription = () => {};
  let releasePractice = () => {};
  const transcriptionReady = new Promise<void>(resolve => { releaseTranscription = resolve; });
  const practiceReady = new Promise<void>(resolve => { releasePractice = resolve; });
  const assets = ["d3479e43-457b-4ab5-80c9-c2488db2b474", "53dc63d6-ab51-476b-9e60-cf2c36309016"];
  await page.route("**/api/speech/transcribe", async route => {
    const index = recordings++;
    if (index === 1) await transcriptionReady;
    await route.fulfill({ json: { audio: { asset_id: assets[index] }, transcript: { text: "Dag Sam. Ik heet Noor. Ik woon in Gent." } } });
  });
  await page.route("**/api/curriculum/pre-a1/practice", async route => {
    const index = submissions++;
    expect(route.request().postDataJSON()).toEqual({ skill: "speaking", audio_asset_id: assets[index] });
    if (index === 1) await practiceReady;
    await route.fulfill({ json: { completed: true, feedback: { nl: "Je hebt jezelf voorgesteld.", en: "", fa: "" } } });
  });
  try {
    await page.goto("/learn/pre-a1");
    const nav = page.getByRole("navigation", { name: "Onderdelen van dit niveau" });
    await nav.getByRole("button", { name: "Spreken", exact: true }).click();
    await page.getByRole("button", { name: "Startles", exact: true }).click();
    await page.getByRole("button", { name: "Start de opname", exact: true }).click();
    await page.getByRole("button", { name: "Stop de opname", exact: true }).click();
    const submit = page.getByRole("button", { name: "Rond spreken af", exact: true });
    await expect(submit).toBeEnabled();
    await submit.click();
    const next = page.getByRole("button", { name: "Volgende vaardigheid", exact: true });
    await expect(next).toBeEnabled();

    await page.getByRole("button", { name: "Opnieuw opnemen", exact: true }).click();
    await expect(page.getByRole("button", { name: "Stop de opname", exact: true })).toBeVisible();
    await expect(next).toBeDisabled();
    await expect(nav.getByRole("button", { name: "Schrijven", exact: true })).toBeDisabled();
    await page.getByRole("button", { name: "Stop de opname", exact: true }).click();
    await expect(page.getByRole("button", { name: "Je opname verwerken…", exact: true })).toBeVisible();
    await expect(next).toBeDisabled();
    releaseTranscription();
    await expect(submit).toBeEnabled();
    await submit.click();
    await expect(page.getByRole("button", { name: "Even nakijken…", exact: true })).toBeVisible();
    await expect(next).toBeDisabled();
    releasePractice();
    await expect(next).toBeEnabled();
    await next.click();
    await expect(page.getByLabel("Jouw tekst", { exact: true })).toBeVisible();
    expect(recordings).toBe(2);
    expect(submissions).toBe(2);
  } finally {
    releaseTranscription();
    releasePractice();
  }
});

test("test interface protects a recording and retries an unchanged submitted snapshot after reload", async ({ page }) => {
  const copy = (nl: string) => ({ nl, en: "", fa: "" });
  const task = { prompt: copy("Vertel wie je bent."), criteria: [copy("Stel jezelf voor.")], min_words: 1, max_words: 30 };
  const attempt = {
    id: "b1b03f44-d38d-47eb-9f32-8c593420f6bb", stage_id: "pre-a1", status: "in_progress", admin_preview: false,
    test: {
      reading: { text: copy("Noor woont in Gent."), questions: [{ id: "r1", prompt: copy("Waar woont Noor?"), options: [copy("Gent"), copy("Brugge")] }] },
      listening: { audio_parts: 1, questions: [{ id: "l1", prompt: copy("Wat hoor je?"), options: [copy("Hallo"), copy("Tot morgen")] }] },
      speaking: task, writing: task,
    }, results: null,
  };
  let submitted: Record<string, unknown> | null = null;
  let submissions = 0;
  await page.route("**/api/curriculum/pre-a1/test", route => route.fulfill({ json: attempt }));
  await page.route(`**/api/curriculum/attempts/${attempt.id}`, route => route.fulfill({ json: { ...attempt, submission: submitted } }));
  await page.route("**/api/speech/transcribe", async route => {
    await new Promise(resolve => setTimeout(resolve, 200));
    await route.fulfill({ json: { audio: { asset_id: "d3479e43-457b-4ab5-80c9-c2488db2b474" }, transcript: { text: "Ik heet Noor en ik woon in Gent." } } });
  });
  await page.route(`**/api/curriculum/attempts/${attempt.id}/submit`, async route => {
    const body = route.request().postDataJSON();
    submissions++;
    if (submitted) expect(body).toEqual(submitted);
    submitted = body;
    await new Promise(resolve => setTimeout(resolve, 200));
    if (submissions === 1) await route.fulfill({ status: 503, json: { detail: "temporary service failure" } });
    else await route.fulfill({ json: { ...attempt, status: "needs_practice", submission: submitted, results: Object.fromEntries(["reading", "listening", "speaking", "writing"].map(skill => [skill, { passed: false, feedback: copy("Oefen nog eens met een nieuwe situatie.") }])) } });
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
