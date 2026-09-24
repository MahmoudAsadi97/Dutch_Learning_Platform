import { readFile } from "node:fs/promises";
import path from "node:path";
import AxeBuilder from "@axe-core/playwright";
import { expect, test, type Page } from "@playwright/test";

const copy = (nl: string, en = `English: ${nl}`, fa = `فارسی: ${nl}`) => ({ nl, en, fa });
const fixtureWords = Array.from({ length: 500 }, (_, index) => ({
  id: `test-word-${index + 1}`, term: `woord${index + 1}`, topic: copy(index < 250 ? "Eten" : "Werk"),
  meaning: copy(`Betekenis ${index + 1}`), example: copy(`Ik gebruik woord${index + 1} vandaag.`),
}));
const fixtureStories = Array.from({ length: 100 }, (_, index) => ({
  id: `test-story-${index + 1}`, title: copy(`Een dag ${index + 1}`), topic: copy(index < 50 ? "Eten" : "Werk"),
  preview: copy(`Noor leest verhaal ${index + 1}.`), word_count: 16, paragraph_count: 2,
  paragraphs: [copy(`Noor leest verhaal ${index + 1}. Het is een mooie dag.`), copy("Daarna vertelt Noor het verhaal aan Sam.")],
  vocabulary: fixtureWords.slice(index * 5, index * 5 + 5),
  question: { id: `test-story-${index + 1}-understand`, prompt: copy("Wie leest het verhaal?"),
    options: [copy("Noor"), copy("Sam")], answer_index: 0, explanation: copy("In de eerste zin leest Noor het verhaal.") },
}));

/** Isolate browser state transitions from authored prose; the API suite checks every real content file. */
async function mockLibrary(page: Page) {
  await page.route(/\/api\/library\/pre-a1(?:\/|\?|$)/, async route => {
    const url = new URL(route.request().url());
    if (url.pathname === "/api/library/pre-a1") {
      await route.fulfill({ json: { learner_key: "library-browser-test", stage_id: "pre-a1", review_status: "unreviewed",
        vocabulary_count: 500, story_count: 100,
        topics: ["Eten", "Werk"].map(key => ({ key, label: copy(key), vocabulary_count: 250, story_count: 50 })) } });
      return;
    }
    const storyId = url.pathname.split("/stories/")[1];
    if (storyId) {
      const story = fixtureStories.find(item => item.id === storyId);
      await route.fulfill({ status: story ? 200 : 404, json: story ?? { detail: "story not found" } });
      return;
    }
    const isWords = url.pathname.endsWith("/vocabulary");
    const query = (url.searchParams.get("q") ?? "").toLowerCase();
    const topic = url.searchParams.get("topic") ?? "";
    const offset = Number(url.searchParams.get("offset") ?? 0);
    const limit = Number(url.searchParams.get("limit") ?? (isWords ? 20 : 12));
    const items = (isWords ? fixtureWords : fixtureStories).filter(item =>
      (!topic || item.topic.nl === topic) && (!query || JSON.stringify(item).toLowerCase().includes(query)));
    await route.fulfill({ json: { total: items.length, offset, limit, items: items.slice(offset, offset + limit) } });
  });
}

async function writingSection(page: Page) {
  await mockLibrary(page);
  await page.goto("/learn/pre-a1");
  await page.getByRole("navigation", { name: "Onderdelen van dit niveau" })
    .getByRole("button", { name: "Schrijven", exact: true }).click();
  return page.getByLabel("Jouw tekst", { exact: true });
}

function writingFeedback(original: string) {
  return { original_text: original, corrected_text: "Ik ben Noor. Ik woon in België.", review_status: "automated",
    corrections: [
      { original: "Ik bent", replacement: "Ik ben", category: "grammar", explanation: copy("Bij ik gebruik je ben.", "Use ben with ik.", "با ik از ben استفاده کن.") },
      { original: "Belgie", replacement: "België", category: "spelling", explanation: copy("Schrijf België met een trema.", "Write België with a diaeresis.", "België را با علامت دو نقطه بنویس.") },
    ], summary: copy("Bekijk deze twee verbeteringen.", "Review these two corrections.", "این دو اصلاح را بررسی کن.") };
}

test("word cards paginate a 500-word bank, filter topics and search without losing the selected language", async ({ page }) => {
  await mockLibrary(page);
  await page.goto("/learn/pre-a1");
  const bank = page.locator(".word-library");
  await expect(bank.getByRole("heading", { name: "500 woorden en uitdrukkingen" })).toBeVisible();
  await expect(bank.locator(".vocabulary-card")).toHaveCount(20);
  const pager = bank.getByRole("navigation", { name: "Pagina’s in de bibliotheek" });
  await expect(pager.getByRole("status")).toHaveText("1–20 van 500");
  await expect(pager.getByRole("button", { name: "Vorige", exact: true })).toBeDisabled();
  await pager.getByRole("button", { name: "Volgende", exact: true }).click();
  await expect(pager.getByRole("status")).toHaveText("21–40 van 500");
  await expect(bank.locator(".vocabulary-card h3").first()).toHaveText("woord21");
  await page.getByLabel("Taalhulp / language").selectOption("nl-fa-en");
  await bank.getByLabel("Onderwerp", { exact: true }).selectOption("Werk");
  await expect(pager.getByRole("status")).toHaveText("1–20 van 250");
  await expect(bank.locator(".vocabulary-card h3").first()).toHaveText("woord251");
  await bank.getByLabel("Zoeken", { exact: true }).fill("woord500");
  await expect(bank.locator(".vocabulary-card")).toHaveCount(1);
  await expect(pager.getByRole("status")).toHaveText("1–1 van 1");
  await expect(pager.getByRole("button", { name: "Volgende", exact: true })).toBeDisabled();
  await bank.getByRole("button", { name: "Toon de betekenis", exact: true }).click();
  await expect(bank.locator(".word-answer [lang=en]").first()).toBeVisible();
  await expect(bank.locator(".word-answer [lang=fa]").first()).toHaveAttribute("dir", "rtl");
  await bank.getByLabel("Zoeken", { exact: true }).fill("no-match-zzzz");
  await expect(pager.getByRole("status")).toHaveText("Geen resultaten");
  await expect(bank.locator(".vocabulary-card")).toHaveCount(0);
});

test("word and example audio requires an explicit click and repeats the cached word without another request", async ({ page }) => {
  await mockLibrary(page);
  const wav = await readFile(path.resolve(__dirname, "../../../api/tests/fixtures/tone_1s.wav"));
  const spoken: string[] = [];
  await page.route("**/api/speech/synthesize", async route => {
    const body = route.request().postDataJSON();
    expect(body.store).toBe(false);
    spoken.push(body.text);
    await route.fulfill({ body: wav, contentType: "audio/wav", headers: { "x-audio-voice": "fixture-tone" } });
  });
  await page.goto("/learn/pre-a1");
  const card = page.locator(".word-library .vocabulary-card").first();
  await expect(card.getByRole("heading")).toHaveText("woord1");
  expect(spoken).toEqual([]);
  await card.getByRole("button", { name: "Toon de betekenis", exact: true }).click();
  await expect(card.locator(".word-example")).toBeVisible();
  expect(spoken).toEqual([]);
  const wordPlay = card.locator(".word-card-heading .phrase-audio-button");
  await wordPlay.click();
  await expect.poll(() => spoken).toEqual(["woord1"]);
  await expect(wordPlay).toHaveAttribute("aria-pressed", "false");
  await expect(card).toContainText("Testtoon; dit is geen uitspraakvoorbeeld.");
  await wordPlay.click();
  await expect(wordPlay).toHaveAttribute("aria-pressed", "true");
  await expect(wordPlay).toHaveAttribute("aria-pressed", "false");
  expect(spoken).toEqual(["woord1"]);
  await card.locator(".word-example .phrase-audio-button").click();
  await expect.poll(() => spoken).toEqual(["woord1", "Ik gebruik woord1 vandaag."]);
});

test("Story Time reveals translations without resetting understanding and read marks never award assessment credit", async ({ page }) => {
  await mockLibrary(page);
  await page.goto("/learn/pre-a1");
  const before = await (await page.request.get("/api/curriculum/pre-a1")).json();
  await page.getByRole("navigation", { name: "Onderdelen van dit niveau" })
    .getByRole("button", { name: "Story Time", exact: true }).click();
  await expect(page.locator(".library-count")).toContainText("100 verhalen");
  await expect(page.locator(".story-tile")).toHaveCount(12);
  await page.getByRole("button", { name: "Lees Een dag 1", exact: true }).click();
  const reader = page.locator(".story-reader");
  await expect(reader.locator(".story-paragraph")).toHaveCount(2);
  await expect(reader.locator(".story-paper [lang=en]")).toHaveCount(0);
  await expect(reader.locator(".story-paper [lang=fa]")).toHaveCount(0);
  const choice = reader.locator('input[name="q-test-story-1-understand"]').first();
  await choice.check();
  await page.getByLabel("Taalhulp / language").selectOption("nl-fa-en");
  await reader.getByRole("button", { name: "Vertaling tonen", exact: true }).click();
  await expect(reader.locator(".story-paper [lang=en]")).toHaveCount(2);
  await expect(reader.locator(".story-paper [lang=fa]")).toHaveCount(2);
  await expect(choice).toBeChecked();
  await reader.getByRole("button", { name: "Controleer mijn begrip", exact: true }).click();
  await expect(reader.locator(".practice-correct")).toContainText("Goed gedaan.");
  await reader.getByRole("button", { name: "Vertaling verbergen", exact: true }).click();
  await expect(choice).toBeChecked();
  await expect(reader.locator(".practice-correct")).toBeVisible();
  await reader.getByRole("button", { name: "Markeer als gelezen", exact: true }).click();
  await expect(reader.getByRole("button", { name: "Gelezen", exact: true })).toBeDisabled();
  const after = await (await page.request.get("/api/curriculum/pre-a1")).json();
  expect(after.progress).toEqual(before.progress);
  await reader.getByRole("button", { name: "← Alle verhalen", exact: true }).click();
  await expect(page.locator(".library-count")).toContainText("1 gemarkeerd als gelezen");
  await page.reload();
  await page.getByRole("navigation", { name: "Onderdelen van dit niveau" })
    .getByRole("button", { name: "Story Time", exact: true }).click();
  await expect(page.locator(".library-count")).toContainText("1 gemarkeerd als gelezen");
});

test("writing corrections explain real fragments and require choosing the revised draft", async ({ page }) => {
  const original = "Ik bent Noor. Ik woon in Belgie.";
  await page.route("**/api/curriculum/pre-a1/writing-feedback", route => {
    expect(route.request().postDataJSON()).toEqual({ text: original });
    return route.fulfill({ json: writingFeedback(original) });
  });
  const draft = await writingSection(page);
  await draft.fill(original);
  const coach = page.getByRole("region", { name: "Schrijfhulp" });
  await coach.getByRole("button", { name: "Controleer spelling en grammatica", exact: true }).click();
  await expect(coach.locator(".correction-list > li")).toHaveCount(2);
  await expect(draft).toHaveValue(original);
  await expect(coach.locator("del").first()).toHaveText("Ik bent");
  await expect(coach.locator("ins").first()).toHaveText("Ik ben");
  await expect(coach).toContainText("Bij ik gebruik je ben.");
  await expect(coach).toContainText("Schrijf België met een trema.");
  await page.getByLabel("Taalhulp / language").selectOption("nl-fa-en");
  await expect(coach).toContainText("Use ben with ik.");
  await expect(coach.locator(".correction-list [lang=fa]").first()).toBeVisible();
  await coach.locator(".corrected-draft summary").click();
  await expect(coach.locator(".corrected-draft > p")).toHaveText("Ik ben Noor. Ik woon in België.");
  await coach.getByRole("button", { name: "Gebruik als nieuwe versie", exact: true }).click();
  await expect(draft).toHaveValue("Ik ben Noor. Ik woon in België.");
  await expect(coach.locator(".writing-review")).toHaveCount(0);
  await page.reload();
  await page.getByRole("navigation", { name: "Onderdelen van dit niveau" })
    .getByRole("button", { name: "Schrijven", exact: true }).click();
  await expect(draft).toHaveValue("Ik ben Noor. Ik woon in België.");
});

test("writing service errors preserve the draft and editing clears previous suggestions", async ({ page }) => {
  const original = "Ik bent Noor. Ik woon in Belgie.";
  let calls = 0;
  await page.route("**/api/curriculum/pre-a1/writing-feedback", route => {
    calls++;
    return calls === 1
      ? route.fulfill({ status: 503, json: { detail: "temporarily unavailable" } })
      : route.fulfill({ json: writingFeedback(original) });
  });
  const draft = await writingSection(page);
  await draft.fill(original);
  const coach = page.getByRole("region", { name: "Schrijfhulp" });
  await coach.getByRole("button", { name: "Controleer spelling en grammatica", exact: true }).click();
  await expect(coach.getByRole("alert")).toContainText("Je invoer blijft staan.");
  await expect(draft).toHaveValue(original);
  await expect(coach.locator(".writing-review")).toHaveCount(0);
  await coach.getByRole("button", { name: "Controleer spelling en grammatica", exact: true }).click();
  await expect(coach.locator(".writing-review")).toBeVisible();
  await draft.fill("Ik ben Noor. Vandaag woon ik in Gent.");
  await expect(coach.locator(".writing-review")).toHaveCount(0);
  await expect(coach.getByRole("alert")).toHaveCount(0);
});

test("a late writing response cannot overwrite or annotate a newer draft", async ({ page }) => {
  const original = "Ik bent Noor. Ik woon in Belgie.";
  let release = () => {};
  let started = () => {};
  let finished = () => {};
  const waitForRelease = new Promise<void>(resolve => { release = resolve; });
  const requestStarted = new Promise<void>(resolve => { started = resolve; });
  const requestFinished = new Promise<void>(resolve => { finished = resolve; });
  await page.route("**/api/curriculum/pre-a1/writing-feedback", async route => {
    started();
    await waitForRelease;
    try { await route.fulfill({ json: writingFeedback(original) }); } finally { finished(); }
  });
  try {
    const draft = await writingSection(page);
    await draft.fill(original);
    const coach = page.getByRole("region", { name: "Schrijfhulp" });
    await coach.getByRole("button", { name: "Controleer spelling en grammatica", exact: true }).click();
    await requestStarted;
    await expect(coach.getByRole("button", { name: "Je tekst nakijken…", exact: true })).toBeDisabled();
    await draft.fill("Mijn nieuwe antwoord blijft staan.");
    release();
    await requestFinished;
    await expect(draft).toHaveValue("Mijn nieuwe antwoord blijft staan.");
    await expect(coach.locator(".writing-review")).toHaveCount(0);
    await expect(coach.getByRole("button", { name: "Controleer spelling en grammatica", exact: true })).toBeEnabled();
  } finally { release(); }
});

test("pre-A1 alphabet has 26 selectable letters, letter names and an independent listening round", async ({ page }) => {
  await mockLibrary(page);
  await page.goto("/learn/pre-a1");
  await page.getByRole("navigation", { name: "Onderdelen van dit niveau" })
    .getByRole("button", { name: "Alfabet", exact: true }).click();
  const alphabet = page.getByTestId("alphabet-practice");
  const picker = alphabet.getByRole("group", { name: "Kies een letter", exact: true });
  await expect(picker.getByRole("button")).toHaveCount(26);
  await expect(picker.getByRole("button", { name: "A", exact: true })).toHaveAttribute("aria-pressed", "true");
  await picker.getByRole("button", { name: "Z", exact: true }).click();
  await expect(picker.getByRole("button", { name: "Z", exact: true })).toHaveAttribute("aria-pressed", "true");
  await expect(picker.getByRole("button", { name: "A", exact: true })).toHaveAttribute("aria-pressed", "false");
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
  await page.goto("/learn/a1");
  await expect(page.getByRole("navigation", { name: "Onderdelen van dit niveau" })
    .getByRole("button", { name: "Alfabet", exact: true })).toHaveCount(0);
});

test("delayed word searches never pair an updated pager with stale cards or restore an older result", async ({ page }) => {
  await mockLibrary(page);
  let release = () => {};
  let started = () => {};
  let finished = () => {};
  const waitForRelease = new Promise<void>(resolve => { release = resolve; });
  const requestStarted = new Promise<void>(resolve => { started = resolve; });
  const requestFinished = new Promise<void>(resolve => { finished = resolve; });
  await page.route(/\/api\/library\/pre-a1\/vocabulary\?/, async route => {
    if (new URL(route.request().url()).searchParams.get("q") !== "woord500") {
      await route.fallback();
      return;
    }
    started();
    await waitForRelease;
    try {
      await route.fulfill({ json: { total: 1, offset: 0, limit: 20, items: [fixtureWords[499]] } });
    } finally { finished(); }
  });
  try {
    await page.goto("/learn/pre-a1");
    const bank = page.locator(".word-library");
    const pager = bank.getByRole("navigation", { name: "Pagina’s in de bibliotheek" });
    await pager.getByRole("button", { name: "Volgende", exact: true }).click();
    await expect(bank.locator(".vocabulary-card h3").first()).toHaveText("woord21");
    await expect(pager.getByRole("status")).toHaveText("21–40 van 500");
    await bank.getByLabel("Zoeken", { exact: true }).fill("woord500");

    // Observe one DOM snapshot without retrying past the debounce: the previous
    // page must disappear as soon as the query changes, before a response exists.
    expect(await bank.evaluate(element => ({
      cards: element.querySelectorAll(".vocabulary-card").length,
      pagers: element.querySelectorAll(".library-pagination").length,
      loading: element.textContent?.includes("Woordkaarten laden…"),
    }))).toEqual({ cards: 0, pagers: 0, loading: true });
    await requestStarted;
    await expect(bank.getByRole("status")).toHaveText("Woordkaarten laden…");
    await expect(pager).toHaveCount(0);

    // A newer search completes first; releasing the older request cannot
    // replace its card, search value, or page range.
    await bank.getByLabel("Zoeken", { exact: true }).fill("woord499");
    await expect(bank.locator(".vocabulary-card h3")).toHaveText(["woord499"]);
    release();
    await requestFinished;
    await expect(bank.getByLabel("Zoeken", { exact: true })).toHaveValue("woord499");
    await expect(bank.locator(".vocabulary-card h3")).toHaveText(["woord499"]);
    await expect(pager.getByRole("status")).toHaveText("1–1 van 1");
    await expect(pager.getByRole("button", { name: "Volgende", exact: true })).toBeDisabled();
  } finally { release(); }
});

test("word cards and translated Story Time remain accessible and fit 320 and 390 pixel screens without autoplay", async ({ page }, testInfo) => {
  await mockLibrary(page);
  const wav = await readFile(path.resolve(__dirname, "../../../api/tests/fixtures/tone_1s.wav"));
  const spoken: string[] = [];
  await page.route("**/api/speech/synthesize", async route => {
    spoken.push(route.request().postDataJSON().text);
    await route.fulfill({ body: wav, contentType: "audio/wav", headers: { "x-audio-voice": "fixture-tone" } });
  });
  for (const width of [320, 390]) {
    await page.setViewportSize({ width, height: 844 });
    await page.goto("/learn/pre-a1");
    await page.getByLabel("Taalhulp / language").selectOption("nl-fa-en");
    const bank = page.locator(".word-library");
    await bank.getByRole("button", { name: "Toon de betekenis", exact: true }).first().click();
    await expect(bank.locator(".word-answer [lang=en]").first()).toBeVisible();
    await expect(bank.locator(".word-answer [lang=fa]").first()).toHaveAttribute("dir", "rtl");
    await page.evaluate(() => document.fonts.ready.then(() => undefined));
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
    const wordsAudit = await new AxeBuilder({ page }).include(".word-library")
      .withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"]).analyze();
    await testInfo.attach(`word-cards-rtl-${width}`, {
      body: await page.screenshot({ fullPage: true }), contentType: "image/png",
    });
    expect(wordsAudit.violations).toEqual([]);

    await page.getByRole("navigation", { name: "Onderdelen van dit niveau" })
      .getByRole("button", { name: "Story Time", exact: true }).click();
    await page.getByRole("button", { name: "Lees Een dag 1", exact: true }).click();
    const reader = page.locator(".story-reader");
    await reader.getByRole("button", { name: "Vertaling tonen", exact: true }).click();
    await expect(reader.locator(".story-paper [lang=fa]").first()).toHaveAttribute("dir", "rtl");
    await expect(reader.locator(".story-paper [lang=en]").first()).toBeVisible();
    await reader.locator(".story-word-strip summary").first().click();
    await expect(reader.locator(".story-word-strip details[open] [lang=fa]").first()).toBeVisible();
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
    const storyAudit = await new AxeBuilder({ page }).include(".story-reader")
      .withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"]).analyze();
    await testInfo.attach(`story-reader-rtl-${width}`, {
      body: await page.screenshot({ fullPage: true }), contentType: "image/png",
    });
    expect(storyAudit.violations).toEqual([]);
    expect(spoken).toEqual([]);
  }
});
