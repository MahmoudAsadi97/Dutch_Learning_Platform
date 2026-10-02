import AxeBuilder from "@axe-core/playwright";
import { expect, test, type Page } from "@playwright/test";

/** Browser checks for the serial, the word bank and the daily plan. Route fixtures drive the states a
 * learner meets; the API suite proves the engine itself. One unmocked check proves the real path. */

const episodeId = "11111111-2222-4333-8444-555555555555";
const paragraphs = [
  { nl: "Het is maandag. Sami gaat naar zijn werk. Hij werkt in de fietsenwinkel.", en: "It is Monday. Sami goes to work." },
  { nl: "Sami gaat naar de bakkerij op de hoek. Ayşe staat achter de toonbank.", en: "Sami goes to the bakery on the corner." },
  { nl: "Baas, de oude hond, ligt bij de deur. Hij heeft iets in zijn mond.", en: "Baas, the old dog, is lying by the door." },
];
const glossary = [
  { term: "de toonbank", meaning_en: "the counter", meaning_fa: "پیشخوان", example: "Ayşe staat achter de toonbank." },
  { term: "de mond", meaning_en: "the mouth", meaning_fa: "دهان", example: "Hij heeft iets in zijn mond." },
];
const questions = [
  { index: 0, prompt: "Waar werkt Sami?", options: ["In de bakkerij.", "In de fietsenwinkel.", "Op het station."] },
  { index: 1, prompt: "Wie ligt bij de deur?", options: ["Ayşe.", "Tom.", "Baas."] },
];
const choices = [{ id: "a" as const, label: "Sami vraagt Tom om hulp." }, { id: "b" as const, label: "Sami gaat naar mevrouw De Clercq." }];
const series = { id: "s1", title: "De Lindestraat", stage_id: "a1", episode_count: 3, town: "Zilverdonk",
  cast: [{ name: "Sami", role: "fietsenmaker bij De Trapper" }, { name: "Ayşe", role: "bakker" }], memory: [{ number: 2, title: "De markt", recap: "Sami kocht appels.", choice: "" }] };

function episode(overrides: Record<string, unknown> = {}) {
  return { id: episodeId, number: 3, stage_id: "a1", status: "ready", error_code: "", title: "De sleutel van Sami", theme: "Een sleutel kwijt",
    theme_source: "auto", topic_id: "a1-t004", mood: "light", word_count: 127, read_at: null, rating: 0, chosen_choice: "", created_at: "2026-10-02T07:00:00Z",
    content_status: "generated", attempts: 1, warnings: [], failure_reasons: [], paragraphs, glossary, choices, questions, answered: false, previous_choice: "", read_aloud: {},
    provider: "local-ollama-strong", model: "llama3.1:8b", ...overrides };
}
function plan(overrides: Record<string, unknown> = {}) {
  return { date: "2026-10-02", streak: { current: 4, best: 9, today_active: false, today_points: 0, active_days: 12 },
    goal: { target: 20, points: 0, met: false }, series, episode: episode(), failed: null, awaiting_choice: null,
    words: { due_count: 3, total: 18, learned_count: 5, new_count: 2, preview: [] }, next_step: "read",
    recent_days: Array.from({ length: 14 }, (_, i) => ({ day: `2026-09-${String(19 + i).padStart(2, "0")}`, points: i % 3 ? 22 : 0, goal_met: i % 3 !== 0 })),
    levels: [{ id: "a1", label: "A1" }, { id: "a2", label: "A2" }], ...overrides };
}

async function storyFixture(page: Page) {
  let state = episode();
  const posts: string[] = [];
  await page.route(/\/api\/today(?:\?|$)/, route => route.fulfill({ json: plan({ episode: state }) }));
  await page.route(/\/api\/stories\/episodes\/[^/]+(?:\/.*)?$/, async route => {
    const url = new URL(route.request().url());
    const action = url.pathname.split(`/stories/episodes/${episodeId}`)[1] ?? "";
    if (route.request().method() === "GET") { await route.fulfill({ json: state }); return; }
    posts.push(action);
    const body = route.request().postDataJSON() as Record<string, unknown>;
    if (action === "/read") state = { ...state, read_at: "2026-10-02T08:00:00Z" };
    if (action === "/answers") {
      const chosen = body.answers as Record<string, number>;
      state = { ...state, read_at: "2026-10-02T08:00:00Z", answered: true, questions: [
        { ...questions[0], answer_index: 1, evidence: "Hij werkt in de fietsenwinkel.", chosen: chosen["0"], correct: chosen["0"] === 1 },
        { ...questions[1], answer_index: 2, evidence: "Baas, de oude hond, ligt bij de deur.", chosen: chosen["1"], correct: chosen["1"] === 2 },
      ] };
    }
    if (action === "/choice") state = { ...state, chosen_choice: String(body.choice) };
    if (action === "/rating") state = { ...state, rating: Number(body.rating) };
    if (action === "/words") { await route.fulfill({ json: { item: { id: "w1", term: String(body.term) }, created: true } }); return; }
    if (action === "/translate") { await route.fulfill({ json: { paragraph_index: body.paragraph_index, fa: "ترجمهٔ این بند.", cached: false } }); return; }
    await route.fulfill({ json: state });
  });
  return { posts, current: () => state };
}

test("today shows the streak, the goal and the episode that is ready", async ({ page }) => {
  await storyFixture(page);
  await page.goto("/");
  const home = page.getByTestId("today-home");
  await expect(home.getByRole("heading", { level: 1 })).toContainText("Er ligt een nieuwe aflevering klaar.");
  await expect(home.getByRole("img", { name: "4 dagen op rij" })).toBeVisible();
  await expect(home.getByText("Nog 20 punten tot je dagdoel.")).toBeVisible();
  await expect(home.getByRole("link", { name: /3 woorden om te herhalen/ })).toHaveAttribute("href", "/woorden");
  await expect(home.getByTestId("episode-card")).toContainText("De sleutel van Sami");
  await expect(home.getByRole("link", { name: "Mijn leerpad Twaalf niveaus met woorden, grammatica en toetsen." })).toHaveAttribute("href", "/leerpad");
  await expect(home.getByText("Wie is wie in De Lindestraat")).toBeVisible();
  const scan = await new AxeBuilder({ page }).include("#main").analyze();
  expect(scan.violations.filter(v => ["critical", "serious"].includes(v.impact ?? ""))).toEqual([]);
});

test("today reports a writer at work and a failed episode honestly", async ({ page }) => {
  await page.route(/\/api\/today(?:\?|$)/, route => route.fulfill({ json: plan({ next_step: "wait", episode: episode({ status: "generating", title: "" }) }) }));
  await page.goto("/");
  await expect(page.getByRole("heading", { level: 1 })).toContainText("Je volgende aflevering wordt geschreven.");
  await expect(page.getByText("De schrijver is bezig…")).toBeVisible();
  await page.unroute(/\/api\/today(?:\?|$)/);
  await page.route(/\/api\/today(?:\?|$)/, route => route.fulfill({ json: plan({ next_step: "review", episode: null, failed: episode({ status: "failed", error_code: "quality", title: "", failure_reasons: ["sentence_too_long: 19 words (limit 12)"] }) }) }));
  await page.goto("/");
  await expect(page.getByText("Deze aflevering haalde de controle niet.")).toBeVisible();
  await page.getByText("Wat er niet klopte").click();
  await expect(page.getByText("sentence_too_long: 19 words (limit 12)")).toBeVisible();
  await expect(page.getByRole("button", { name: "Opnieuw laten schrijven" })).toBeVisible();
});

test("reading an episode: finish, answer, save a word, choose how it continues", async ({ page }) => {
  const fixture = await storyFixture(page);
  await page.goto(`/verhalen/${episodeId}`);
  const reader = page.getByTestId("episode-reader");
  await expect(reader.getByRole("heading", { level: 1 })).toHaveText("De sleutel van Sami");
  await expect(reader.getByTestId("episode-paragraph")).toHaveCount(3);
  await expect(reader.getByText("It is Monday. Sami goes to work.")).toBeVisible();
  await expect(reader.getByRole("heading", { name: "Twee vragen over het verhaal" })).toHaveCount(0);
  await reader.getByRole("button", { name: "Bewaar", exact: true }).first().click();
  await expect(reader.getByText('"de toonbank" staat in je woordenlijst en komt terug op het juiste moment.')).toBeVisible();
  await reader.getByTestId("finish-reading").click();
  await expect(reader.getByRole("heading", { name: "Twee vragen over het verhaal" })).toBeVisible();
  const check = reader.getByRole("button", { name: "Controleer mijn antwoorden" });
  await expect(check).toBeDisabled();
  await reader.getByRole("radiogroup", { name: "Waar werkt Sami?" }).getByLabel("In de fietsenwinkel.").check();
  await reader.getByRole("radiogroup", { name: "Wie ligt bij de deur?" }).getByLabel("Tom.").check();
  await check.click();
  await expect(reader.getByRole("heading", { name: "1 van 2 juist" })).toBeVisible();
  await expect(reader.getByText("In het verhaal: “Baas, de oude hond, ligt bij de deur.”")).toBeVisible();
  await expect(reader.getByRole("heading", { name: "Hoe gaat het verder?" })).toBeVisible();
  await reader.getByRole("button", { name: /Sami gaat naar mevrouw De Clercq\./ }).click();
  await expect(reader.getByRole("heading", { name: "De volgende aflevering wordt geschreven." })).toBeVisible();
  await expect(reader.getByRole("button", { name: /Sami vraagt Tom om hulp\./ })).toBeDisabled();
  expect(fixture.posts).toEqual(["/words", "/read", "/answers", "/choice"]);
  const yes = reader.getByRole("button", { name: "Ja", exact: true });
  await yes.click();
  await expect(yes).toHaveAttribute("aria-pressed", "true");
  expect(fixture.current().rating).toBe(1);
});

test("persian support translates a paragraph on request and keeps it", async ({ page }) => {
  await storyFixture(page);
  await page.goto(`/verhalen/${episodeId}`);
  await page.getByLabel("Taalhulp / language").selectOption("nl-fa");
  const first = page.getByTestId("episode-paragraph").first();
  await first.getByRole("button", { name: "Vertaal naar het Perzisch" }).click();
  await expect(first.locator("[lang=fa]")).toHaveText("ترجمهٔ این بند.");
  await expect(first.getByRole("button", { name: "Vertaal naar het Perzisch" })).toHaveCount(0);
});

test("word review reveals, grades and brings a lapsed card back in the same round", async ({ page }) => {
  const items = [
    { id: "w1", term: "de toonbank", meaning_en: "the counter", meaning_fa: "پیشخوان", example: "Ayşe staat achter de toonbank.", source_kind: "story", source_id: "", ease: 2.5, interval_days: 0, repetitions: 0, lapses: 0, due_at: "2026-10-02T00:00:00Z", due: true, learned: false, last_grade: null, created_at: "2026-10-01T00:00:00Z" },
    { id: "w2", term: "de mond", meaning_en: "the mouth", meaning_fa: "دهان", example: "", source_kind: "story", source_id: "", ease: 2.5, interval_days: 0, repetitions: 0, lapses: 0, due_at: "2026-10-02T00:00:00Z", due: true, learned: false, last_grade: null, created_at: "2026-10-01T00:00:00Z" },
  ];
  const reviews: string[] = [];
  await page.route(/\/api\/words(?:\?|$)/, route => route.fulfill({ json: { items, total: 2, due_count: 2, learned_count: 0, new_count: 2 } }));
  await page.route(/\/api\/words\/[^/]+\/review$/, async route => {
    const body = route.request().postDataJSON() as { grade: string };
    const id = route.request().url().split("/words/")[1].split("/")[0];
    reviews.push(`${id}:${body.grade}`);
    const item = items.find(entry => entry.id === id)!;
    await route.fulfill({ json: body.grade === "again" ? { ...item, lapses: 1, due: true } : { ...item, interval_days: 1, repetitions: 1, due: false, due_at: "2026-10-03T00:00:00Z" } });
  });
  await page.goto("/woorden");
  const review = page.getByTestId("word-review");
  await expect(review.getByRole("heading", { level: 1 })).toHaveText("Herhaal wat je bewaarde.");
  await expect(review.getByText("2 KAARTEN IN DEZE RONDE")).toBeVisible();
  await expect(review.getByText("the counter")).toHaveCount(0);
  await review.getByTestId("reveal-word").click();
  await expect(review.getByText("the counter")).toBeVisible();
  await review.getByRole("button", { name: /Nog eens/ }).click();
  await expect(review.getByText("2 KAARTEN IN DEZE RONDE")).toBeVisible();
  await expect(review.locator(".flashcard-term")).toContainText("de mond");
  await review.getByTestId("reveal-word").click();
  await review.getByRole("button", { name: /Goed/ }).click();
  await expect(review.locator(".flashcard-term")).toContainText("de toonbank");
  await review.getByTestId("reveal-word").click();
  await review.getByRole("button", { name: /Makkelijk/ }).click();
  await expect(review.getByRole("heading", { level: 1 })).toHaveText("Klaar voor vandaag.");
  expect(reviews).toEqual(["w1:again", "w2:good", "w1:easy"]);
});

test("the real API queues the first episode for a new learner", async ({ page }) => {
  await page.goto("/");
  const home = page.getByTestId("today-home");
  await expect(home.getByRole("heading", { level: 1 })).toContainText(/wordt geschreven|nieuwe aflevering klaar/);
  await expect(home.getByText("Wie is wie in De Lindestraat")).toBeVisible();
  await page.goto("/verhalen");
  await expect(page.getByTestId("story-library").getByRole("heading", { level: 1 })).toHaveText("De Lindestraat");
  await expect(page.locator(".episode-tile")).toHaveCount(1);
});
