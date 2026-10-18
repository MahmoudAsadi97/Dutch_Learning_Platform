import AxeBuilder from "@axe-core/playwright";
import { expect, test } from "./fixtures/test";

/** Browser checks for the serial, the word bank and the daily plan. Route fixtures drive the states a
 * learner meets; the API suite proves the engine itself. One unmocked check proves the real path. */
import { episode, episodeId, plan, storyFixture } from "./fixtures/stories";

test("the dashboard offers one learning route instead of competing story and word entrances", async ({
  page,
}) => {
  await storyFixture(page);
  await page.goto("/");
  const home = page.getByTestId("study-dashboard");
  await expect(home.getByRole("heading", { level: 1 })).toContainText("Wat wil je vandaag kunnen zeggen?");
  await expect(home.getByRole("link", { name: /^Verder met A1/ })).toHaveAttribute(
    "href",
    "/learn/a1?skill=reading",
  );
  await expect(home.getByRole("link", { name: /^Kies een ander niveau/ })).toHaveAttribute(
    "href",
    "/leerpad",
  );
  await expect(home.locator(".study-skill-card")).toHaveCount(4);
  await expect(home.getByText("Wie is wie in De Lindestraat")).toHaveCount(0);
  await expect(home.getByTestId("episode-card")).toHaveCount(0);
  const scan = await new AxeBuilder({ page }).include("#main").analyze();
  expect(scan.violations.filter((v) => ["critical", "serious"].includes(v.impact ?? ""))).toEqual([]);
});

test("background story generation does not block the dashboard's learning route", async ({ page }) => {
  const requests: string[] = [];
  page.on("request", (request) => {
    if (/\/api\/today(?:\/prepare)?(?:\?|$)/.test(request.url())) requests.push(request.url());
  });
  await page.route(/\/api\/today(?:\/prepare)?(?:\?|$)/, (route) =>
    route.fulfill({
      json: plan({ next_step: "wait", episode: episode({ status: "generating", title: "" }) }),
    }),
  );
  await page.goto("/");
  await expect(page.getByTestId("study-dashboard")).toBeVisible();
  await expect(page.getByRole("link", { name: /^Verder met A1/ })).toBeVisible();
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
  await expect(page.getByTestId("study-dashboard")).toBeVisible();
  await expect(page.getByRole("link", { name: /^Kies een ander niveau/ })).toBeVisible();
  await expect(page.getByText("sentence_too_long: 19 words (limit 12)")).toHaveCount(0);
  expect(requests).toEqual([]);
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

test("episode English help can be hidden and restored without requesting Persian translation", async ({
  page,
}) => {
  await storyFixture(page);
  await page.goto(`/verhalen/${episodeId}`);
  const first = page.getByTestId("episode-paragraph").first();
  await expect(first.locator("[lang=en]")).toHaveText("It is Monday. Sami goes to work.");
  await page.getByLabel("Taalhulp / language").selectOption("nl");
  await expect(first.locator("[lang=en]")).toHaveCount(0);
  await expect(first.locator("[lang=nl]").first()).toContainText("Het is maandag.");
  await page.getByLabel("Taalhulp / language").selectOption("nl-en");
  await expect(first.locator("[lang=en]")).toHaveText("It is Monday. Sami goes to work.");
  await expect(first.locator("[lang=fa]")).toHaveCount(0);
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
  await expect(page.locator('[lang="fa"]')).toHaveCount(0);
  await page.getByLabel("Taalhulp / language").selectOption("nl");
  await expect(review.getByText("the counter")).toHaveCount(0);
  await expect(review.locator(".flashcard-term")).toContainText("de toonbank");
  await page.getByLabel("Taalhulp / language").selectOption("nl-en");
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

test("the first queued episode remains available in the personal reading collection", async ({ page }) => {
  const response = await page.request.get("/api/stories");
  expect(response.ok()).toBe(true);
  const collection = await response.json();
  expect(collection.series).toBeTruthy();
  await page.goto("/verhalen?view=personal");
  await expect(page.getByTestId("story-library").locator(".path-heading h2")).toHaveText("De Lindestraat");
  await expect(page.locator(".episode-tile")).toHaveCount(1);
});
