import AxeBuilder from "@axe-core/playwright";
import { expect, test } from "./fixtures/test";

/** Browser checks for the serial, the word bank and the daily plan. Route fixtures drive the states a
 * learner meets; the API suite proves the engine itself. One unmocked check proves the real path. */
import { episode, episodeId, plan, storyFixture } from "./fixtures/stories";

test("today shows the streak, the goal and the episode that is ready", async ({ page }) => {
  await storyFixture(page);
  await page.goto("/");
  const home = page.getByTestId("today-home");
  await expect(home.getByRole("heading", { level: 1 })).toContainText("Er ligt een nieuwe aflevering klaar.");
  await expect(home.getByRole("img", { name: "4 dagen op rij" })).toBeVisible();
  await expect(home.getByText("Nog 20 punten tot je dagdoel.")).toBeVisible();
  await expect(home.getByRole("link", { name: /3 woorden om te herhalen/ })).toHaveAttribute(
    "href",
    "/woorden?view=personal",
  );
  await expect(home.getByTestId("episode-card")).toContainText("De sleutel van Sami");
  await expect(
    home.getByRole("link", { name: "Mijn leerpad Twaalf niveaus met woorden, grammatica en toetsen." }),
  ).toHaveAttribute("href", "/leerpad");
  await expect(home.getByText("Wie is wie in De Lindestraat")).toBeVisible();
  const scan = await new AxeBuilder({ page }).include("#main").analyze();
  expect(scan.violations.filter((v) => ["critical", "serious"].includes(v.impact ?? ""))).toEqual([]);
});

test("today reports a writer at work and a failed episode honestly", async ({ page }) => {
  await page.route(/\/api\/today(?:\/prepare)?(?:\?|$)/, (route) =>
    route.fulfill({
      json: plan({ next_step: "wait", episode: episode({ status: "generating", title: "" }) }),
    }),
  );
  await page.goto("/");
  await expect(page.getByRole("heading", { level: 1 })).toContainText(
    "Je volgende aflevering wordt geschreven.",
  );
  await expect(page.getByText("De schrijver is bezig…")).toBeVisible();
  await page.unroute(/\/api\/today(?:\/prepare)?(?:\?|$)/);
  await page.route(/\/api\/today(?:\/prepare)?(?:\?|$)/, (route) =>
    route.fulfill({
      json: plan({
        next_step: "review",
        episode: null,
        failed: episode({
          status: "failed",
          error_code: "quality",
          title: "",
          failure_reasons: ["sentence_too_long: 19 words (limit 12)"],
        }),
      }),
    }),
  );
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
  await expect(
    reader.getByText('"de toonbank" staat in je woordenlijst en komt terug op het juiste moment.'),
  ).toBeVisible();
  await reader.getByTestId("finish-reading").click();
  await expect(reader.getByRole("heading", { name: "Twee vragen over het verhaal" })).toBeVisible();
  const check = reader.getByRole("button", { name: "Controleer mijn antwoorden" });
  await expect(check).toBeDisabled();
  const workplace = reader.getByRole("radiogroup", { name: "Waar werkt Sami?", exact: true });
  const chosenWorkplace = workplace.getByRole("radio", { name: "In de fietsenwinkel.", exact: true });
  await chosenWorkplace.check();
  await expect(chosenWorkplace).toBeChecked();
  await expect(
    workplace.getByRole("button", {
      name: "Luister: In de fietsenwinkel. · synthetische stem",
      exact: true,
    }),
  ).toBeVisible();
  const chosenPerson = reader
    .getByRole("radiogroup", { name: "Wie ligt bij de deur?", exact: true })
    .getByRole("radio", { name: "Tom.", exact: true });
  await chosenPerson.check();
  await expect(chosenPerson).toBeChecked();
  await expect(reader.locator(".answer-options label button")).toHaveCount(0);
  await check.click();
  await expect(reader.getByRole("heading", { name: "1 van 2 juist" })).toBeVisible();
  await expect(reader.getByText("In het verhaal: “Baas, de oude hond, ligt bij de deur.”")).toBeVisible();
  await expect(reader.getByRole("heading", { name: "Hoe gaat het verder?" })).toBeVisible();
  await reader.getByRole("button", { name: "Sami gaat naar mevrouw De Clercq.", exact: true }).click();
  await expect(
    reader.getByRole("heading", { name: "De volgende aflevering wordt geschreven." }),
  ).toBeVisible();
  await expect(reader.getByRole("button", { name: "Sami vraagt Tom om hulp.", exact: true })).toBeDisabled();
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
    {
      id: "w1",
      term: "de toonbank",
      meaning_en: "the counter",
      meaning_fa: "پیشخوان",
      example: "Ayşe staat achter de toonbank.",
      source_kind: "story",
      source_id: "",
      ease: 2.5,
      interval_days: 0,
      repetitions: 0,
      lapses: 0,
      due_at: "2026-10-02T00:00:00Z",
      due: true,
      learned: false,
      last_grade: null,
      created_at: "2026-10-01T00:00:00Z",
    },
    {
      id: "w2",
      term: "de mond",
      meaning_en: "the mouth",
      meaning_fa: "دهان",
      example: "",
      source_kind: "story",
      source_id: "",
      ease: 2.5,
      interval_days: 0,
      repetitions: 0,
      lapses: 0,
      due_at: "2026-10-02T00:00:00Z",
      due: true,
      learned: false,
      last_grade: null,
      created_at: "2026-10-01T00:00:00Z",
    },
  ];
  const reviews: string[] = [];
  await page.route(/\/api\/words(?:\?|$)/, (route) =>
    route.fulfill({ json: { items, total: 2, due_count: 2, learned_count: 0, new_count: 2 } }),
  );
  await page.route(/\/api\/words\/[^/]+\/review$/, async (route) => {
    const body = route.request().postDataJSON() as { grade: string };
    const id = route.request().url().split("/words/")[1].split("/")[0];
    reviews.push(`${id}:${body.grade}`);
    const item = items.find((entry) => entry.id === id)!;
    await route.fulfill({
      json:
        body.grade === "again"
          ? { ...item, lapses: 1, due: true }
          : { ...item, interval_days: 1, repetitions: 1, due: false, due_at: "2026-10-03T00:00:00Z" },
    });
  });
  await page.goto("/woorden?view=personal");
  const review = page.getByTestId("word-review");
  await expect(review.locator(".path-heading h2")).toHaveText("Herhaal wat je bewaarde.");
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
  await expect(review.locator(".path-heading h2")).toHaveText("Klaar voor vandaag.");
  expect(reviews).toEqual(["w1:again", "w2:good", "w1:easy"]);
});

test("the real API queues the first episode for a new learner", async ({ page }) => {
  await page.goto("/");
  const home = page.getByTestId("today-home");
  await expect(home.getByRole("heading", { level: 1 })).toContainText(
    /wordt geschreven|nieuwe aflevering klaar/,
  );
  await expect(home.getByText("Wie is wie in De Lindestraat")).toBeVisible();
  await page.goto("/verhalen?view=personal");
  await expect(page.getByTestId("story-library").locator(".path-heading h2")).toHaveText("De Lindestraat");
  await expect(page.locator(".episode-tile")).toHaveCount(1);
});
