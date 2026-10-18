import { readFile } from "node:fs/promises";
import path from "node:path";
import AxeBuilder from "@axe-core/playwright";
import type { Page } from "@playwright/test";
import { expect, test } from "./fixtures/test";

const copy = (nl: string, en: string) => ({ nl, en });
const fixtureWords = Array.from({ length: 500 }, (_, index) => ({
  id: "test-word-" + (index + 1),
  term: "woord" + (index + 1),
  topic: copy(index < 250 ? "Eten" : "Werk", index < 250 ? "Food" : "Work"),
  meaning: copy("Betekenis " + (index + 1), "Meaning " + (index + 1)),
  example: copy("Ik gebruik woord" + (index + 1) + " vandaag.", "I use word" + (index + 1) + " today."),
}));

/** Fixtures isolate pagination and media state from prose authoring; the API tests validate content. */
async function mockWords(page: Page) {
  await page.route(/\/api\/library\/pre-a1\/vocabulary(?:\?|$)/, async (route) => {
    const url = new URL(route.request().url());
    const query = (url.searchParams.get("q") ?? "").toLowerCase();
    const offset = Number(url.searchParams.get("offset") ?? 0);
    const limit = Number(url.searchParams.get("limit") ?? 18);
    const items = fixtureWords.filter((word) => JSON.stringify(word).toLowerCase().includes(query));
    await route.fulfill({
      json: { total: items.length, offset, limit, items: items.slice(offset, offset + limit) },
    });
  });
}

async function wordReference(page: Page) {
  await page.goto("/learn/pre-a1?skill=reading&view=vocabulary");
  const reference = page.getByRole("region", { name: "Woordenlijst van dit niveau" });
  await expect(reference.locator(".study-word").first()).toBeVisible();
  return reference;
}

async function writingSection(page: Page) {
  const response = await page.request.get("/api/study/a1/topics?skill=writing");
  expect(response.ok()).toBe(true);
  const catalog = await response.json();
  const topic = catalog.topics.find((item: { available: boolean }) => item.available);
  expect(topic).toBeTruthy();
  await page.goto("/learn/a1?skill=writing&topic=" + topic.id + "&step=practise");
  const draft = page.getByLabel(/^Jouw antwoord/);
  await expect(draft).toBeVisible();
  return draft;
}

function writingFeedback() {
  return {
    status: "evaluated",
    score: 7,
    dimensions: { task: 8, grammar: 6, vocabulary: 7, organisation: 7, pronunciation: null },
    summary: copy("Bekijk deze twee verbeteringen.", "Review these two corrections."),
    corrections: [
      {
        original: "Ik bent",
        replacement: "Ik ben",
        category: "grammar",
        explanation: copy("Bij ik gebruik je ben.", "Use ben with ik."),
      },
      {
        original: "Belgie",
        replacement: "België",
        category: "spelling",
        explanation: copy("Schrijf België met een trema.", "Write België with a diaeresis."),
      },
    ],
    checks: [],
    pronunciation_note: copy("Uitspraak is niet beoordeeld.", "Pronunciation was not assessed."),
    ephemeral: true,
  };
}

test("the compact word reference retains the full 500-word bank and resets pagination for searches", async ({
  page,
}) => {
  await mockWords(page);
  await page.setViewportSize({ width: 390, height: 844 });
  const bank = await wordReference(page);
  await expect(bank.locator(".study-word")).toHaveCount(18);
  await expect(bank.locator(".study-word-top strong").first()).toHaveText("woord1");
  await expect(bank.getByRole("button", { name: /^Vorige(?:\s|$)/ })).toBeDisabled();
  await bank.getByRole("button", { name: /Volgende woorden/ }).click();
  await expect(bank.locator(".study-word-top strong").first()).toHaveText("woord19");
  await page.getByLabel("Taalhulp / language").selectOption("nl-en");
  await bank.getByLabel("Zoek in de woordenlijst").fill("woord500");
  await expect(bank.locator(".study-word")).toHaveCount(1);
  await expect(bank.locator(".study-word-top strong")).toHaveText("woord500");
  await expect(bank.getByRole("button", { name: /Volgende woorden/ })).toBeDisabled();
  await expect(bank.locator('[lang="en"]').first()).toBeVisible();
  await bank.getByLabel("Zoek in de woordenlijst").fill("no-match-zzzz");
  await expect(bank.locator(".study-word")).toHaveCount(0);
  await expect(bank).toContainText("Geen woorden gevonden");
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
});

test("word and sentence pronunciation require a click and replay uses cached audio", async ({ page }) => {
  await mockWords(page);
  const wav = await readFile(path.resolve(__dirname, "../../../api/tests/fixtures/tone_1s.wav"));
  const spoken: string[] = [];
  await page.route("**/api/speech/synthesize", async (route) => {
    const body = route.request().postDataJSON();
    expect(body.store).toBe(false);
    spoken.push(body.text);
    await route.fulfill({
      body: wav,
      contentType: "audio/wav",
      headers: { "x-audio-voice": "fixture-tone" },
    });
  });
  const bank = await wordReference(page);
  const card = bank.locator(".study-word").first();
  expect(spoken).toEqual([]);
  const wordPlay = card.locator(".study-word-top .phrase-audio-button");
  await wordPlay.click();
  await expect.poll(() => spoken).toEqual(["woord1"]);
  await expect(wordPlay).toHaveAttribute("aria-pressed", "false");
  await expect(card).toContainText("Testtoon; dit is geen uitspraakvoorbeeld.");
  await wordPlay.click();
  await expect(wordPlay).toHaveAttribute("aria-pressed", "true");
  await expect(wordPlay).toHaveAttribute("aria-pressed", "false");
  expect(spoken).toEqual(["woord1"]);
  await card.locator(".study-word-example .phrase-audio-button").click();
  await expect.poll(() => spoken).toEqual(["woord1", "Ik gebruik woord1 vandaag."]);
});

test("a slower word search cannot display stale cards or replace a newer search", async ({ page }) => {
  await mockWords(page);
  let release = () => {};
  let started = () => {};
  let finished = () => {};
  const held = new Promise<void>((resolve) => {
    release = resolve;
  });
  const requested = new Promise<void>((resolve) => {
    started = resolve;
  });
  const completed = new Promise<void>((resolve) => {
    finished = resolve;
  });
  await page.route(/\/api\/library\/pre-a1\/vocabulary\?/, async (route) => {
    if (new URL(route.request().url()).searchParams.get("q") !== "woord500") {
      await route.fallback();
      return;
    }
    started();
    await held;
    try {
      await route.fulfill({ json: { total: 1, offset: 0, limit: 18, items: [fixtureWords[499]] } });
    } finally {
      finished();
    }
  });
  try {
    const bank = await wordReference(page);
    await bank.getByRole("button", { name: /Volgende woorden/ }).click();
    await expect(bank.locator(".study-word-top strong").first()).toHaveText("woord19");
    await bank.getByLabel("Zoek in de woordenlijst").fill("woord500");
    // The old page disappears immediately, not only after the replacement request completes.
    expect(await bank.locator(".study-word").count()).toBe(0);
    await requested;
    await bank.getByLabel("Zoek in de woordenlijst").fill("woord499");
    await expect(bank.locator(".study-word-top strong")).toHaveText(["woord499"]);
    release();
    await completed;
    await expect(bank.getByLabel("Zoek in de woordenlijst")).toHaveValue("woord499");
    await expect(bank.locator(".study-word-top strong")).toHaveText(["woord499"]);
  } finally {
    release();
  }
});

test("temporary writing feedback corrects real fragments and disappears when the draft changes", async ({
  page,
}) => {
  const original = "Ik bent Noor. Ik woon in Belgie.";
  await page.route(/\/api\/study\/a1\/topics\/[^/]+\/feedback$/, (route) => {
    expect(route.request().postDataJSON().text).toBe(original);
    return route.fulfill({ json: writingFeedback() });
  });
  const draft = await writingSection(page);
  await draft.fill(original);
  await page.getByRole("button", { name: /^Bekijk mijn feedback/ }).click();
  const report = page.getByRole("region", { name: "Tijdelijke oefenfeedback" });
  await expect(report.locator(".study-correction")).toHaveCount(2);
  await expect(report.locator("del").first()).toHaveText("Ik bent");
  await expect(report.locator(".study-correction strong").first()).toHaveText("Ik ben");
  await expect(report).toContainText("Schrijf België met een trema.");
  await expect(report.locator(".study-score")).toContainText("7/10");
  await expect(draft).toHaveValue(original);
  await page.getByLabel("Taalhulp / language").selectOption("nl-en");
  await expect(report).toContainText("Use ben with ik.");
  await expect(report.locator('[lang="fa"]')).toHaveCount(0);
  await draft.fill("Mijn nieuwe antwoord blijft staan.");
  await expect(report).toHaveCount(0);
  await page.reload();
  await expect(draft).toHaveValue("");
  await expect(report).toHaveCount(0);
});

test("writing service failures preserve the answer and a later successful review remains temporary", async ({
  page,
}) => {
  let calls = 0;
  await page.route(/\/api\/study\/a1\/topics\/[^/]+\/feedback$/, (route) => {
    calls++;
    return calls === 1
      ? route.fulfill({ status: 503, json: { detail: "temporarily unavailable" } })
      : route.fulfill({ json: writingFeedback() });
  });
  const draft = await writingSection(page);
  const error = page.getByTestId("study-practice").getByRole("alert");
  await draft.fill("Ik bent Noor. Ik woon in Belgie.");
  await page.getByRole("button", { name: /^Bekijk mijn feedback/ }).click();
  await expect(error).toBeVisible();
  await expect(draft).toHaveValue("Ik bent Noor. Ik woon in Belgie.");
  await expect(page.getByRole("region", { name: "Tijdelijke oefenfeedback" })).toHaveCount(0);
  await page.getByRole("button", { name: /^Bekijk mijn feedback/ }).click();
  await expect(page.getByRole("region", { name: "Tijdelijke oefenfeedback" })).toBeVisible();
  await draft.fill("Ik woon in België.");
  await expect(page.getByRole("region", { name: "Tijdelijke oefenfeedback" })).toHaveCount(0);
  await expect(error).toHaveCount(0);
});

test("an in-flight writing review cannot annotate an answer edited after its response", async ({ page }) => {
  let release = () => {};
  let started = () => {};
  const held = new Promise<void>((resolve) => {
    release = resolve;
  });
  const requested = new Promise<void>((resolve) => {
    started = resolve;
  });
  await page.route(/\/api\/study\/a1\/topics\/[^/]+\/feedback$/, async (route) => {
    started();
    await held;
    await route.fulfill({ json: writingFeedback() });
  });
  try {
    const draft = await writingSection(page);
    await draft.fill("Ik bent Noor. Ik woon in Belgie.");
    await page.getByRole("button", { name: /^Bekijk mijn feedback/ }).click();
    await requested;
    // Locking the submitted version prevents an older response from attaching to a newer answer.
    await expect(draft).toBeDisabled();
    await expect(page.getByRole("button", { name: /^Je antwoord bekijken/ })).toBeDisabled();
    release();
    const report = page.getByRole("region", { name: "Tijdelijke oefenfeedback" });
    await expect(report).toBeVisible();
    await expect(draft).toBeEnabled();
    await draft.fill("Mijn nieuwe antwoord blijft staan.");
    await expect(draft).toHaveValue("Mijn nieuwe antwoord blijft staan.");
    await expect(report).toHaveCount(0);
  } finally {
    release();
  }
});

test("compact bilingual words remain accessible at 320 and 390 pixels without autoplay", async ({
  page,
}, testInfo) => {
  await mockWords(page);
  let audioCalls = 0;
  await page.route("**/api/speech/synthesize", (route) => {
    audioCalls++;
    return route.abort();
  });
  for (const width of [320, 390]) {
    await page.setViewportSize({ width, height: 844 });
    const bank = await wordReference(page);
    await page.getByLabel("Taalhulp / language").selectOption("nl-en");
    await expect(bank.locator('[lang="en"]').first()).toBeVisible();
    await page.evaluate(() => document.fonts.ready.then(() => undefined));
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
    const audit = await new AxeBuilder({ page })
      .include(".study-reference")
      .withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"])
      .analyze();
    expect(audit.violations).toEqual([]);
    await testInfo.attach("compact-words-" + width, {
      body: await page.screenshot({ fullPage: true }),
      contentType: "image/png",
    });
  }
  expect(audioCalls).toBe(0);
});
